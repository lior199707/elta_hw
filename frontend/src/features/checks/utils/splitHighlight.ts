export interface HighlightedText {
  before: string
  match: string
  after: string
}

export function splitHighlight(text: string, start: number, end: number): HighlightedText {
  if (start < 0 || start > end || end > text.length) {
    throw new Error(`Highlight range ${start}-${end} is outside text of length ${text.length}`)
  }
  return { before: text.slice(0, start), match: text.slice(start, end), after: text.slice(end) }
}
