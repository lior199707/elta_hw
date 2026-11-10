import type { Ref, TextareaHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

import { FIELD_CLASSES } from './input'

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  ref?: Ref<HTMLTextAreaElement>
}

export function Textarea({ className, ...props }: TextareaProps) {
  return <textarea className={cn(FIELD_CLASSES, 'min-h-24', className)} {...props} />
}
