import { describe, expect, it } from 'vitest'

import {
  RULE_TEXT_MAX_LENGTH,
  RULE_TITLE_MAX_LENGTH,
  ruleFormSchema,
  ruleListSchema,
} from './rule.schema'

const validRule = {
  id: 1,
  title: 'No names',
  text: 'Do not mention people.',
  is_active: true,
  created_at: '2026-11-10T18:40:24Z',
  updated_at: '2026-11-10T18:40:24Z',
}

describe('ruleListSchema', () => {
  it('accepts a valid list, including an empty one', () => {
    expect(ruleListSchema.parse([validRule])).toHaveLength(1)
    expect(ruleListSchema.parse([])).toEqual([])
  })

  it('rejects a rule with a wrong field type', () => {
    expect(ruleListSchema.safeParse([{ ...validRule, is_active: 'yes' }]).success).toBe(false)
  })
})

describe('ruleFormSchema', () => {
  it('accepts valid values and trims whitespace', () => {
    const result = ruleFormSchema.parse({ title: '  Title  ', text: ' Body ', is_active: true })

    expect(result).toEqual({ title: 'Title', text: 'Body', is_active: true })
  })

  it('rejects empty and whitespace-only fields', () => {
    const result = ruleFormSchema.safeParse({ title: '   ', text: '', is_active: true })

    expect(result.success).toBe(false)
  })

  it('enforces the maximum lengths', () => {
    const tooLongTitle = ruleFormSchema.safeParse({
      title: 'a'.repeat(RULE_TITLE_MAX_LENGTH + 1),
      text: 'ok',
      is_active: true,
    })
    const tooLongText = ruleFormSchema.safeParse({
      title: 'ok',
      text: 'a'.repeat(RULE_TEXT_MAX_LENGTH + 1),
      is_active: true,
    })
    const atLimit = ruleFormSchema.safeParse({
      title: 'a'.repeat(RULE_TITLE_MAX_LENGTH),
      text: 'a'.repeat(RULE_TEXT_MAX_LENGTH),
      is_active: false,
    })

    expect(tooLongTitle.success).toBe(false)
    expect(tooLongText.success).toBe(false)
    expect(atLimit.success).toBe(true)
  })
})
