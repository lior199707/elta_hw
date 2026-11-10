const UNKNOWN_ERROR_MESSAGE = 'Something went wrong. Please try again.'

export function getErrorMessage(error: unknown): string {
  return error instanceof Error && error.message ? error.message : UNKNOWN_ERROR_MESSAGE
}
