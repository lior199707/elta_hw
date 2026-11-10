import {
  BlockKind,
  CheckStatus,
  DocumentFormat,
  FailureReason,
  Severity,
} from '../types/checkEnums'
import type { Block, CheckRun, FailedChunk, Violation } from '../types/checkRun'

export const SPEED_BLOCK_TEXT = 'The drone flies at 120 km/h over Tel Aviv.'
export const CONTACT_BLOCK_TEXT = 'Contact John Smith for details.'

function locate(text: string, quote: string) {
  const start = text.indexOf(quote)
  if (start < 0) {
    throw new Error(`Fixture quote not found: ${quote}`)
  }
  return { quote, start, end: start + quote.length }
}

const speedBlock: Block = {
  block_id: 'B3',
  index: 3,
  kind: BlockKind.Paragraph,
  text: SPEED_BLOCK_TEXT,
  heading_path: ['Overview', 'Specifications'],
  section_position: 4,
  table_number: null,
  table_row: null,
}

const contactBlock: Block = {
  block_id: 'B7',
  index: 7,
  kind: BlockKind.TableRow,
  text: CONTACT_BLOCK_TEXT,
  heading_path: [],
  section_position: null,
  table_number: 1,
  table_row: 3,
}

const violations: Violation[] = [
  {
    rule_id: 'R2',
    block_id: 'B7',
    ...locate(CONTACT_BLOCK_TEXT, 'John Smith'),
    explanation: 'Names a person.',
    severity: Severity.Low,
  },
  {
    rule_id: 'R3',
    block_id: 'B3',
    ...locate(SPEED_BLOCK_TEXT, 'Tel Aviv'),
    explanation: 'Discloses a location.',
    severity: Severity.Medium,
  },
  {
    rule_id: 'R1',
    block_id: 'B3',
    ...locate(SPEED_BLOCK_TEXT, '120 km/h'),
    explanation: 'States a speed figure.',
    severity: Severity.High,
  },
]

export const failedChunk: FailedChunk = {
  chunk_id: 'C2',
  first_block_id: 'B12',
  last_block_id: 'B18',
  reason: FailureReason.QuotaExceeded,
  message: 'quota',
}

export function makeCheckRun(overrides: Partial<CheckRun['result']> = {}): CheckRun {
  return {
    id: 42,
    created_at: '2026-11-10T18:40:24Z',
    document_sha256: 'abc',
    document_size_bytes: 2048,
    result: {
      document_name: 'spec.docx',
      document_format: DocumentFormat.Docx,
      status: CheckStatus.Completed,
      rules: [
        { rule_id: 'R1', title: 'No performance figures', text: 'No speeds.' },
        { rule_id: 'R2', title: 'No personal names', text: 'No names.' },
        { rule_id: 'R3', title: 'No exact locations', text: 'No places.' },
        { rule_id: 'R4', title: 'No profanity', text: 'Be polite.' },
      ],
      violations,
      context_blocks: [speedBlock, contactBlock],
      block_count: 20,
      chunks_total: 2,
      failed_chunks: [],
      dropped_count: 0,
      models_used: ['gemini-2.5-flash'],
      duration_ms: 12_500,
      has_page_layout: false,
      ...overrides,
    },
  }
}
