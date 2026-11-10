import { expect, test } from '@playwright/test'

import {
  CREATED_STATUS,
  NOT_FOUND_STATUS,
  NO_CONTENT_STATUS,
  apiPath,
  makeMockRule,
  mockApi,
} from './apiMocks'
import type { MockRule } from './apiMocks'

const RULE_PATH_PATTERN = /^\/api\/rules\/(\d+)$/

test('creates, toggles, edits and deletes a rule', async ({ page }) => {
  let rules: MockRule[] = []
  let nextId = 1
  await mockApi(page, async (route) => {
    const request = route.request()
    const path = apiPath(route)
    const method = request.method()
    const idMatch = RULE_PATH_PATTERN.exec(path)
    const id = Number(idMatch?.[1])

    if (method === 'GET' && path === '/api/rules') {
      await route.fulfill({ json: rules })
    } else if (method === 'POST' && path === '/api/rules') {
      const created = makeMockRule(nextId++, request.postDataJSON() as Partial<MockRule>)
      rules = [...rules, created]
      await route.fulfill({ status: CREATED_STATUS, json: created })
    } else if (method === 'PATCH' && idMatch) {
      const patch = request.postDataJSON() as Partial<MockRule>
      rules = rules.map((rule) => (rule.id === id ? { ...rule, ...patch } : rule))
      await route.fulfill({ json: rules.find((rule) => rule.id === id) })
    } else if (method === 'DELETE' && idMatch) {
      rules = rules.filter((rule) => rule.id !== id)
      await route.fulfill({ status: NO_CONTENT_STATUS })
    } else {
      await route.fulfill({ status: NOT_FOUND_STATUS, json: { detail: 'unmocked' } })
    }
  })

  await page.goto('/rules')
  await expect(page.getByText(/No rules yet/)).toBeVisible()

  await page.getByRole('button', { name: 'Add rule' }).click()
  const addDialog = page.getByRole('dialog', { name: 'Add rule' })
  await addDialog.getByRole('button', { name: 'Add rule' }).click()
  await expect(addDialog.getByText('Title is required')).toBeVisible()
  await addDialog.getByLabel('Title').fill('No personal names')
  await addDialog.getByLabel('Rule text').fill('The document must not name people.')
  await addDialog.getByRole('button', { name: 'Add rule' }).click()
  await expect(page.getByRole('heading', { name: 'No personal names' })).toBeVisible()

  const toggle = page.getByRole('switch', { name: 'Active: No personal names' })
  await expect(toggle).toBeChecked()
  await toggle.click()
  await expect(toggle).not.toBeChecked()

  await page.getByRole('button', { name: 'Edit No personal names' }).click()
  const editDialog = page.getByRole('dialog', { name: 'Edit rule' })
  await editDialog.getByLabel('Title').fill('No names')
  await editDialog.getByRole('button', { name: 'Save changes' }).click()
  await expect(page.getByRole('heading', { name: 'No names' })).toBeVisible()

  await page.getByRole('button', { name: 'Delete No names' }).click()
  const confirmDialog = page.getByRole('dialog', { name: 'Delete rule' })
  await confirmDialog.getByRole('button', { name: 'Delete rule' }).click()
  await expect(page.getByText(/No rules yet/)).toBeVisible()
})
