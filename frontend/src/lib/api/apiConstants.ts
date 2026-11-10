export const API_BASE_URL = '/api'

export const HttpMethod = {
  Get: 'GET',
  Post: 'POST',
  Patch: 'PATCH',
  Delete: 'DELETE',
} as const
export type HttpMethod = (typeof HttpMethod)[keyof typeof HttpMethod]

export const ERROR_MESSAGES = {
  network: 'Could not reach the server. Check your connection and try again.',
  unexpectedResponse: 'The server returned an unexpected response.',
  requestFailed: 'The request failed',
} as const
