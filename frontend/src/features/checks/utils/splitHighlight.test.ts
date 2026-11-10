import { describe, expect, it } from 'vitest'

import { splitHighlight } from './splitHighlight'

describe('splitHighlight', () => {
  it('splits text around the range', () => {
    expect(splitHighlight('hello big world', 6, 9)).toEqual({
      before: 'hello ',
      match: 'big',
      after: ' world',
    })
  })

  it('handles ranges at the start and end of the text', () => {
    expect(splitHighlight('abc', 0, 3)).toEqual({ before: '', match: 'abc', after: '' })
  })

  it('handles an empty range', () => {
    expect(splitHighlight('abc', 1, 1)).toEqual({ before: 'a', match: '', after: 'bc' })
  })

  it('throws on an invalid range', () => {
    expect(() => splitHighlight('abc', 2, 10)).toThrow('outside text')
    expect(() => splitHighlight('abc', 2, 1)).toThrow('outside text')
  })
})
