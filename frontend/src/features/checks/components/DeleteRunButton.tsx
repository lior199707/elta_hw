import { useState } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/dialog'
import { getErrorMessage } from '@/lib/api/getErrorMessage'
import { ROUTES } from '@/lib/routes'

import { useDeleteCheck } from '../hooks/useCheckMutations'

export function DeleteRunButton({ runId, documentName }: { runId: number; documentName: string }) {
  const navigate = useNavigate()
  const deleteCheck = useDeleteCheck()
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <Button
        variant="secondary"
        onClick={() => {
          deleteCheck.reset()
          setIsOpen(true)
        }}
      >
        Delete run
      </Button>
      <ConfirmDialog
        open={isOpen}
        onOpenChange={setIsOpen}
        title="Delete check run"
        description={`Delete the check run for "${documentName}"? This cannot be undone.`}
        confirmLabel="Delete run"
        isPending={deleteCheck.isPending}
        errorMessage={deleteCheck.error ? getErrorMessage(deleteCheck.error) : null}
        onConfirm={() => {
          deleteCheck.mutate(runId, {
            onSuccess: () => {
              toast.success('Check run deleted')
              void navigate(ROUTES.history)
            },
          })
        }}
      />
    </>
  )
}
