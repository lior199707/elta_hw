/// <reference types="node" />

import { expect, test } from '@playwright/test'

import { makeCheckRun } from '../features/checks/utils/checkRunFixtures'
import { CREATED_STATUS, NOT_FOUND_STATUS, apiPath, makeMockRule, mockApi } from './apiMocks'

const run = makeCheckRun()

test.describe('check workflow', () => {
  test('runs a check end to end and shows the highlighted quote', async ({ page }) => {
    const requestedPaths: string[] = []
    await mockApi(page, async (route) => {
      const path = apiPath(route)
      const method = route.request().method()
      requestedPaths.push(`${method} ${path}`)
      if (method === 'GET' && path === '/api/rules?active=true') {
        await route.fulfill({
          json: [makeMockRule(1, { title: 'No performance figures' }), makeMockRule(2)],
        })
      } else if (method === 'POST' && path === '/api/checks') {
        await route.fulfill({ status: CREATED_STATUS, json: run })
      } else if (method === 'GET' && path === `/api/checks/${run.id}`) {
        await route.fulfill({ json: run })
      } else {
        await route.fulfill({ status: NOT_FOUND_STATUS, json: { detail: 'unmocked' } })
      }
    })

    await page.goto('/')
    const runButton = page.getByRole('button', { name: 'Run check' })
    await expect(page.getByRole('checkbox', { name: /No performance figures/ })).toBeChecked()
    await expect(runButton).toBeDisabled()

    await page
      .getByLabel('Document')
      .setInputFiles({ name: 'spec.docx', mimeType: 'text/plain', buffer: Buffer.from('hello') })
    await expect(runButton).toBeEnabled()
    await runButton.click()

    await expect(page).toHaveURL(new RegExp(`/history/${run.id}$`))
    await expect(page.getByRole('heading', { level: 1, name: 'spec.docx' })).toBeVisible()
    const mark = page.getByText('120 km/h').first()
    await expect(mark).toBeVisible()
    await expect(mark).toHaveJSProperty('tagName', 'MARK')
    await expect(page.getByRole('region', { name: 'No profanity' })).toContainText('Passed')

    await page.getByText('Position in document').click()
    await expect(
      page.getByRole('list', { name: 'Violations by position in document' }),
    ).toBeVisible()
  })

  test('shows the warning banner for a partial result', async ({ page }) => {
    const partialRun = makeCheckRun({
      status: 'partial',
      failed_chunks: [
        {
          chunk_id: 'C2',
          first_block_id: 'B12',
          last_block_id: 'B18',
          reason: 'quota_exceeded',
          message: 'quota',
        },
      ],
    })
    await mockApi(page, async (route) => {
      await route.fulfill({ json: partialRun })
    })

    await page.goto(`/history/${partialRun.id}`)

    const banner = page.getByRole('alert')
    await expect(banner).toContainText('Part of the document was NOT checked')
    await expect(banner).toContainText('Paragraphs 12 to 18')
    await expect(page.getByText('Passed', { exact: true })).toHaveCount(0)
  })

  test('shows the API error when the check is rejected', async ({ page }) => {
    await mockApi(page, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({ status: 415, json: { detail: 'Unsupported document type' } })
      } else {
        await route.fulfill({ json: [makeMockRule(1)] })
      }
    })

    await page.goto('/')
    await page
      .getByLabel('Document')
      .setInputFiles({ name: 'a.txt', mimeType: 'text/plain', buffer: Buffer.from('hello') })
    await page.getByRole('button', { name: 'Run check' }).click()

    await expect(page.getByText('Unsupported document type').first()).toBeVisible()
    await expect(page).toHaveURL(/\/$/)
  })

  test('filters violations by rule and clears the filters', async ({ page }) => {
    await mockApi(page, async (route) => {
      await route.fulfill({ json: run })
    })

    await page.goto(`/history/${run.id}`)
    await expect(page.getByText('Showing 3 of 3 violations')).toBeVisible()
    await expect(page.locator('mark', { hasText: '120 km/h' })).toBeVisible()

    await page.getByRole('checkbox', { name: /No performance figures/ }).click()

    await expect(page.getByText('Showing 2 of 3 violations')).toBeVisible()
    await expect(page.locator('mark', { hasText: '120 km/h' })).toHaveCount(0)
    await expect(page).toHaveURL(/rules=/)

    await page.getByRole('button', { name: 'Clear filters' }).click()

    await expect(page.getByText('Showing 3 of 3 violations')).toBeVisible()
    await expect(page.locator('mark', { hasText: '120 km/h' })).toBeVisible()
    await expect(page).not.toHaveURL(/rules=/)
  })
})
