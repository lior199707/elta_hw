import { useQuery } from '@tanstack/react-query'

import { getCheck, listChecks } from '../api/repository'
import type { ListChecksParams } from '../api/repository'
import { checkKeys } from './checkKeys'

export function useChecks(params: ListChecksParams = {}) {
  return useQuery({
    queryKey: checkKeys.list(params),
    queryFn: ({ signal }) => listChecks(params, signal),
  })
}

export function useCheck(id: number) {
  return useQuery({
    queryKey: checkKeys.detail(id),
    queryFn: ({ signal }) => getCheck(id, signal),
  })
}
