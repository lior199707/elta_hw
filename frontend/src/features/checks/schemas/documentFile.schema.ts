import { z } from 'zod'

const BYTES_PER_MB = 1024 * 1024

export const MAX_DOCUMENT_SIZE_MB = 20
export const MAX_DOCUMENT_SIZE_BYTES = MAX_DOCUMENT_SIZE_MB * BYTES_PER_MB
export const ALLOWED_DOCUMENT_EXTENSIONS = ['.docx', '.txt'] as const
export const DOCUMENT_ACCEPT_ATTRIBUTE = ALLOWED_DOCUMENT_EXTENSIONS.join(',')

function hasAllowedExtension(name: string): boolean {
  const lowerName = name.toLowerCase()
  return ALLOWED_DOCUMENT_EXTENSIONS.some((extension) => lowerName.endsWith(extension))
}

export const documentFileSchema = z
  .instanceof(File)
  .refine((file) => hasAllowedExtension(file.name), {
    message: `Unsupported file type. Upload a ${ALLOWED_DOCUMENT_EXTENSIONS.join(' or ')} file.`,
  })
  .refine((file) => file.size > 0, { message: 'The file is empty.' })
  .refine((file) => file.size <= MAX_DOCUMENT_SIZE_BYTES, {
    message: `The file is too large. The maximum size is ${MAX_DOCUMENT_SIZE_MB} MB.`,
  })
