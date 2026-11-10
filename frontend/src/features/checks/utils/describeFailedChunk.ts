import { FailureReason } from '../types/checkEnums'
import type { FailedChunk } from '../types/checkRun'

export const FAILURE_REASON_LABELS: Record<FailureReason, string> = {
  [FailureReason.QuotaExceeded]: 'The model quota was exceeded.',
  [FailureReason.Overloaded]: 'The model was overloaded.',
  [FailureReason.Timeout]: 'The model timed out.',
  [FailureReason.Blocked]: 'The model blocked the content.',
  [FailureReason.InvalidResponse]: 'The model returned an invalid response.',
  [FailureReason.Unavailable]: 'The model was unavailable.',
}

const TRAILING_NUMBER = /(\d+)$/

function blockNumber(blockId: string): number | null {
  const match = TRAILING_NUMBER.exec(blockId)
  return match?.[1] ? Number(match[1]) : null
}

export function describeBlockRange(firstBlockId: string, lastBlockId: string): string {
  const first = blockNumber(firstBlockId)
  const last = blockNumber(lastBlockId)
  if (first === null || last === null) {
    return `blocks ${firstBlockId} to ${lastBlockId}`
  }
  return first === last ? `paragraph ${first}` : `paragraphs ${first} to ${last}`
}

export function describeFailedChunk(chunk: FailedChunk): string {
  const range = describeBlockRange(chunk.first_block_id, chunk.last_block_id)
  return `${range[0]?.toUpperCase() ?? ''}${range.slice(1)}: ${FAILURE_REASON_LABELS[chunk.reason]}`
}
