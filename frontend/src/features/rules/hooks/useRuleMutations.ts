import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createRule, deleteRule, updateRule } from '../api/repository'
import type { UpdateRulePayload } from '../types/rule'
import { ruleKeys } from './ruleKeys'

function useInvalidateRules() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ruleKeys.all })
}

export function useCreateRule() {
  const invalidateRules = useInvalidateRules()
  return useMutation({ mutationFn: createRule, onSuccess: invalidateRules })
}

interface UpdateRuleVariables {
  id: number
  payload: UpdateRulePayload
}

export function useUpdateRule() {
  const invalidateRules = useInvalidateRules()
  return useMutation({
    mutationFn: ({ id, payload }: UpdateRuleVariables) => updateRule(id, payload),
    onSuccess: invalidateRules,
  })
}

export function useDeleteRule() {
  const invalidateRules = useInvalidateRules()
  return useMutation({ mutationFn: deleteRule, onSuccess: invalidateRules })
}
