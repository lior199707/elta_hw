import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { BlockKind } from '../types/checkEnums'
import type { ViolationView } from '../types/checkRun'
import { makeCheckRun } from '../utils/checkRunFixtures'
import { describeBlockLocation } from '../utils/describeBlockLocation'
import { ViolationCard } from './ViolationCard'

function makeView(blockOverrides: Partial<ViolationView['block']> = {}): ViolationView {
  const { result } = makeCheckRun()
  const violation = result.violations[2]
  const block = result.context_blocks[0]
  if (!violation || !block) {
    throw new Error('fixture must contain a violation and a block')
  }
  const merged = { ...block, ...blockOverrides }
  return {
    ...violation,
    block: merged,
    ruleTitle: 'No performance figures',
    location: describeBlockLocation(merged, result.block_count),
  }
}

describe('ViolationCard location chips', () => {
  it('renders labelled chips as a description list without repeating the file', () => {
    render(<ViolationCard violation={makeView({ page: 2 })} showRuleTitle />)

    expect(screen.getByText('Page').nextElementSibling).toHaveTextContent('2')
    expect(screen.getByText('Paragraph').nextElementSibling).toHaveTextContent('4 in section')
    expect(screen.queryByText('File')).not.toBeInTheDocument()
    expect(screen.queryByText(/of 20/)).not.toBeInTheDocument()
  })

  it('puts the full section text in a title attribute', () => {
    render(<ViolationCard violation={makeView()} showRuleTitle />)

    expect(screen.getByTitle('Overview > Specifications')).toBeInTheDocument()
  })

  it('shows a labelled Block chip for legacy blocks', () => {
    const view = makeView({
      kind: BlockKind.TableRow,
      section_position: null,
      table_number: null,
      table_row: null,
    })

    render(<ViolationCard violation={view} showRuleTitle />)

    expect(screen.getByText('Block').nextElementSibling).toHaveTextContent('3 of 20')
    expect(screen.getByTitle('Position in the extracted text')).toBeInTheDocument()
  })
})

describe('ViolationCard header', () => {
  it('shows the rule title on its own line above the severity badge', () => {
    render(<ViolationCard violation={makeView()} showRuleTitle />)

    const title = screen.getByRole('heading', { name: 'No performance figures' })
    const severity = screen.getByText(/severity$/)
    expect(title.compareDocumentPosition(severity) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(title.parentElement).not.toBe(severity.parentElement)
  })

  it('renders the severity badge in the larger size than the location chips', () => {
    render(<ViolationCard violation={makeView({ page: 2 })} showRuleTitle={false} />)

    expect(screen.getByText(/severity$/)).toHaveAttribute('data-size', 'md')
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })
})
