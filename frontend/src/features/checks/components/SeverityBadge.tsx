import { Badge } from '@/components/ui/badge'
import type { BadgeTone } from '@/components/ui/badge'

import { Severity } from '../types/checkEnums'

const SEVERITY_PRESENTATION: Record<Severity, { label: string; tone: BadgeTone }> = {
  [Severity.High]: { label: 'High', tone: 'danger' },
  [Severity.Medium]: { label: 'Medium', tone: 'warning' },
  [Severity.Low]: { label: 'Low', tone: 'info' },
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const { label, tone } = SEVERITY_PRESENTATION[severity]
  return (
    <Badge tone={tone} size="md">
      {label} severity
    </Badge>
  )
}
