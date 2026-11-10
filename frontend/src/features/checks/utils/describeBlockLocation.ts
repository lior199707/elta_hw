import { BlockKind } from '../types/checkEnums'
import type { Block } from '../types/checkRun'

export const HEADING_PATH_SEPARATOR = ' > '
const IN_SECTION_SUFFIX = ' in section'
const FALLBACK_TITLE = 'Position in the extracted text'

export interface LocationPart {
  label: string
  value: string
  title?: string
}

export interface BlockLocation {
  parts: LocationPart[]
}

function fallbackPart(block: Block, blockCount: number): LocationPart {
  return { label: 'Block', value: `${block.index} of ${blockCount}`, title: FALLBACK_TITLE }
}

function describePosition(block: Block, blockCount: number): LocationPart[] {
  const suffix = block.heading_path.length > 0 ? IN_SECTION_SUFFIX : ''
  switch (block.kind) {
    case BlockKind.Paragraph:
      return block.section_position == null
        ? [fallbackPart(block, blockCount)]
        : [{ label: 'Paragraph', value: `${block.section_position}${suffix}` }]
    case BlockKind.ListItem:
      return block.section_position == null
        ? [fallbackPart(block, blockCount)]
        : [{ label: 'List item', value: `${block.section_position}${suffix}` }]
    case BlockKind.TableRow:
      return block.table_number == null || block.table_row == null
        ? [fallbackPart(block, blockCount)]
        : [
            { label: 'Table', value: String(block.table_number) },
            { label: 'Row', value: String(block.table_row) },
          ]
    case BlockKind.Heading:
      return [{ label: 'Type', value: 'Heading' }]
    case BlockKind.Header:
      return [{ label: 'Location', value: 'Page header' }]
    case BlockKind.Footer:
      return [{ label: 'Location', value: 'Page footer' }]
  }
}

export function describeBlockLocation(block: Block, blockCount: number): BlockLocation {
  const parts: LocationPart[] = []
  if (block.page != null) {
    parts.push({ label: 'Page', value: String(block.page) })
  }
  if (block.heading_path.length > 0) {
    const section = block.heading_path.join(HEADING_PATH_SEPARATOR)
    parts.push({ label: 'Section', value: section, title: section })
  }
  parts.push(...describePosition(block, blockCount))
  return { parts }
}

const NOTE_WITH_PAGES =
  'Page numbers are taken from the layout Microsoft Word saved in the file and can differ if the document is opened with other fonts or settings.'
const NOTE_WITHOUT_PAGES =
  'Page numbers are not shown because this file has no saved page layout (it was not last saved by Microsoft Word). Locations use section, paragraph and table row.'

const NOTE_LEGACY_RUN =
  'Page numbers are not available for this run because it was saved before page support was added. Locations use section, paragraph and table row.'

export function describeLocationNote(
  hasPageLayout: boolean | null | undefined,
  blocks: readonly Block[],
): string {
  if (hasPageLayout != null) {
    return hasPageLayout ? NOTE_WITH_PAGES : NOTE_WITHOUT_PAGES
  }
  // Runs stored before the layout flag existed: blocks may still carry pages.
  return blocks.some((block) => block.page != null) ? NOTE_WITH_PAGES : NOTE_LEGACY_RUN
}
