import type { RuleActiveFilter } from '../types/rule'

export const ruleKeys = {
  all: ['rules'] as const,
  list: (filter: RuleActiveFilter) => [...ruleKeys.all, 'list', filter] as const,
}
