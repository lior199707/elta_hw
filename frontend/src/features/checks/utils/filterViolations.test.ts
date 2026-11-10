import { describe, expect, it } from 'vitest'

import { Severity } from '../types/checkEnums'
import { makeCheckRun } from './checkRunFixtures'
import {
  countByRule,
  countBySeverity,
  filterRuleGroups,
  filterViolations,
} from './filterViolations'
import { groupViolationsByRule, resolveViolations } from './groupViolations'

const result = makeCheckRun().result
const violations = resolveViolations(result)
const groups = groupViolationsByRule(result)
const NO_FILTERS = { ruleIds: null, severities: null, query: '' }

function quotes(list: { quote: string }[]) {
  return list.map((violation) => violation.quote)
}

describe('filterViolations', () => {
  it('returns everything when no filter is active', () => {
    expect(filterViolations(violations, NO_FILTERS)).toHaveLength(3)
  })

  it('filters by selected rules', () => {
    const filtered = filterViolations(violations, { ...NO_FILTERS, ruleIds: new Set(['R1']) })

    expect(quotes(filtered)).toEqual(['120 km/h'])
  })

  it('returns nothing when no rule is selected', () => {
    expect(filterViolations(violations, { ...NO_FILTERS, ruleIds: new Set() })).toEqual([])
  })

  it('filters by severity', () => {
    const filtered = filterViolations(violations, {
      ...NO_FILTERS,
      severities: new Set([Severity.High, Severity.Low]),
    })

    expect(quotes(filtered)).toEqual(['120 km/h', 'John Smith'])
  })

  it('searches quote, explanation and rule title case-insensitively', () => {
    const search = (query: string) => quotes(filterViolations(violations, { ...NO_FILTERS, query }))

    expect(search('KM/H')).toEqual(['120 km/h'])
    expect(search('discloses a location')).toEqual(['Tel Aviv'])
    expect(search('personal names')).toEqual(['John Smith'])
    expect(search('  nothing matches  ')).toEqual([])
  })

  it('combines rule, severity and search filters with AND', () => {
    const state = {
      ruleIds: new Set(['R1', 'R2']),
      severities: new Set([Severity.High]),
      query: 'speed',
    }

    expect(quotes(filterViolations(violations, state))).toEqual(['120 km/h'])
    expect(filterViolations(violations, { ...state, query: 'location' })).toEqual([])
  })

  it('handles an empty violation list', () => {
    expect(filterViolations([], NO_FILTERS)).toEqual([])
  })
})

describe('filterRuleGroups', () => {
  it('keeps every group, including passed ones, when no filter is active', () => {
    expect(filterRuleGroups(groups, NO_FILTERS)).toHaveLength(4)
  })

  it('hides unchecked rules entirely, including passed groups', () => {
    const filtered = filterRuleGroups(groups, { ...NO_FILTERS, ruleIds: new Set(['R1', 'R4']) })

    expect(filtered.map((group) => group.rule.rule_id)).toEqual(['R1', 'R4'])
    const withoutPassed = filterRuleGroups(groups, { ...NO_FILTERS, ruleIds: new Set(['R1']) })
    expect(withoutPassed.map((group) => group.rule.rule_id)).toEqual(['R1'])
  })

  it('drops groups without matches and hides passed groups while narrowing', () => {
    const filtered = filterRuleGroups(groups, {
      ...NO_FILTERS,
      severities: new Set([Severity.Low]),
    })

    expect(filtered.map((group) => group.rule.rule_id)).toEqual(['R2'])
  })

  it('returns no groups when nothing is selected', () => {
    expect(filterRuleGroups(groups, { ...NO_FILTERS, ruleIds: new Set() })).toEqual([])
  })
})

describe('counts', () => {
  it('counts violations per rule and per severity', () => {
    expect(Object.fromEntries(countByRule(violations))).toEqual({ R1: 1, R2: 1, R3: 1 })
    expect(Object.fromEntries(countBySeverity(violations))).toEqual({
      high: 1,
      medium: 1,
      low: 1,
    })
  })

  it('returns empty maps for no violations', () => {
    expect(countByRule([]).size).toBe(0)
  })
})
