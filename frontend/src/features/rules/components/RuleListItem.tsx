import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'

import type { Rule } from '../types/rule'

interface RuleListItemProps {
  rule: Rule
  isToggling: boolean
  onToggleActive: (rule: Rule, isActive: boolean) => void
  onEdit: (rule: Rule) => void
  onDelete: (rule: Rule) => void
}

export function RuleListItem({
  rule,
  isToggling,
  onToggleActive,
  onEdit,
  onDelete,
}: RuleListItemProps) {
  return (
    <li>
      <Card className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-slate-900">{rule.title}</h3>
            <Badge tone={rule.is_active ? 'success' : 'neutral'}>
              {rule.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          <p className="text-sm break-words whitespace-pre-wrap text-slate-600">{rule.text}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Switch
            label={`Active: ${rule.title}`}
            checked={rule.is_active}
            disabled={isToggling}
            onCheckedChange={(checked) => {
              onToggleActive(rule, checked)
            }}
          />
          <Button
            variant="secondary"
            size="sm"
            aria-label={`Edit ${rule.title}`}
            onClick={() => {
              onEdit(rule)
            }}
          >
            Edit
          </Button>
          <Button
            variant="ghost"
            size="sm"
            aria-label={`Delete ${rule.title}`}
            onClick={() => {
              onDelete(rule)
            }}
          >
            Delete
          </Button>
        </div>
      </Card>
    </li>
  )
}
