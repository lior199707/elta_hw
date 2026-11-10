import type { BlockLocation } from '../utils/describeBlockLocation'

export function LocationChips({ location }: { location: BlockLocation }) {
  return (
    <dl aria-label="Location in document" className="flex flex-wrap gap-2">
      {location.parts.map((part) => (
        <div
          key={`${part.label}-${part.value}`}
          title={part.title}
          className="inline-flex max-w-full min-w-0 items-baseline gap-1.5 rounded-md border border-slate-300 bg-slate-100 px-2 py-1 text-xs"
        >
          <dt className="shrink-0 font-medium tracking-wide text-slate-500 uppercase">
            {part.label}
          </dt>
          <dd className="max-w-xs min-w-0 truncate font-semibold text-slate-900">{part.value}</dd>
        </div>
      ))}
    </dl>
  )
}
