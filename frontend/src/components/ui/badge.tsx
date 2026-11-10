import { cva } from 'class-variance-authority'
import type { VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

const badgeVariants = cva('inline-flex items-center rounded-full font-semibold', {
  variants: {
    size: {
      sm: 'px-2.5 py-0.5 text-xs',
      md: 'px-3 py-1 text-sm',
    },
    tone: {
      neutral: 'bg-slate-100 text-slate-700',
      success: 'bg-emerald-100 text-emerald-800',
      warning: 'bg-amber-100 text-amber-900',
      danger: 'bg-red-100 text-red-800',
      info: 'bg-sky-100 text-sky-800',
    },
  },
  defaultVariants: { size: 'sm', tone: 'neutral' },
})

type BadgeProps = HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>

export function Badge({ className, tone, size, ...props }: BadgeProps) {
  return (
    <span
      data-size={size ?? 'sm'}
      className={cn(badgeVariants({ tone, size }), className)}
      {...props}
    />
  )
}

export type BadgeTone = NonNullable<VariantProps<typeof badgeVariants>['tone']>
