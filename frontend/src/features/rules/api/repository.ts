import { HttpMethod } from '@/lib/api/apiConstants'
import { requestJson, requestVoid } from '@/lib/api/httpClient'

import { ruleListSchema, ruleSchema } from '../schemas/rule.schema'
import type { CreateRulePayload, Rule, UpdateRulePayload } from '../types/rule'
import { RuleActiveFilter } from '../types/rule'

export const RULES_PATH = '/rules'
export const ACTIVE_QUERY_PARAM = 'active'

export function listRules(filter: RuleActiveFilter, signal?: AbortSignal): Promise<Rule[]> {
  const query = filter === RuleActiveFilter.Active ? `?${ACTIVE_QUERY_PARAM}=true` : ''
  return requestJson(`${RULES_PATH}${query}`, ruleListSchema, { signal })
}

export function createRule(payload: CreateRulePayload): Promise<Rule> {
  return requestJson(RULES_PATH, ruleSchema, {
    method: HttpMethod.Post,
    body: { json: payload },
  })
}

export function updateRule(id: number, payload: UpdateRulePayload): Promise<Rule> {
  return requestJson(`${RULES_PATH}/${id}`, ruleSchema, {
    method: HttpMethod.Patch,
    body: { json: payload },
  })
}

export function deleteRule(id: number): Promise<void> {
  return requestVoid(`${RULES_PATH}/${id}`, { method: HttpMethod.Delete })
}
