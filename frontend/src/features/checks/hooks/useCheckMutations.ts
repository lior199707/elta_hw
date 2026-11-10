import { useMutation, useQueryClient } from '@tanstack/react-query'

import { deleteCheck, runCheck } from '../api/repository'
import { checkKeys } from './checkKeys'

export function useRunCheck() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: runCheck,
    onSuccess: async (run) => {
      queryClient.setQueryData(checkKeys.detail(run.id), run)
      await queryClient.invalidateQueries({ queryKey: checkKeys.lists() })
    },
  })
}

export function useDeleteCheck() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteCheck,
    onSuccess: async (_data, id) => {
      queryClient.removeQueries({ queryKey: checkKeys.detail(id) })
      await queryClient.invalidateQueries({ queryKey: checkKeys.lists() })
    },
  })
}
