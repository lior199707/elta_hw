import { HttpMethod } from '@/lib/api/apiConstants'
import { requestJson, requestVoid } from '@/lib/api/httpClient'

import { checkRunSchema, checkRunSummaryListSchema } from '../schemas/checkRun.schema'
import type { CheckRun, CheckRunSummary, RunCheckPayload } from '../types/checkRun'

export const CHECKS_PATH = '/checks'
export const FILE_FIELD = 'file'
export const RULE_IDS_FIELD = 'rule_ids'
export const DEFAULT_PAGE_LIMIT = 50

export interface ListChecksParams {
  limit?: number
  offset?: number
}

export function buildCheckFormData({ file, ruleIds }: RunCheckPayload): FormData {
  const form = new FormData()
  form.append(FILE_FIELD, file)
  ruleIds.forEach((ruleId) => {
    form.append(RULE_IDS_FIELD, String(ruleId))
  })
  return form
}

export function runCheck(payload: RunCheckPayload): Promise<CheckRun> {
  return requestJson(CHECKS_PATH, checkRunSchema, {
    method: HttpMethod.Post,
    body: { form: buildCheckFormData(payload) },
  })
}

export function listChecks(
  { limit = DEFAULT_PAGE_LIMIT, offset = 0 }: ListChecksParams = {},
  signal?: AbortSignal,
): Promise<CheckRunSummary[]> {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  return requestJson(`${CHECKS_PATH}?${query.toString()}`, checkRunSummaryListSchema, { signal })
}

export function getCheck(id: number, signal?: AbortSignal): Promise<CheckRun> {
  return requestJson(`${CHECKS_PATH}/${id}`, checkRunSchema, { signal })
}

export function deleteCheck(id: number): Promise<void> {
  return requestVoid(`${CHECKS_PATH}/${id}`, { method: HttpMethod.Delete })
}
