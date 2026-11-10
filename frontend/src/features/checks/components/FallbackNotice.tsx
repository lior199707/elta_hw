import { Alert } from '@/components/ui/alert'

import type { CheckResult } from '../types/checkRun'

type FallbackNoticeProps = Pick<CheckResult, 'fallback_chunk_count' | 'chunks_total'>

export function FallbackNotice({ fallback_chunk_count, chunks_total }: FallbackNoticeProps) {
  if (!fallback_chunk_count || fallback_chunk_count <= 0) {
    return null
  }
  const chunkNoun = chunks_total === 1 ? 'chunk' : 'chunks'
  const verb = chunks_total === 1 ? 'was' : 'were'

  return (
    <Alert tone="warning" role="status">
      {fallback_chunk_count} of {chunks_total} {chunkNoun} {verb} checked by the fallback model
      because the primary model was unavailable. The fallback model is less capable and may miss
      findings; consider re-running later.
    </Alert>
  )
}
