import { Badge } from '@/components/ui/badge'
import type { BadgeTone } from '@/components/ui/badge'

import { RuleOutcome } from '../types/checkEnums'
import type { RuleGroup } from '../types/checkRun'
import { ViolationCard } from './ViolationCard'

const OUTCOME_PRESENTATION: Record<
  Exclude<RuleOutcome, typeof RuleOutcome.Violated>,
  { label: string; tone: BadgeTone }
> = {
  [RuleOutcome.Passed]: { label: 'Passed', tone: 'success' },
  [RuleOutcome.PassedPartial]: { label: 'No violations in checked parts', tone: 'warning' },
  [RuleOutcome.NotChecked]: { label: 'Not checked', tone: 'danger' },
}

export function RuleGroupSection({ group }: { group: RuleGroup }) {
  const headingId = `rule-group-${group.rule.rule_id}`
  const outcomeBadge =
    group.outcome === RuleOutcome.Violated ? (
      <Badge tone="danger">
        {group.violations.length} {group.violations.length === 1 ? 'violation' : 'violations'}
      </Badge>
    ) : (
      <Badge tone={OUTCOME_PRESENTATION[group.outcome].tone}>
        {OUTCOME_PRESENTATION[group.outcome].label}
      </Badge>
    )

  return (
    <section aria-labelledby={headingId} className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <h3 id={headingId} className="text-lg font-semibold text-slate-900">
          {group.rule.title}
        </h3>
        {outcomeBadge}
      </div>
      {group.violations.length > 0 ? (
        <ul className="space-y-3">
          {group.violations.map((violation) => (
            <ViolationCard
              key={`${violation.rule_id}-${violation.block_id}-${violation.start}-${violation.end}`}
              violation={violation}
              showRuleTitle={false}
            />
          ))}
        </ul>
      ) : null}
    </section>
  )
}
