import { Link, useParams } from 'react-router'

import { Alert } from '@/components/ui/alert'
import { CheckRunDetail } from '@/features/checks/components/CheckRunDetail'
import { HISTORY_ID_PARAM, ROUTES } from '@/lib/routes'

export function CheckResultPage() {
  const rawId = useParams()[HISTORY_ID_PARAM]
  const runId = Number(rawId)

  if (!rawId || !Number.isInteger(runId) || runId <= 0) {
    return (
      <Alert tone="error">
        <p>This check run id is not valid.</p>
        <Link to={ROUTES.history} className="mt-2 inline-block font-medium underline">
          Back to history
        </Link>
      </Alert>
    )
  }

  return <CheckRunDetail runId={runId} />
}
