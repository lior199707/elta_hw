import { expect, test } from '@playwright/test'

const RULES_API = '/api/rules'

test('add, deactivate, reactivate and delete a rule against the real backend', async ({
  page,
  request,
}) => {
  const title = `E2E lifecycle rule ${Date.now()}`
  const ruleCheckbox = page.getByRole('checkbox', { name: new RegExp(title) })

  await page.goto('/rules')
  await page.getByRole('button', { name: 'Add rule' }).click()
  const addDialog = page.getByRole('dialog', { name: 'Add rule' })
  await addDialog.getByLabel('Title').fill(title)
  await addDialog.getByLabel('Rule text').fill('The document must not mention test data.')
  await addDialog.getByRole('button', { name: 'Add rule' }).click()
  await expect(page.getByRole('heading', { name: title })).toBeVisible()

  try {
    await page.getByRole('link', { name: 'Check' }).click()
    await expect(ruleCheckbox).toBeVisible()

    await page.getByRole('link', { name: 'Rules' }).click()
    const toggle = page.getByRole('switch', { name: `Active: ${title}` })
    await toggle.click()
    await expect(toggle).not.toBeChecked()
    await page.getByRole('link', { name: 'Check' }).click()
    await expect(page.getByRole('checkbox').first()).toBeVisible()
    await expect(ruleCheckbox).toHaveCount(0)

    await page.getByRole('link', { name: 'Rules' }).click()
    await page.getByRole('switch', { name: `Active: ${title}` }).click()
    await expect(page.getByRole('switch', { name: `Active: ${title}` })).toBeChecked()
    await page.getByRole('link', { name: 'Check' }).click()
    await expect(ruleCheckbox).toBeVisible()

    await page.getByRole('link', { name: 'Rules' }).click()
    await page.getByRole('button', { name: `Delete ${title}` }).click()
    const confirmDialog = page.getByRole('dialog', { name: 'Delete rule' })
    await confirmDialog.getByRole('button', { name: 'Delete rule' }).click()
    await expect(page.getByRole('heading', { name: title })).toHaveCount(0)
    await page.getByRole('link', { name: 'Check' }).click()
    await expect(page.getByRole('checkbox').first()).toBeVisible()
    await expect(ruleCheckbox).toHaveCount(0)
  } finally {
    const rules: { id: number; title: string }[] = await (await request.get(RULES_API)).json()
    for (const rule of rules.filter((candidate) => candidate.title === title)) {
      await request.delete(`${RULES_API}/${rule.id}`)
    }
  }
})
