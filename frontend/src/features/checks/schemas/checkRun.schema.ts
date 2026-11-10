import { z } from 'zod'

import {
  BlockKind,
  CheckStatus,
  DocumentFormat,
  FailureReason,
  Severity,
} from '../types/checkEnums'

const ruleSnapshotSchema = z.object({
  rule_id: z.string(),
  title: z.string(),
  text: z.string(),
})

const violationSchema = z.object({
  rule_id: z.string(),
  block_id: z.string(),
  quote: z.string(),
  start: z.number().int().nonnegative(),
  end: z.number().int().nonnegative(),
  explanation: z.string(),
  severity: z.enum(Severity),
})

const blockSchema = z.object({
  block_id: z.string(),
  index: z.number().int(),
  kind: z.enum(BlockKind),
  text: z.string(),
  heading_path: z.array(z.string()),
  page: z.number().int().nullish(),
  section_position: z.number().int().nullish(),
  table_number: z.number().int().nullish(),
  table_row: z.number().int().nullish(),
})

const failedChunkSchema = z.object({
  chunk_id: z.string(),
  first_block_id: z.string(),
  last_block_id: z.string(),
  reason: z.enum(FailureReason),
  message: z.string(),
})

export const checkResultSchema = z
  .object({
    document_name: z.string(),
    document_format: z.enum(DocumentFormat),
    status: z.enum(CheckStatus),
    rules: z.array(ruleSnapshotSchema),
    violations: z.array(violationSchema),
    context_blocks: z.array(blockSchema),
    block_count: z.number().int(),
    chunks_total: z.number().int(),
    failed_chunks: z.array(failedChunkSchema),
    dropped_count: z.number().int(),
    models_used: z.array(z.string()),
    duration_ms: z.number(),
    fallback_chunk_count: z.number().int().nullish(),
    has_page_layout: z.boolean().nullish(),
  })
  .superRefine((result, context) => {
    const ruleIds = new Set(result.rules.map((rule) => rule.rule_id))
    const blocksById = new Map(result.context_blocks.map((block) => [block.block_id, block]))
    result.violations.forEach((violation, index) => {
      const block = blocksById.get(violation.block_id)
      if (!block) {
        context.addIssue({
          code: 'custom',
          message: `Violation references unknown block ${violation.block_id}`,
          path: ['violations', index, 'block_id'],
        })
      } else if (violation.start > violation.end || violation.end > block.text.length) {
        context.addIssue({
          code: 'custom',
          message: 'Violation offsets are outside the block text',
          path: ['violations', index, 'start'],
        })
      }
      if (!ruleIds.has(violation.rule_id)) {
        context.addIssue({
          code: 'custom',
          message: `Violation references unknown rule ${violation.rule_id}`,
          path: ['violations', index, 'rule_id'],
        })
      }
    })
  })

export const checkRunSchema = z.object({
  id: z.number().int(),
  created_at: z.string(),
  document_sha256: z.string(),
  document_size_bytes: z.number().int(),
  result: checkResultSchema,
})

export const checkRunSummarySchema = z.object({
  id: z.number().int(),
  created_at: z.string(),
  document_name: z.string(),
  status: z.enum(CheckStatus),
  violation_count: z.number().int(),
  models_used: z.array(z.string()),
})

export const checkRunSummaryListSchema = z.array(checkRunSummarySchema)
