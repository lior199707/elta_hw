import { ResultViewMode, Severity } from '../types/checkEnums'

export const VIEW_PARAMS = {
  sort: 'sort',
  rules: 'rules',
  severity: 'severity',
  query: 'q',
} as const

const LIST_SEPARATOR = ','
const ALL_SEVERITIES: readonly Severity[] = Object.values(Severity)
const ALL_SORTS: readonly ResultViewMode[] = Object.values(ResultViewMode)

export const DEFAULT_SORT = ResultViewMode.ByRule

export interface ResultViewState {
  sort: ResultViewMode
  /** null means every rule is selected. */
  ruleIds: ReadonlySet<string> | null
  /** null means every severity is selected. */
  severities: ReadonlySet<Severity> | null
  query: string
}

function parseSelection(raw: string | null, allowed: readonly string[]): Set<string> | null {
  if (raw === null) {
    return null
  }
  if (raw === '') {
    return new Set()
  }
  const valid = raw.split(LIST_SEPARATOR).filter((item) => allowed.includes(item))
  if (valid.length === 0 || valid.length >= allowed.length) {
    return null
  }
  return new Set(valid)
}

function isSort(value: string | null): value is ResultViewMode {
  return ALL_SORTS.some((sort) => sort === value)
}

export function parseResultViewState(
  params: URLSearchParams,
  knownRuleIds: readonly string[],
): ResultViewState {
  const sort = params.get(VIEW_PARAMS.sort)
  const severities = parseSelection(params.get(VIEW_PARAMS.severity), ALL_SEVERITIES)
  return {
    sort: isSort(sort) ? sort : DEFAULT_SORT,
    ruleIds: parseSelection(params.get(VIEW_PARAMS.rules), knownRuleIds),
    severities: severities as ReadonlySet<Severity> | null,
    query: params.get(VIEW_PARAMS.query) ?? '',
  }
}

function writeParam(params: URLSearchParams, key: string, value: string | null): void {
  if (value === null) {
    params.delete(key)
  } else {
    params.set(key, value)
  }
}

export function serializeResultViewState(
  state: ResultViewState,
  base: URLSearchParams = new URLSearchParams(),
): URLSearchParams {
  const params = new URLSearchParams(base)
  writeParam(params, VIEW_PARAMS.sort, state.sort === DEFAULT_SORT ? null : state.sort)
  writeParam(
    params,
    VIEW_PARAMS.rules,
    state.ruleIds === null ? null : [...state.ruleIds].join(LIST_SEPARATOR),
  )
  writeParam(
    params,
    VIEW_PARAMS.severity,
    state.severities === null ? null : [...state.severities].join(LIST_SEPARATOR),
  )
  writeParam(params, VIEW_PARAMS.query, state.query === '' ? null : state.query)
  return params
}

export function hasActiveFilters(state: ResultViewState): boolean {
  return state.ruleIds !== null || state.severities !== null || state.query.trim() !== ''
}
