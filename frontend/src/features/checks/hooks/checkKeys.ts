import type { ListChecksParams } from '../api/repository'

export const checkKeys = {
  all: ['checks'] as const,
  lists: () => [...checkKeys.all, 'list'] as const,
  list: (params: ListChecksParams) => [...checkKeys.lists(), params] as const,
  details: () => [...checkKeys.all, 'detail'] as const,
  detail: (id: number) => [...checkKeys.details(), id] as const,
}
