import { describe, expect, it } from 'vitest'

import { makeCheckRun } from '../utils/checkRunFixtures'
import { checkRunSchema, checkRunSummaryListSchema } from './checkRun.schema'

describe('checkRunSchema', () => {
  it('accepts a valid run', () => {
    expect(checkRunSchema.safeParse(makeCheckRun()).success).toBe(true)
  })

  it('accepts a run without violations', () => {
    const run = makeCheckRun({ violations: [], context_blocks: [] })

    expect(checkRunSchema.safeParse(run).success).toBe(true)
  })

  it('rejects an unknown status', () => {
    const run = { ...makeCheckRun(), result: { ...makeCheckRun().result, status: 'weird' } }

    expect(checkRunSchema.safeParse(run).success).toBe(false)
  })

  it('rejects a violation that points to a missing block', () => {
    const run = makeCheckRun({ context_blocks: [] })

    expect(checkRunSchema.safeParse(run).success).toBe(false)
  })

  it('rejects a violation whose offsets exceed the block text', () => {
    const base = makeCheckRun()
    const [first, ...rest] = base.result.violations
    if (!first) {
      throw new Error('fixture must contain violations')
    }
    const run = makeCheckRun({ violations: [{ ...first, end: 9999 }, ...rest] })

    expect(checkRunSchema.safeParse(run).success).toBe(false)
  })

  it('rejects a violation for a rule missing from the snapshot', () => {
    const base = makeCheckRun()
    const run = makeCheckRun({ rules: base.result.rules.filter((rule) => rule.rule_id !== 'R1') })

    expect(checkRunSchema.safeParse(run).success).toBe(false)
  })
})

describe('checkRunSummaryListSchema', () => {
  it('accepts summaries and an empty list', () => {
    const summary = {
      id: 1,
      created_at: '2026-11-10T18:40:24Z',
      document_name: 'a.txt',
      status: 'partial',
      violation_count: 2,
      models_used: ['m'],
    }

    expect(checkRunSummaryListSchema.safeParse([summary]).success).toBe(true)
    expect(checkRunSummaryListSchema.safeParse([]).success).toBe(true)
  })

  it('rejects a negative-type mismatch', () => {
    expect(checkRunSummaryListSchema.safeParse([{ id: 'x' }]).success).toBe(false)
  })
})

describe('checkRunSchema legacy payloads', () => {
  it('accepts history saved without the location and fallback fields', () => {
    const run = makeCheckRun()
    const legacyBlocks = run.result.context_blocks.map((block) => ({
      block_id: block.block_id,
      index: block.index,
      kind: block.kind,
      text: block.text,
      heading_path: block.heading_path,
    }))
    const legacy = {
      ...run,
      result: {
        ...run.result,
        fallback_chunk_count: undefined,
        has_page_layout: undefined,
        context_blocks: legacyBlocks,
      },
    }

    expect(checkRunSchema.safeParse(legacy).success).toBe(true)
  })

  it('accepts explicit nulls for the new fields', () => {
    const run = makeCheckRun({ fallback_chunk_count: null })

    expect(checkRunSchema.safeParse(run).success).toBe(true)
  })
})
