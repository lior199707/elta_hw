import { describe, expect, it } from 'vitest'

import { FailureReason } from '../types/checkEnums'
import { failedChunk } from './checkRunFixtures'
import {
  describeBlockRange,
  describeFailedChunk,
  FAILURE_REASON_LABELS,
} from './describeFailedChunk'

describe('describeBlockRange', () => {
  it('describes a range of paragraphs', () => {
    expect(describeBlockRange('B12', 'B18')).toBe('paragraphs 12 to 18')
  })

  it('describes a single paragraph', () => {
    expect(describeBlockRange('B5', 'B5')).toBe('paragraph 5')
  })

  it('falls back to raw ids when numbers cannot be parsed', () => {
    expect(describeBlockRange('start', 'end')).toBe('blocks start to end')
  })
})

describe('describeFailedChunk', () => {
  it('combines the range and a human reason', () => {
    expect(describeFailedChunk(failedChunk)).toBe(
      'Paragraphs 12 to 18: The model quota was exceeded.',
    )
  })

  it('has a label for every failure reason', () => {
    Object.values(FailureReason).forEach((reason) => {
      expect(FAILURE_REASON_LABELS[reason].length).toBeGreaterThan(0)
    })
  })
})
