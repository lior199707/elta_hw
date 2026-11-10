import { describe, expect, it } from 'vitest'

import { MAX_DOCUMENT_SIZE_BYTES } from '../schemas/documentFile.schema'
import { validateDocumentFile } from './validateDocumentFile'

describe('validateDocumentFile', () => {
  it('accepts .docx and .txt files, case-insensitively', () => {
    expect(validateDocumentFile(new File(['x'], 'a.docx'))).toBeNull()
    expect(validateDocumentFile(new File(['x'], 'NOTES.TXT'))).toBeNull()
  })

  it('rejects other extensions', () => {
    expect(validateDocumentFile(new File(['x'], 'a.pdf'))).toContain('Unsupported file type')
  })

  it('rejects empty files', () => {
    expect(validateDocumentFile(new File([], 'a.txt'))).toBe('The file is empty.')
  })

  it('rejects files over 20 MB but accepts exactly 20 MB', () => {
    const atLimit = new File(['x'], 'a.txt')
    Object.defineProperty(atLimit, 'size', { value: MAX_DOCUMENT_SIZE_BYTES })
    const overLimit = new File(['x'], 'b.txt')
    Object.defineProperty(overLimit, 'size', { value: MAX_DOCUMENT_SIZE_BYTES + 1 })

    expect(validateDocumentFile(atLimit)).toBeNull()
    expect(validateDocumentFile(overLimit)).toContain('20 MB')
  })
})
