export const CheckStatus = {
  Completed: 'completed',
  Partial: 'partial',
  Failed: 'failed',
} as const
export type CheckStatus = (typeof CheckStatus)[keyof typeof CheckStatus]

export const DocumentFormat = { Docx: '.docx', Txt: '.txt' } as const
export type DocumentFormat = (typeof DocumentFormat)[keyof typeof DocumentFormat]

export const Severity = { High: 'high', Medium: 'medium', Low: 'low' } as const
export type Severity = (typeof Severity)[keyof typeof Severity]

export const BlockKind = {
  Heading: 'heading',
  Paragraph: 'paragraph',
  ListItem: 'list_item',
  TableRow: 'table_row',
  Header: 'header',
  Footer: 'footer',
} as const
export type BlockKind = (typeof BlockKind)[keyof typeof BlockKind]

export const FailureReason = {
  QuotaExceeded: 'quota_exceeded',
  Overloaded: 'overloaded',
  Timeout: 'timeout',
  Blocked: 'blocked',
  InvalidResponse: 'invalid_response',
  Unavailable: 'unavailable',
} as const
export type FailureReason = (typeof FailureReason)[keyof typeof FailureReason]

export const ResultViewMode = { ByRule: 'rule', Position: 'position' } as const
export type ResultViewMode = (typeof ResultViewMode)[keyof typeof ResultViewMode]

export const RuleOutcome = {
  Violated: 'violated',
  Passed: 'passed',
  PassedPartial: 'passed_partial',
  NotChecked: 'not_checked',
} as const
export type RuleOutcome = (typeof RuleOutcome)[keyof typeof RuleOutcome]
