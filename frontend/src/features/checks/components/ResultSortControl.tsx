import { cn } from '@/lib/utils'

import { ResultViewMode } from '../types/checkEnums'

const SORT_OPTIONS: { value: ResultViewMode; label: string }[] = [
  { value: ResultViewMode.ByRule, label: 'Rule' },
  { value: ResultViewMode.Position, label: 'Position in document' },
]

interface ResultSortControlProps {
  value: ResultViewMode
  onChange: (value: ResultViewMode) => void
}

export function ResultSortControl({ value, onChange }: ResultSortControlProps) {
  return (
    <fieldset className="flex flex-wrap items-center gap-3">
      <legend className="sr-only">Sort violations by</legend>
      <span aria-hidden="true" className="text-sm font-medium text-slate-800">
        Sort violations by
      </span>
      <div className="inline-flex overflow-hidden rounded-md border border-slate-300">
        {SORT_OPTIONS.map((option) => (
          <label
            key={option.value}
            className={cn(
              'cursor-pointer px-3 py-1.5 text-sm font-medium has-[:focus-visible]:outline-2 has-[:focus-visible]:-outline-offset-2 has-[:focus-visible]:outline-indigo-600',
              value === option.value
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-700 hover:bg-slate-50',
            )}
          >
            <input
              type="radio"
              name="violation-sort"
              className="sr-only"
              value={option.value}
              checked={value === option.value}
              onChange={() => {
                onChange(option.value)
              }}
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
