import * as DialogPrimitive from '@radix-ui/react-dialog'
import type { ReactNode } from 'react'

import { Button } from './button'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: ReactNode
}

export function Dialog({ open, onOpenChange, title, description, children }: DialogProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-slate-900/50" />
        <DialogPrimitive.Content className="fixed top-1/2 left-1/2 z-50 max-h-[90vh] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
          <DialogPrimitive.Title className="text-lg font-semibold text-slate-900">
            {title}
          </DialogPrimitive.Title>
          {description ? (
            <DialogPrimitive.Description className="mt-2 text-sm text-slate-600">
              {description}
            </DialogPrimitive.Description>
          ) : (
            <DialogPrimitive.Description className="sr-only">{title}</DialogPrimitive.Description>
          )}
          <div className="mt-4">{children}</div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  onConfirm: () => void
  isPending: boolean
  errorMessage?: string | null
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  onConfirm,
  isPending,
  errorMessage,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange} title={title} description={description}>
      {errorMessage ? (
        <p role="alert" className="mb-4 text-sm text-red-700">
          {errorMessage}
        </p>
      ) : null}
      <div className="flex justify-end gap-2">
        <Button
          variant="secondary"
          disabled={isPending}
          onClick={() => {
            onOpenChange(false)
          }}
        >
          Cancel
        </Button>
        <Button variant="danger" disabled={isPending} onClick={onConfirm}>
          {isPending ? 'Deleting...' : confirmLabel}
        </Button>
      </div>
    </Dialog>
  )
}
