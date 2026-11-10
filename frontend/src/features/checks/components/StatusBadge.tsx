import { Badge } from '@/components/ui/badge'
import type { BadgeTone } from '@/components/ui/badge'

import { CheckStatus } from '../types/checkEnums'

const STATUS_PRESENTATION: Record<CheckStatus, { label: string; tone: BadgeTone }> = {
  [CheckStatus.Completed]: { label: 'Completed', tone: 'success' },
  [CheckStatus.Partial]: { label: 'Partial', tone: 'warning' },
  [CheckStatus.Failed]: { label: 'Failed', tone: 'danger' },
}

export function StatusBadge({ status }: { status: CheckStatus }) {
  const { label, tone } = STATUS_PRESENTATION[status]
  return <Badge tone={tone}>{label}</Badge>
}
