import { describeBlockLocation } from './describeBlockLocation'
import { CheckStatus, RuleOutcome } from '../types/checkEnums'
import type { CheckResult, RuleGroup, ViolationView } from '../types/checkRun'

function compareDocumentOrder(a: ViolationView, b: ViolationView): number {
  return a.block.index - b.block.index || a.start - b.start || a.end - b.end
}

export function resolveViolations(result: CheckResult): ViolationView[] {
  const blocksById = new Map(result.context_blocks.map((block) => [block.block_id, block]))
  const titlesById = new Map(result.rules.map((rule) => [rule.rule_id, rule.title]))
  return result.violations
    .map((violation) => {
      const block = blocksById.get(violation.block_id)
      const ruleTitle = titlesById.get(violation.rule_id)
      if (!block || ruleTitle === undefined) {
        throw new Error(`Unresolvable violation: ${violation.rule_id} in ${violation.block_id}`)
      }
      const location = describeBlockLocation(block, result.block_count)
      return { ...violation, block, ruleTitle, location }
    })
    .sort(compareDocumentOrder)
}

function outcomeWithoutViolations(status: CheckResult['status']): RuleOutcome {
  if (status === CheckStatus.Failed) {
    return RuleOutcome.NotChecked
  }
  return status === CheckStatus.Partial ? RuleOutcome.PassedPartial : RuleOutcome.Passed
}

export function groupViolationsByRule(result: CheckResult): RuleGroup[] {
  const violations = resolveViolations(result)
  return result.rules.map((rule) => {
    const ruleViolations = violations.filter((violation) => violation.rule_id === rule.rule_id)
    return {
      rule,
      violations: ruleViolations,
      outcome:
        ruleViolations.length > 0 ? RuleOutcome.Violated : outcomeWithoutViolations(result.status),
    }
  })
}
