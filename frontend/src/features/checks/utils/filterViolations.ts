import type { Severity } from '../types/checkEnums'
import type { RuleGroup, ViolationView } from '../types/checkRun'
import type { ResultViewState } from './resultViewParams'

type FilterState = Pick<ResultViewState, 'ruleIds' | 'severities' | 'query'>

function matchesQuery(violation: ViolationView, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (needle === '') {
    return true
  }
  return [violation.quote, violation.explanation, violation.ruleTitle].some((field) =>
    field.toLowerCase().includes(needle),
  )
}

export function filterViolations(
  violations: readonly ViolationView[],
  state: FilterState,
): ViolationView[] {
  return violations.filter(
    (violation) =>
      (state.ruleIds === null || state.ruleIds.has(violation.rule_id)) &&
      (state.severities === null || state.severities.has(violation.severity)) &&
      matchesQuery(violation, state.query),
  )
}

export function filterRuleGroups(groups: readonly RuleGroup[], state: FilterState): RuleGroup[] {
  const narrowsViolations = state.severities !== null || state.query.trim() !== ''
  return groups.flatMap((group) => {
    if (state.ruleIds !== null && !state.ruleIds.has(group.rule.rule_id)) {
      return []
    }
    const violations = filterViolations(group.violations, state)
    const keepEmptyPassedGroup = group.violations.length === 0 && !narrowsViolations
    return violations.length > 0 || keepEmptyPassedGroup ? [{ ...group, violations }] : []
  })
}

export function countByRule(violations: readonly ViolationView[]): Map<string, number> {
  const counts = new Map<string, number>()
  violations.forEach((violation) => {
    counts.set(violation.rule_id, (counts.get(violation.rule_id) ?? 0) + 1)
  })
  return counts
}

export function countBySeverity(violations: readonly ViolationView[]): Map<Severity, number> {
  const counts = new Map<Severity, number>()
  violations.forEach((violation) => {
    counts.set(violation.severity, (counts.get(violation.severity) ?? 0) + 1)
  })
  return counts
}
