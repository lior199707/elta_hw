import type { z } from 'zod'

import type { ruleFormSchema, ruleSchema } from '../schemas/rule.schema'

export type Rule = z.infer<typeof ruleSchema>

export type RuleFormValues = z.input<typeof ruleFormSchema>
export type RuleFormData = z.output<typeof ruleFormSchema>

export type CreateRulePayload = RuleFormData
export type UpdateRulePayload = Partial<RuleFormData>

export const RuleActiveFilter = { All: 'all', Active: 'active' } as const
export type RuleActiveFilter = (typeof RuleActiveFilter)[keyof typeof RuleActiveFilter]
