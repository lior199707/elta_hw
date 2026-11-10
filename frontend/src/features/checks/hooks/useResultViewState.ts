import { useMemo } from 'react'
import { useSearchParams } from 'react-router'

import { parseResultViewState, serializeResultViewState } from '../utils/resultViewParams'
import type { ResultViewState } from '../utils/resultViewParams'

export function useResultViewState(knownRuleIds: readonly string[]) {
  const [searchParams, setSearchParams] = useSearchParams()
  const state = useMemo(
    () => parseResultViewState(searchParams, knownRuleIds),
    [searchParams, knownRuleIds],
  )

  const update = (patch: Partial<ResultViewState>) => {
    setSearchParams(
      (previous) =>
        serializeResultViewState(
          { ...parseResultViewState(previous, knownRuleIds), ...patch },
          previous,
        ),
      { replace: true },
    )
  }

  const clearFilters = () => {
    update({ ruleIds: null, severities: null, query: '' })
  }

  return { state, update, clearFilters }
}
