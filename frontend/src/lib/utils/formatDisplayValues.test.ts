import { describe, expect, it } from 'vitest'

import { formatDateTime, formatDuration, formatFileSize } from './formatDisplayValues'

describe('formatDuration', () => {
  it('formats milliseconds, seconds and minutes', () => {
    expect(formatDuration(250)).toBe('250 ms')
    expect(formatDuration(12_340)).toBe('12.3 s')
    expect(formatDuration(125_000)).toBe('2 min 5 s')
  })
})

describe('formatFileSize', () => {
  it('formats bytes, kilobytes and megabytes', () => {
    expect(formatFileSize(512)).toBe('512 B')
    expect(formatFileSize(2048)).toBe('2.0 KB')
    expect(formatFileSize(5 * 1024 * 1024)).toBe('5.0 MB')
    expect(formatFileSize(20 * 1024 * 1024)).toBe('20 MB')
  })
})

describe('formatDateTime', () => {
  it('formats a valid ISO date', () => {
    expect(formatDateTime('2026-11-10T18:40:24.234974Z')).toContain('2026')
  })

  it('throws on an invalid date', () => {
    expect(() => formatDateTime('not-a-date')).toThrow('Invalid ISO date')
  })
})
