import { useQuery } from '@tanstack/react-query'

import { listRules } from '../api/repository'
import type { RuleActiveFilter } from '../types/rule'
import { ruleKeys } from './ruleKeys'

export function useRules(filter: RuleActiveFilter) {
  return useQuery({
    queryKey: ruleKeys.list(filter),
    queryFn: ({ signal }) => listRules(filter, signal),
  })
}
