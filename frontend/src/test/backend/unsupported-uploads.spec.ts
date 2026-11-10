/// <reference types="node" />
import { expect, test } from '@playwright/test'
import type { APIRequestContext } from '@playwright/test'

const CHECKS_API = '/api/checks'
const PDF_BYTES = Buffer.from('%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n')

async function historyCount(request: APIRequestContext) {
  return ((await (await request.get(CHECKS_API)).json()) as unknown[]).length
}

test('an unsupported file type is rejected in the browser before anything is sent', async ({
  page,
}) => {
  let checkRequests = 0
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().includes(CHECKS_API)) checkRequests += 1
  })

  await page.goto('/')
  await page.locator('input[type="file"]').setInputFiles({
    name: 'report.pdf',
    mimeType: 'application/pdf',
    buffer: PDF_BYTES,
  })

  await expect(page.getByText('Unsupported file type. Upload a .docx or .txt file.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Run check' })).toBeDisabled()
  expect(checkRequests).toBe(0)
})

test('a PDF renamed to .docx is rejected by the backend with a readable message', async ({
  page,
  request,
}) => {
  const before = await historyCount(request)

  await page.goto('/')
  await page.locator('input[type="file"]').setInputFiles({
    name: 'disguised.docx',
    mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    buffer: PDF_BYTES,
  })
  const response = page.waitForResponse(
    (candidate) => candidate.url().includes(CHECKS_API) && candidate.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Run check' }).click()

  expect((await response).status()).toBe(422)
  await expect(page.getByText(/not a readable DOCX document/).first()).toBeVisible()
  await expect(page.getByRole('button', { name: 'Run check' })).toBeEnabled()
  await expect(page).toHaveURL(/\/$/)
  expect(await historyCount(request)).toBe(before)
})
