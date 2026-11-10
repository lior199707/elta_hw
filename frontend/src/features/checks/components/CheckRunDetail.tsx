import { Link } from 'react-router'

import { Alert } from '@/components/ui/alert'
import { buttonVariants } from '@/components/ui/buttonVariants'
import { Spinner } from '@/components/ui/spinner'
import { getErrorMessage } from '@/lib/api/getErrorMessage'
import { ROUTES } from '@/lib/routes'

import { useCheck } from '../hooks/useChecks'
import { CheckResultView } from './CheckResultView'
import { DeleteRunButton } from './DeleteRunButton'

export function CheckRunDetail({ runId }: { runId: number }) {
  const checkQuery = useCheck(runId)

  if (checkQuery.isPending) {
    return (
      <p role="status" className="flex items-center gap-2 text-slate-600">
        <Spinner /> Loading result...
      </p>
    )
  }

  if (checkQuery.isError) {
    return (
      <Alert tone="error">
        <p>Could not load this check run: {getErrorMessage(checkQuery.error)}</p>
        <Link to={ROUTES.history} className="mt-2 inline-block font-medium underline">
          Back to history
        </Link>
      </Alert>
    )
  }

  const run = checkQuery.data
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to={ROUTES.history} className="text-sm font-medium text-indigo-700 underline">
          Back to history
        </Link>
        <div className="flex gap-2">
          <Link to={ROUTES.check} className={buttonVariants({ variant: 'secondary' })}>
            New check
          </Link>
          <DeleteRunButton runId={run.id} documentName={run.result.document_name} />
        </div>
      </div>
      <CheckResultView run={run} />
    </div>
  )
}
