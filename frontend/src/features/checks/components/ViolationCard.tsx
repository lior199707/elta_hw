import { Card } from '@/components/ui/card'

import type { ViolationView } from '../types/checkRun'
import { splitHighlight } from '../utils/splitHighlight'
import { LocationChips } from './LocationChips'
import { SeverityBadge } from './SeverityBadge'

interface ViolationCardProps {
  violation: ViolationView
  showRuleTitle: boolean
}

export function ViolationCard({ violation, showRuleTitle }: ViolationCardProps) {
  const { before, match, after } = splitHighlight(
    violation.block.text,
    violation.start,
    violation.end,
  )

  return (
    <li>
      <Card className="space-y-3">
        {showRuleTitle ? (
          <h4 className="text-base font-semibold text-slate-900">{violation.ruleTitle}</h4>
        ) : null}
        <div>
          <SeverityBadge severity={violation.severity} />
        </div>
        <LocationChips location={violation.location} />
        <blockquote className="rounded-md border-l-4 border-slate-300 bg-slate-50 p-3 text-sm break-words whitespace-pre-wrap text-slate-800">
          {before}
          <mark className="rounded bg-yellow-200 px-0.5 font-medium text-slate-900">{match}</mark>
          {after}
        </blockquote>
        <p className="text-sm text-slate-700">{violation.explanation}</p>
      </Card>
    </li>
  )
}
