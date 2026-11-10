import { Button } from '@/components/ui/button'

import type { SelectableRule } from '../types/checkRun'

interface RuleSelectorProps {
  rules: SelectableRule[]
  selectedIds: ReadonlySet<number>
  disabled: boolean
  onToggle: (ruleId: number) => void
  onSelectAll: () => void
  onSelectNone: () => void
}

export function RuleSelector({
  rules,
  selectedIds,
  disabled,
  onToggle,
  onSelectAll,
  onSelectNone,
}: RuleSelectorProps) {
  return (
    <fieldset className="space-y-3" disabled={disabled}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <legend className="font-medium text-slate-900">
          Rules ({selectedIds.size} of {rules.length} selected)
        </legend>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onSelectAll}>
            Select all
          </Button>
          <Button variant="ghost" size="sm" onClick={onSelectNone}>
            Select none
          </Button>
        </div>
      </div>
      <ul className="space-y-2">
        {rules.map((rule) => (
          <li key={rule.id}>
            <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 bg-white p-3 has-[:checked]:border-indigo-300 has-[:checked]:bg-indigo-50">
              <input
                type="checkbox"
                className="mt-1 size-4 accent-indigo-600"
                checked={selectedIds.has(rule.id)}
                onChange={() => {
                  onToggle(rule.id)
                }}
              />
              <span>
                <span className="block font-medium text-slate-900">{rule.title}</span>
                <span className="block text-sm text-slate-600">{rule.text}</span>
              </span>
            </label>
          </li>
        ))}
      </ul>
    </fieldset>
  )
}
