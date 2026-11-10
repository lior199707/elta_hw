import type { InputHTMLAttributes, Ref } from 'react'

import { cn } from '@/lib/utils'

const FIELD_CLASSES =
  'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-slate-100 aria-invalid:border-red-500'

export { FIELD_CLASSES }

type InputProps = InputHTMLAttributes<HTMLInputElement> & { ref?: Ref<HTMLInputElement> }

export function Input({ className, ...props }: InputProps) {
  return <input className={cn(FIELD_CLASSES, className)} {...props} />
}
