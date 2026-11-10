import { useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'

import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/dialog'
import { Spinner } from '@/components/ui/spinner'
import { getErrorMessage } from '@/lib/api/getErrorMessage'
import { ROUTES } from '@/lib/routes'
import { formatDateTime } from '@/lib/utils/formatDisplayValues'

import { useDeleteCheck } from '../hooks/useCheckMutations'
import { useChecks } from '../hooks/useChecks'
import type { CheckRunSummary } from '../types/checkRun'
import { StatusBadge } from './StatusBadge'

export function HistoryList() {
  const checksQuery = useChecks()
  const deleteCheck = useDeleteCheck()
  const [runToDelete, setRunToDelete] = useState<CheckRunSummary | null>(null)

  if (checksQuery.isPending) {
    return (
      <p role="status" className="flex items-center gap-2 text-slate-600">
        <Spinner /> Loading history...
      </p>
    )
  }

  if (checksQuery.isError) {
    return (
      <Alert tone="error">
        <p>Could not load history: {getErrorMessage(checksQuery.error)}</p>
        <Button
          variant="secondary"
          size="sm"
          className="mt-2"
          onClick={() => {
            void checksQuery.refetch()
          }}
        >
          Retry
        </Button>
      </Alert>
    )
  }

  if (checksQuery.data.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
        <p className="text-slate-700">No checks have been run yet.</p>
        <p className="mt-1 text-sm text-slate-600">
          <Link to={ROUTES.check} className="font-medium text-indigo-700 underline">
            Run your first check
          </Link>
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Check history, newest first</caption>
          <thead className="bg-slate-50 text-xs text-slate-600 uppercase">
            <tr>
              <th scope="col" className="px-4 py-3">
                Date
              </th>
              <th scope="col" className="px-4 py-3">
                Document
              </th>
              <th scope="col" className="px-4 py-3">
                Status
              </th>
              <th scope="col" className="px-4 py-3">
                Violations
              </th>
              <th scope="col" className="px-4 py-3">
                Model
              </th>
              <th scope="col" className="px-4 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {checksQuery.data.map((run) => (
              <tr key={run.id}>
                <td className="px-4 py-3 whitespace-nowrap text-slate-700">
                  {formatDateTime(run.created_at)}
                </td>
                <td className="px-4 py-3 break-all">
                  <Link
                    to={ROUTES.historyDetail(run.id)}
                    className="font-medium text-indigo-700 underline"
                  >
                    {run.document_name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={run.status} />
                </td>
                <td className="px-4 py-3">{run.violation_count}</td>
                <td className="px-4 py-3 text-slate-700">{run.models_used.join(', ') || 'None'}</td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label={`Delete run ${run.document_name}`}
                    onClick={() => {
                      deleteCheck.reset()
                      setRunToDelete(run)
                    }}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ConfirmDialog
        open={runToDelete !== null}
        onOpenChange={(open) => {
          if (!open) {
            setRunToDelete(null)
          }
        }}
        title="Delete check run"
        description={`Delete the check run for "${runToDelete?.document_name ?? ''}"? This cannot be undone.`}
        confirmLabel="Delete run"
        isPending={deleteCheck.isPending}
        errorMessage={deleteCheck.error ? getErrorMessage(deleteCheck.error) : null}
        onConfirm={() => {
          if (runToDelete) {
            deleteCheck.mutate(runToDelete.id, {
              onSuccess: () => {
                toast.success('Check run deleted')
                setRunToDelete(null)
              },
            })
          }
        }}
      />
    </>
  )
}
