import { describe, expect, it } from 'vitest'

import { BlockKind } from '../types/checkEnums'
import type { Block } from '../types/checkRun'
import { describeBlockLocation, describeLocationNote } from './describeBlockLocation'

const BLOCK_COUNT = 321

const base: Block = {
  block_id: 'B12',
  index: 12,
  kind: BlockKind.Paragraph,
  text: 'x',
  heading_path: ['23 Maintenance procedure 23'],
  page: null,
  section_position: 5,
  table_number: null,
  table_row: null,
}

function locate(overrides: Partial<Block>) {
  return describeBlockLocation({ ...base, ...overrides }, BLOCK_COUNT)
}

function chips(overrides: Partial<Block>) {
  return locate(overrides).parts.map((part) => [part.label, part.value])
}

describe('describeBlockLocation', () => {
  it('does not repeat the file name, which the result summary already shows', () => {
    expect(locate({})).not.toHaveProperty('file')
  })

  it('describes a paragraph within a section', () => {
    expect(chips({})).toEqual([
      ['Section', '23 Maintenance procedure 23'],
      ['Paragraph', '5 in section'],
    ])
  })

  it('puts the page first when it is a number', () => {
    expect(chips({ page: 2 })).toEqual([
      ['Page', '2'],
      ['Section', '23 Maintenance procedure 23'],
      ['Paragraph', '5 in section'],
    ])
  })

  it('omits the page when it is null or missing', () => {
    expect(chips({ page: null }).some(([label]) => label === 'Page')).toBe(false)
    expect(chips({ page: undefined }).some(([label]) => label === 'Page')).toBe(false)
  })

  it('joins a nested heading path with " > " and keeps the full text in the title', () => {
    const section = locate({ heading_path: ['Overview', 'Specs'] }).parts.find(
      (part) => part.label === 'Section',
    )

    expect(section).toEqual({
      label: 'Section',
      value: 'Overview > Specs',
      title: 'Overview > Specs',
    })
  })

  it('describes a list item within a section', () => {
    expect(chips({ kind: BlockKind.ListItem, section_position: 2 })).toContainEqual([
      'List item',
      '2 in section',
    ])
  })

  it('describes a table row with separate Table and Row chips', () => {
    expect(
      chips({ kind: BlockKind.TableRow, section_position: null, table_number: 1, table_row: 61 }),
    ).toEqual([
      ['Section', '23 Maintenance procedure 23'],
      ['Table', '1'],
      ['Row', '61'],
    ])
  })

  it('describes a TXT paragraph without a section or any total', () => {
    const location = locate({ heading_path: [], section_position: 7 })

    expect(location.parts).toEqual([{ label: 'Paragraph', value: '7' }])
  })

  it('describes headings, page headers and page footers', () => {
    expect(chips({ kind: BlockKind.Heading, section_position: null })).toContainEqual([
      'Type',
      'Heading',
    ])
    expect(chips({ kind: BlockKind.Header, section_position: null })).toContainEqual([
      'Location',
      'Page header',
    ])
    expect(chips({ kind: BlockKind.Footer, section_position: null })).toContainEqual([
      'Location',
      'Page footer',
    ])
  })

  it('falls back to a labeled block position when the section position is missing', () => {
    const fallback = locate({ section_position: null }).parts.at(-1)

    expect(fallback).toEqual({
      label: 'Block',
      value: '12 of 321',
      title: 'Position in the extracted text',
    })
  })

  it('falls back when table numbers are missing or the fields are absent (legacy history)', () => {
    const legacy: Block = {
      block_id: 'B182',
      index: 182,
      kind: BlockKind.TableRow,
      text: 'x',
      heading_path: [],
    }

    expect(describeBlockLocation(legacy, BLOCK_COUNT).parts).toEqual([
      { label: 'Block', value: '182 of 321', title: 'Position in the extracted text' },
    ])
  })
})

describe('describeLocationNote', () => {
  const withPage = { ...base, page: 3 }

  it('uses the Word-layout note when the document has a saved page layout', () => {
    expect(describeLocationNote(true, [base])).toBe(
      'Page numbers are taken from the layout Microsoft Word saved in the file and can differ if the document is opened with other fonts or settings.',
    )
  })

  it('explains that the file has no saved layout when it has none', () => {
    expect(describeLocationNote(false, [base])).toBe(
      'Page numbers are not shown because this file has no saved page layout (it was not last saved by Microsoft Word). Locations use section, paragraph and table row.',
    )
  })

  it('falls back to the blocks for runs saved before the layout flag existed', () => {
    expect(describeLocationNote(null, [withPage])).toBe(
      'Page numbers are taken from the layout Microsoft Word saved in the file and can differ if the document is opened with other fonts or settings.',
    )
    expect(describeLocationNote(undefined, [withPage])).toBe(
      'Page numbers are taken from the layout Microsoft Word saved in the file and can differ if the document is opened with other fonts or settings.',
    )
  })

  it('does not blame the file for missing pages in runs saved before page support', () => {
    const note = describeLocationNote(undefined, [base])

    expect(note).toBe(
      'Page numbers are not available for this run because it was saved before page support was added. Locations use section, paragraph and table row.',
    )
    expect(describeLocationNote(null, [])).toBe(note)
  })
})
