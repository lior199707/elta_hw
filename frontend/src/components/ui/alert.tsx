import { cva } from 'class-variance-authority'
import type { VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

const alertVariants = cva('rounded-md border p-4 text-sm', {
  variants: {
    tone: {
      error: 'border-red-300 bg-red-50 text-red-900',
      warning: 'border-amber-300 bg-amber-50 text-amber-900',
      info: 'border-sky-300 bg-sky-50 text-sky-900',
    },
  },
  defaultVariants: { tone: 'info' },
})

type AlertProps = HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>

export function Alert({ className, tone, role = 'alert', ...props }: AlertProps) {
  return <div role={role} className={cn(alertVariants({ tone }), className)} {...props} />
}
