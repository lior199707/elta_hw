import { z } from 'zod'

export const RULE_TITLE_MAX_LENGTH = 200
export const RULE_TEXT_MAX_LENGTH = 2000

export const ruleSchema = z.object({
  id: z.number().int(),
  title: z.string(),
  text: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
})

export const ruleListSchema = z.array(ruleSchema)

export const ruleFormSchema = z.object({
  title: z
    .string()
    .trim()
    .min(1, 'Title is required')
    .max(RULE_TITLE_MAX_LENGTH, `Title must be at most ${RULE_TITLE_MAX_LENGTH} characters`),
  text: z
    .string()
    .trim()
    .min(1, 'Rule text is required')
    .max(RULE_TEXT_MAX_LENGTH, `Rule text must be at most ${RULE_TEXT_MAX_LENGTH} characters`),
  is_active: z.boolean(),
})
