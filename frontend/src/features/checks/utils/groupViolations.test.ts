import { describe, expect, it } from 'vitest'

import { CheckStatus, RuleOutcome } from '../types/checkEnums'
import { makeCheckRun } from './checkRunFixtures'
import { groupViolationsByRule, resolveViolations } from './groupViolations'

describe('resolveViolations', () => {
  it('sorts by block index then start offset', () => {
    const violations = resolveViolations(makeCheckRun().result)

    expect(violations.map((violation) => violation.quote)).toEqual([
      '120 km/h',
      'Tel Aviv',
      'John Smith',
    ])
  })

  it('attaches the block and the snapshot rule title', () => {
    const [first] = resolveViolations(makeCheckRun().result)

    expect(first?.block.block_id).toBe('B3')
    expect(first?.ruleTitle).toBe('No performance figures')
  })

  it('returns an empty list when there are no violations', () => {
    expect(resolveViolations(makeCheckRun({ violations: [] }).result)).toEqual([])
  })

  it('throws when a block is missing', () => {
    expect(() => resolveViolations(makeCheckRun({ context_blocks: [] }).result)).toThrow(
      'Unresolvable violation',
    )
  })
})

describe('groupViolationsByRule', () => {
  it('keeps snapshot rule order and counts violations per rule', () => {
    const groups = groupViolationsByRule(makeCheckRun().result)

    expect(groups.map((group) => [group.rule.rule_id, group.violations.length])).toEqual([
      ['R1', 1],
      ['R2', 1],
      ['R3', 1],
      ['R4', 0],
    ])
    expect(groups[0]?.outcome).toBe(RuleOutcome.Violated)
  })

  it('marks rules without violations as passed on a completed run', () => {
    const groups = groupViolationsByRule(makeCheckRun().result)

    expect(groups[3]?.outcome).toBe(RuleOutcome.Passed)
  })

  it('does not claim a pass for partial runs', () => {
    const groups = groupViolationsByRule(makeCheckRun({ status: CheckStatus.Partial }).result)

    expect(groups[3]?.outcome).toBe(RuleOutcome.PassedPartial)
  })

  it('marks rules as not checked when the run failed', () => {
    const run = makeCheckRun({ status: CheckStatus.Failed, violations: [], context_blocks: [] })

    const groups = groupViolationsByRule(run.result)

    expect(groups.every((group) => group.outcome === RuleOutcome.NotChecked)).toBe(true)
  })
})
