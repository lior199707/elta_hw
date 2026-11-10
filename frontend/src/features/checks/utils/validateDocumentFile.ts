import { documentFileSchema } from '../schemas/documentFile.schema'

export function validateDocumentFile(file: File): string | null {
  const result = documentFileSchema.safeParse(file)
  return result.success ? null : (result.error.issues[0]?.message ?? 'Invalid file.')
}
