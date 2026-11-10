import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

import { Severity } from '../types/checkEnums'
import type { ResultRule } from '../types/checkRun'
import type { ResultViewState } from '../utils/resultViewParams'

const SEVERITY_OPTIONS: { value: Severity; label: string }[] = [
  { value: Severity.High, label: 'High' },
  { value: Severity.Medium, label: 'Medium' },
  { value: Severity.Low, label: 'Low' },
]

interface ResultFiltersProps {
  rules: readonly ResultRule[]
  ruleCounts: ReadonlyMap<string, number>
  severityCounts: ReadonlyMap<Severity, number>
  state: ResultViewState
  shownCount: number
  totalCount: number
  hasActiveFilters: boolean
  onChange: (patch: Partial<ResultViewState>) => void
  onClear: () => void
}

function toggled<T>(current: ReadonlySet<T> | null, all: readonly T[], item: T): Set<T> | null {
  const next = new Set(current ?? all)
  if (!next.delete(item)) {
    next.add(item)
  }
  return next.size === all.length ? null : next
}

export function ResultFilters({
  rules,
  ruleCounts,
  severityCounts,
  state,
  shownCount,
  totalCount,
  hasActiveFilters,
  onChange,
  onClear,
}: ResultFiltersProps) {
  const allRuleIds = rules.map((rule) => rule.rule_id)
  const allSeverities = SEVERITY_OPTIONS.map((option) => option.value)

  return (
    <Card className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <fieldset className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <legend className="text-sm font-medium text-slate-800">Filter by rule</legend>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  onChange({ ruleIds: null })
                }}
              >
                All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  onChange({ ruleIds: new Set() })
                }}
              >
                None
              </Button>
            </div>
          </div>
          <ul className="space-y-1">
            {rules.map((rule) => (
              <li key={rule.rule_id}>
                <label className="flex items-center gap-2 text-sm text-slate-800">
                  <input
                    type="checkbox"
                    className="size-4 accent-indigo-600"
                    checked={state.ruleIds === null || state.ruleIds.has(rule.rule_id)}
                    onChange={() => {
                      onChange({ ruleIds: toggled(state.ruleIds, allRuleIds, rule.rule_id) })
                    }}
                  />
                  {rule.title} ({ruleCounts.get(rule.rule_id) ?? 0})
                </label>
              </li>
            ))}
          </ul>
        </fieldset>
        <div className="space-y-4">
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-slate-800">Filter by severity</legend>
            <ul className="flex flex-wrap gap-x-4 gap-y-1">
              {SEVERITY_OPTIONS.map((option) => (
                <li key={option.value}>
                  <label className="flex items-center gap-2 text-sm text-slate-800">
                    <input
                      type="checkbox"
                      className="size-4 accent-indigo-600"
                      checked={state.severities === null || state.severities.has(option.value)}
                      onChange={() => {
                        onChange({
                          severities: toggled(state.severities, allSeverities, option.value),
                        })
                      }}
                    />
                    {option.label} ({severityCounts.get(option.value) ?? 0})
                  </label>
                </li>
              ))}
            </ul>
          </fieldset>
          <div className="space-y-1">
            <label htmlFor="violation-search" className="text-sm font-medium text-slate-800">
              Search violations
            </label>
            <Input
              id="violation-search"
              type="search"
              placeholder="Quote, explanation or rule title"
              value={state.query}
              onChange={(event) => {
                onChange({ query: event.target.value })
              }}
            />
          </div>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p aria-live="polite" className="text-sm text-slate-700">
          Showing {shownCount} of {totalCount} {totalCount === 1 ? 'violation' : 'violations'}
        </p>
        <Button variant="secondary" size="sm" disabled={!hasActiveFilters} onClick={onClear}>
          Clear filters
        </Button>
      </div>
    </Card>
  )
}
