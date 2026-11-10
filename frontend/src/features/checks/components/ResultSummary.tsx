import { Card } from '@/components/ui/card'
import { formatDateTime, formatDuration } from '@/lib/utils/formatDisplayValues'

import type { CheckRun } from '../types/checkRun'
import { StatusBadge } from './StatusBadge'

export function ResultSummary({ run }: { run: CheckRun }) {
  const { result } = run
  const items = [
    { label: 'Violations', value: String(result.violations.length) },
    { label: 'Rules checked', value: String(result.rules.length) },
    { label: 'Duration', value: formatDuration(result.duration_ms) },
    { label: 'Model', value: result.models_used.join(', ') || 'None' },
    { label: 'Checked on', value: formatDateTime(run.created_at) },
  ]

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold break-all text-slate-900">{result.document_name}</h1>
        <StatusBadge status={result.status} />
      </div>
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {items.map((item) => (
          <div key={item.label}>
            <dt className="text-xs font-medium tracking-wide text-slate-500 uppercase">
              {item.label}
            </dt>
            <dd className="mt-1 text-sm font-semibold text-slate-900">{item.value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}
