import { z } from 'zod'

import { ERROR_MESSAGES } from './apiConstants'

const LOCATION_SEPARATOR = '.'
const MESSAGE_SEPARATOR = '; '
const IGNORED_LOCATION_ROOTS = new Set(['body', 'query', 'path'])

const detailItemSchema = z.object({
  loc: z.array(z.union([z.string(), z.number()])).optional(),
  msg: z.string(),
})

const errorBodySchema = z.object({
  detail: z.union([z.string(), z.array(detailItemSchema)]),
})

type DetailItem = z.infer<typeof detailItemSchema>

function describeDetailItem(item: DetailItem): string {
  const location = (item.loc ?? [])
    .filter((part, index) => !(index === 0 && IGNORED_LOCATION_ROOTS.has(String(part))))
    .join(LOCATION_SEPARATOR)
  return location ? `${location}: ${item.msg}` : item.msg
}

export function parseErrorMessage(body: unknown, status: number): string {
  const fallback = `${ERROR_MESSAGES.requestFailed} (HTTP ${status}).`
  const parsed = errorBodySchema.safeParse(body)
  if (!parsed.success) {
    return fallback
  }
  const { detail } = parsed.data
  if (typeof detail === 'string') {
    return detail
  }
  if (detail.length === 0) {
    return fallback
  }
  return detail.map(describeDetailItem).join(MESSAGE_SEPARATOR)
}
