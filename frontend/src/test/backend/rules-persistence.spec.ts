/// <reference types="node" />
import { expect, test } from '@playwright/test'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const RULES_API = '/api/rules'
const HEALTH_API = '/api/health'
const REPO_ROOT = fileURLToPath(new URL('../../../..', import.meta.url))
const RESTART_COMMAND = 'docker compose restart backend'
const RESTART_TIMEOUT_MS = 90_000
const HEALTH_POLL_MS = 1_000

test('a rule added in the browser survives a backend container restart', async ({
  page,
  request,
}) => {
  test.setTimeout(RESTART_TIMEOUT_MS * 2)
  const title = `E2E persistence rule ${Date.now()}`

  try {
    await page.goto('/rules')
    await page.getByRole('button', { name: 'Add rule' }).click()
    const addDialog = page.getByRole('dialog', { name: 'Add rule' })
    await addDialog.getByLabel('Title').fill(title)
    await addDialog.getByLabel('Rule text').fill('Created to verify that rules persist.')
    await addDialog.getByRole('button', { name: 'Add rule' }).click()
    await expect(page.getByRole('heading', { name: title })).toBeVisible()

    execSync(RESTART_COMMAND, { cwd: REPO_ROOT, stdio: 'ignore' })
    await expect
      .poll(
        async () => {
          try {
            return (await request.get(HEALTH_API)).status()
          } catch {
            return 0
          }
        },
        { timeout: RESTART_TIMEOUT_MS, intervals: [HEALTH_POLL_MS] },
      )
      .toBe(200)

    await page.reload()
    await expect(page.getByRole('heading', { name: title })).toBeVisible()
    await expect(page.getByRole('switch', { name: `Active: ${title}` })).toBeChecked()
  } finally {
    const rules: { id: number; title: string }[] = await (await request.get(RULES_API)).json()
    for (const rule of rules.filter((candidate) => candidate.title === title)) {
      await request.delete(`${RULES_API}/${rule.id}`)
    }
  }
})
