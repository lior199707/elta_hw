import { useMemo } from 'react'

import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

import { useResultViewState } from '../hooks/useResultViewState'
import { CheckStatus, ResultViewMode } from '../types/checkEnums'
import type { CheckRun } from '../types/checkRun'
import { describeLocationNote } from '../utils/describeBlockLocation'
import {
  countByRule,
  countBySeverity,
  filterRuleGroups,
  filterViolations,
} from '../utils/filterViolations'
import { groupViolationsByRule, resolveViolations } from '../utils/groupViolations'
import { hasActiveFilters } from '../utils/resultViewParams'
import { CoverageWarning } from './CoverageWarning'
import { FallbackNotice } from './FallbackNotice'
import { ResultFilters } from './ResultFilters'
import { ResultSortControl } from './ResultSortControl'
import { ResultSummary } from './ResultSummary'
import { RuleGroupSection } from './RuleGroupSection'
import { ViolationCard } from './ViolationCard'

export function CheckResultView({ run }: { run: CheckRun }) {
  const { result } = run
  const knownRuleIds = useMemo(() => result.rules.map((rule) => rule.rule_id), [result.rules])
  const { state, update, clearFilters } = useResultViewState(knownRuleIds)
  const groups = useMemo(() => groupViolationsByRule(result), [result])
  const violations = useMemo(() => resolveViolations(result), [result])
  const ruleCounts = useMemo(() => countByRule(violations), [violations])
  const severityCounts = useMemo(() => countBySeverity(violations), [violations])

  const filteredViolations = filterViolations(violations, state)
  const filteredGroups = filterRuleGroups(groups, state)
  const filtersActive = hasActiveFilters(state)
  const hasViolations = violations.length > 0
  const nothingMatches = hasViolations && filteredViolations.length === 0

  let list
  if (nothingMatches) {
    list = (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
        <p className="text-slate-700">No violations match the current filters</p>
        <Button variant="secondary" size="sm" className="mt-3" onClick={clearFilters}>
          Clear filters
        </Button>
      </div>
    )
  } else if (state.sort === ResultViewMode.ByRule) {
    list = (
      <div className="space-y-8">
        {filteredGroups.map((group) => (
          <RuleGroupSection key={group.rule.rule_id} group={group} />
        ))}
      </div>
    )
  } else {
    list = (
      <ul className="space-y-3" aria-label="Violations by position in document">
        {filteredViolations.map((violation) => (
          <ViolationCard
            key={`${violation.rule_id}-${violation.block_id}-${violation.start}-${violation.end}`}
            violation={violation}
            showRuleTitle
          />
        ))}
      </ul>
    )
  }

  return (
    <div className="space-y-6">
      <ResultSummary run={run} />
      <CoverageWarning status={result.status} failed_chunks={result.failed_chunks} />
      <FallbackNotice
        fallback_chunk_count={result.fallback_chunk_count}
        chunks_total={result.chunks_total}
      />
      {result.dropped_count > 0 ? (
        <Alert tone="info" role="note">
          {result.dropped_count} model{' '}
          {result.dropped_count === 1 ? 'finding was' : 'findings were'} discarded because{' '}
          {result.dropped_count === 1 ? 'its quote was' : 'their quotes were'} not found in the
          document.
        </Alert>
      ) : null}
      {result.status === CheckStatus.Completed && !hasViolations ? (
        <Alert tone="info" role="status">
          No violations were found. All {result.rules.length} rules passed.
        </Alert>
      ) : null}
      <p className="text-xs text-slate-500">
        {describeLocationNote(result.has_page_layout, result.context_blocks)}
      </p>
      {hasViolations ? (
        <>
          <ResultSortControl
            value={state.sort}
            onChange={(sort) => {
              update({ sort })
            }}
          />
          <ResultFilters
            rules={result.rules}
            ruleCounts={ruleCounts}
            severityCounts={severityCounts}
            state={state}
            shownCount={filteredViolations.length}
            totalCount={violations.length}
            hasActiveFilters={filtersActive}
            onChange={update}
            onClear={clearFilters}
          />
        </>
      ) : null}
      {list}
    </div>
  )
}
