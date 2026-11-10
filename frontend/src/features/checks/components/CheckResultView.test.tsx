import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { renderWithProviders } from '@/lib/test-utils/renderWithProviders'

import { CheckStatus } from '../types/checkEnums'
import { failedChunk, makeCheckRun } from '../utils/checkRunFixtures'
import { CheckResultView } from './CheckResultView'

describe('CheckResultView', () => {
  it('shows the summary and groups violations by rule with counts', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    expect(screen.getByRole('heading', { level: 1, name: 'spec.docx' })).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('gemini-2.5-flash')).toBeInTheDocument()
    const group = screen.getByRole('region', { name: 'No performance figures' })
    expect(within(group).getByText('1 violation')).toBeInTheDocument()
  })

  it('shows rules without violations as passed', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    const group = screen.getByRole('region', { name: 'No profanity' })

    expect(within(group).getByText('Passed')).toBeInTheDocument()
  })

  it('highlights the quote with a mark element using the offsets', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    const marks = screen.getAllByText('120 km/h')

    expect(marks[0]?.tagName).toBe('MARK')
  })

  it('shows explicit labeled locations and the page number note', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    expect(screen.getAllByText('Overview > Specifications')).toHaveLength(2)
    expect(screen.getAllByText('Section')).toHaveLength(2)
    expect(screen.getAllByText('4 in section')).toHaveLength(2)
    expect(screen.queryByText('File')).not.toBeInTheDocument()
    expect(screen.getByText('Table').nextElementSibling).toHaveTextContent('1')
    expect(screen.getByText('Row').nextElementSibling).toHaveTextContent('3')
    expect(screen.getAllByRole('term').length).toBeGreaterThan(0)
    expect(
      screen.getByText(/Page numbers are not shown because this file has no saved page layout/),
    ).toBeInTheDocument()
  })

  it('hides the rule title on cards in By rule view and shows it in Position in document', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    expect(screen.queryAllByRole('heading', { level: 4 })).toHaveLength(0)
    await userEvent.click(screen.getByRole('radio', { name: 'Position in document' }))

    expect(screen.getAllByRole('heading', { level: 4 })).toHaveLength(3)
  })

  it('shows an amber fallback notice when fallback chunks were used', () => {
    renderWithProviders(
      <CheckResultView run={makeCheckRun({ fallback_chunk_count: 1, chunks_total: 2 })} />,
    )

    expect(screen.getByRole('status')).toHaveTextContent(
      '1 of 2 chunks were checked by the fallback model because the primary model was unavailable.',
    )
  })

  it.each([0, null, undefined])('hides the fallback notice when the count is %s', (count) => {
    renderWithProviders(<CheckResultView run={makeCheckRun({ fallback_chunk_count: count })} />)

    expect(screen.queryByText(/fallback model/)).not.toBeInTheDocument()
  })

  it('switches to document order', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    await userEvent.click(screen.getByRole('radio', { name: 'Position in document' }))

    const list = screen.getByRole('list', { name: 'Violations by position in document' })
    const titles = within(list)
      .getAllByRole('heading', { level: 4 })
      .map((heading) => heading.textContent)
    expect(titles).toEqual(['No performance figures', 'No exact locations', 'No personal names'])
    expect(screen.queryByRole('region', { name: 'No profanity' })).not.toBeInTheDocument()
  })

  it('warns that part of the document was not checked on a partial run', () => {
    renderWithProviders(
      <CheckResultView
        run={makeCheckRun({ status: CheckStatus.Partial, failed_chunks: [failedChunk] })}
      />,
    )

    const banner = screen.getByRole('alert')
    expect(banner).toHaveTextContent('Part of the document was NOT checked')
    expect(banner).toHaveTextContent('Paragraphs 12 to 18')
    expect(screen.queryByText('Passed')).not.toBeInTheDocument()
  })

  it('never implies a clean document when the run failed', () => {
    renderWithProviders(
      <CheckResultView
        run={makeCheckRun({
          status: CheckStatus.Failed,
          violations: [],
          context_blocks: [],
          failed_chunks: [failedChunk],
        })}
      />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('The document was NOT checked')
    expect(screen.queryByText('Passed')).not.toBeInTheDocument()
    expect(screen.queryByText(/No violations were found/)).not.toBeInTheDocument()
    expect(screen.getAllByText('Not checked')).toHaveLength(4)
  })

  it('shows a note when model findings were dropped', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun({ dropped_count: 3 })} />)

    expect(screen.getByRole('note')).toHaveTextContent(
      '3 model findings were discarded because their quotes were not found in the document.',
    )
  })

  it('shows an all-clear message when a completed run has no violations', () => {
    renderWithProviders(
      <CheckResultView run={makeCheckRun({ violations: [], context_blocks: [] })} />,
    )

    expect(screen.getByText(/No violations were found/)).toBeInTheDocument()
  })
})

describe('CheckResultView page numbers', () => {
  it('shows the page in locations and the Word layout note when blocks have pages', () => {
    const base = makeCheckRun()
    const run = makeCheckRun({
      has_page_layout: true,
      context_blocks: base.result.context_blocks.map((block) => ({ ...block, page: 14 })),
    })

    renderWithProviders(<CheckResultView run={run} />)

    expect(screen.getAllByText('Page')).toHaveLength(3)
    expect(screen.getAllByText('14')).toHaveLength(3)
    expect(screen.getByText(/taken from the layout Microsoft Word saved/)).toBeInTheDocument()
  })
})

describe('CheckResultView sort control', () => {
  it('is a labelled radio group defaulting to Rule', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    expect(screen.getByRole('group', { name: 'Sort violations by' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Rule' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Position in document' })).not.toBeChecked()
  })

  it('switches between grouped and flat views', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    await userEvent.click(screen.getByRole('radio', { name: 'Position in document' }))
    expect(screen.getByRole('radio', { name: 'Position in document' })).toBeChecked()
    expect(screen.queryByRole('region', { name: 'No profanity' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('radio', { name: 'Rule' }))

    expect(screen.getByRole('region', { name: 'No profanity' })).toBeInTheDocument()
  })

  it('reads the sort mode from the URL', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />, ['/history/42?sort=position'])

    expect(screen.getByRole('radio', { name: 'Position in document' })).toBeChecked()
  })

  it('ignores an invalid sort value in the URL', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />, ['/history/42?sort=nope'])

    expect(screen.getByRole('radio', { name: 'Rule' })).toBeChecked()
  })
})

describe('CheckResultView filters', () => {
  it('shows per-rule and per-severity counts and an unfiltered summary', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    expect(screen.getByRole('checkbox', { name: 'No performance figures (1)' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'No profanity (0)' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'High (1)' })).toBeChecked()
    expect(screen.getByText('Showing 3 of 3 violations')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Clear filters' })).toBeDisabled()
  })

  it('hides an unchecked rule including its passed group and updates the summary', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    await userEvent.click(screen.getByRole('checkbox', { name: 'No performance figures (1)' }))
    await userEvent.click(screen.getByRole('checkbox', { name: 'No profanity (0)' }))

    expect(screen.queryByRole('region', { name: 'No performance figures' })).not.toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'No profanity' })).not.toBeInTheDocument()
    expect(screen.getByText('Showing 2 of 3 violations')).toBeInTheDocument()
  })

  it('supports the None and All shortcuts and the empty state', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    await userEvent.click(screen.getByRole('button', { name: 'None' }))
    expect(screen.getByText('No violations match the current filters')).toBeInTheDocument()
    expect(screen.getByText('Showing 0 of 3 violations')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'All' }))

    expect(screen.getByText('Showing 3 of 3 violations')).toBeInTheDocument()
  })

  it('filters by severity and by search text', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    await userEvent.click(screen.getByRole('checkbox', { name: 'High (1)' }))
    expect(screen.getByText('Showing 2 of 3 violations')).toBeInTheDocument()
    await userEvent.type(screen.getByRole('searchbox', { name: 'Search violations' }), 'TEL')

    expect(screen.getByText('Showing 1 of 3 violations')).toBeInTheDocument()
  })

  it('clears filters from the empty state', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    await userEvent.type(screen.getByRole('searchbox', { name: 'Search violations' }), 'zzzz')
    expect(screen.getByText('No violations match the current filters')).toBeInTheDocument()
    const clearButtons = screen.getAllByRole('button', { name: 'Clear filters' })
    await userEvent.click(clearButtons[clearButtons.length - 1] as HTMLElement)

    expect(screen.getByText('Showing 3 of 3 violations')).toBeInTheDocument()
    expect(screen.getByRole('searchbox', { name: 'Search violations' })).toHaveValue('')
  })

  it('applies filters from the URL and ignores invalid values', () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />, [
      '/history/42?rules=R1,BOGUS&severity=high,extreme&q=km&sort=position',
    ])

    expect(screen.getByText('Showing 1 of 3 violations')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'No personal names (1)' })).not.toBeChecked()
  })

  it('keeps the summary bar violation count unfiltered', async () => {
    renderWithProviders(<CheckResultView run={makeCheckRun()} />)

    await userEvent.click(screen.getByRole('button', { name: 'None' }))

    expect(screen.getByText('Violations').nextElementSibling).toHaveTextContent('3')
  })

  it('hides filters when the run has no violations', () => {
    renderWithProviders(
      <CheckResultView run={makeCheckRun({ violations: [], context_blocks: [] })} />,
    )

    expect(screen.queryByText(/Showing/)).not.toBeInTheDocument()
  })
})
