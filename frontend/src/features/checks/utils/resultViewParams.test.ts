import { describe, expect, it } from 'vitest'

import { ResultViewMode, Severity } from '../types/checkEnums'
import {
  hasActiveFilters,
  parseResultViewState,
  serializeResultViewState,
} from './resultViewParams'

const RULES = ['R1', 'R2', 'R3']

function parse(search: string) {
  return parseResultViewState(new URLSearchParams(search), RULES)
}

describe('parseResultViewState', () => {
  it('returns defaults for an empty query string', () => {
    expect(parse('')).toEqual({
      sort: ResultViewMode.ByRule,
      ruleIds: null,
      severities: null,
      query: '',
    })
  })

  it('parses valid sort, rules, severity and query', () => {
    const state = parse('sort=position&rules=R1,R3&severity=high&q=km')

    expect(state.sort).toBe(ResultViewMode.Position)
    expect([...(state.ruleIds ?? [])]).toEqual(['R1', 'R3'])
    expect([...(state.severities ?? [])]).toEqual([Severity.High])
    expect(state.query).toBe('km')
  })

  it('ignores an invalid sort value', () => {
    expect(parse('sort=banana').sort).toBe(ResultViewMode.ByRule)
  })

  it('drops unknown rule ids and falls back to all rules when none are valid', () => {
    expect([...(parse('rules=R1,BOGUS').ruleIds ?? [])]).toEqual(['R1'])
    expect(parse('rules=BOGUS').ruleIds).toBeNull()
  })

  it('treats an empty rules param as no rules selected', () => {
    expect(parse('rules=').ruleIds?.size).toBe(0)
  })

  it('ignores invalid severities', () => {
    expect(parse('severity=extreme').severities).toBeNull()
    expect([...(parse('severity=low,extreme').severities ?? [])]).toEqual([Severity.Low])
  })

  it('normalizes a full selection to null', () => {
    expect(parse('rules=R1,R2,R3').ruleIds).toBeNull()
    expect(parse('severity=high,medium,low').severities).toBeNull()
  })
})

describe('serializeResultViewState', () => {
  it('omits defaults', () => {
    expect(serializeResultViewState(parse('')).toString()).toBe('')
  })

  it('round-trips a filtered state', () => {
    const search = 'sort=position&rules=R1%2CR3&severity=high&q=km'

    expect(serializeResultViewState(parse(search)).toString()).toBe(search)
  })

  it('keeps unrelated params and removes cleared ones', () => {
    const base = new URLSearchParams('keep=1&q=old')

    expect(serializeResultViewState(parse(''), base).toString()).toBe('keep=1')
  })

  it('serializes an empty selection as an empty param', () => {
    const state = { ...parse(''), ruleIds: new Set<string>() }

    expect(serializeResultViewState(state).toString()).toBe('rules=')
  })
})

describe('hasActiveFilters', () => {
  it('is false for defaults, including sort changes', () => {
    expect(hasActiveFilters(parse('sort=position'))).toBe(false)
  })

  it('is true when rules, severity or a non-blank query is set', () => {
    expect(hasActiveFilters(parse('rules=R1'))).toBe(true)
    expect(hasActiveFilters(parse('severity=low'))).toBe(true)
    expect(hasActiveFilters(parse('q=abc'))).toBe(true)
    expect(hasActiveFilters(parse('q=%20'))).toBe(false)
  })
})
