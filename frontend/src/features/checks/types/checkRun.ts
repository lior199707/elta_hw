import type { z } from 'zod'

import type {
  checkResultSchema,
  checkRunSchema,
  checkRunSummarySchema,
} from '../schemas/checkRun.schema'
import type { RuleOutcome } from './checkEnums'
import type { BlockLocation } from '../utils/describeBlockLocation'

export type CheckRun = z.infer<typeof checkRunSchema>
export type CheckResult = z.infer<typeof checkResultSchema>
export type CheckRunSummary = z.infer<typeof checkRunSummarySchema>
export type ResultRule = CheckResult['rules'][number]
export type Violation = CheckResult['violations'][number]
export type Block = CheckResult['context_blocks'][number]
export type FailedChunk = CheckResult['failed_chunks'][number]

export interface ViolationView extends Violation {
  block: Block
  ruleTitle: string
  location: BlockLocation
}

export interface RuleGroup {
  rule: ResultRule
  violations: ViolationView[]
  outcome: RuleOutcome
}

export interface SelectableRule {
  id: number
  title: string
  text: string
}

export interface RunCheckPayload {
  file: File
  ruleIds: number[]
}
