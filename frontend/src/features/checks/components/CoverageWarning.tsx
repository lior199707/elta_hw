import { Alert } from '@/components/ui/alert'

import { CheckStatus } from '../types/checkEnums'
import type { CheckResult } from '../types/checkRun'
import { describeFailedChunk } from '../utils/describeFailedChunk'

type CoverageWarningProps = Pick<CheckResult, 'status' | 'failed_chunks'>

export function CoverageWarning({ status, failed_chunks }: CoverageWarningProps) {
  if (status === CheckStatus.Completed) {
    return null
  }
  const isFailed = status === CheckStatus.Failed

  return (
    <Alert tone={isFailed ? 'error' : 'warning'}>
      <p className="font-semibold">
        {isFailed ? 'The document was NOT checked.' : 'Part of the document was NOT checked.'}
      </p>
      <p className="mt-1">
        {isFailed
          ? 'The check failed before any result was produced. Do not treat this document as compliant.'
          : 'The findings below are incomplete. Unchecked sections may contain further violations, so do not treat this document as compliant.'}
      </p>
      {failed_chunks.length > 0 ? (
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {failed_chunks.map((chunk) => (
            <li key={chunk.chunk_id}>{describeFailedChunk(chunk)}</li>
          ))}
        </ul>
      ) : null}
    </Alert>
  )
}
