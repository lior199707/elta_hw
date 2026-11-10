import type { z } from 'zod'

import { API_BASE_URL, ERROR_MESSAGES, HttpMethod } from './apiConstants'
import { ApiError } from './ApiError'
import { parseErrorMessage } from './parseErrorMessage'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

type RequestBody = { json: unknown } | { form: FormData }

interface RequestOptions {
  method?: HttpMethod
  body?: RequestBody
  signal?: AbortSignal
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const { method = HttpMethod.Get, body, signal } = options
  const init: RequestInit = { method, signal }
  if (body && 'json' in body) {
    init.headers = JSON_HEADERS
    init.body = JSON.stringify(body.json)
  } else if (body) {
    init.body = body.form
  }
  try {
    return await fetch(`${API_BASE_URL}${path}`, init)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    throw new ApiError(ERROR_MESSAGES.network)
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return null
  }
}

async function ensureOk(response: Response): Promise<void> {
  if (response.ok) {
    return
  }
  throw new ApiError(parseErrorMessage(await readJson(response), response.status), response.status)
}

export async function requestJson<TSchema extends z.ZodType>(
  path: string,
  schema: TSchema,
  options: RequestOptions = {},
): Promise<z.infer<TSchema>> {
  const response = await send(path, options)
  await ensureOk(response)
  const parsed = schema.safeParse(await readJson(response))
  if (!parsed.success) {
    throw new ApiError(ERROR_MESSAGES.unexpectedResponse, response.status)
  }
  return parsed.data
}

export async function requestVoid(path: string, options: RequestOptions = {}): Promise<void> {
  const response = await send(path, options)
  await ensureOk(response)
}
