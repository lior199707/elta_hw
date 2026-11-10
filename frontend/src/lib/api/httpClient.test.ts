import { afterEach, describe, expect, it, vi } from 'vitest'
import { z } from 'zod'

import { ApiError } from './ApiError'
import { HttpMethod } from './apiConstants'
import { requestJson, requestVoid } from './httpClient'

const schema = z.object({ id: z.number() })

function mockFetch(response: Response | Error) {
  const fetchMock = vi.fn<typeof fetch>()
  if (response instanceof Error) {
    fetchMock.mockRejectedValue(response)
  } else {
    fetchMock.mockResolvedValue(response)
  }
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function jsonResponse(body: unknown, status: number) {
  return new Response(JSON.stringify(body), { status })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('requestJson', () => {
  it('returns validated data and sends JSON bodies', async () => {
    const fetchMock = mockFetch(jsonResponse({ id: 1 }, 200))

    const result = await requestJson('/rules', schema, {
      method: HttpMethod.Post,
      body: { json: { title: 'a' } },
    })

    expect(result).toEqual({ id: 1 })
    const [url, init] = fetchMock.mock.calls[0] ?? []
    expect(url).toBe('/api/rules')
    expect(init?.method).toBe('POST')
    expect(init?.body).toBe('{"title":"a"}')
  })

  it('uses a string detail as the error message', async () => {
    mockFetch(jsonResponse({ detail: 'Rule 9 not found' }, 404))

    await expect(requestJson('/rules/9', schema)).rejects.toMatchObject({
      message: 'Rule 9 not found',
      status: 404,
    })
  })

  it('joins array details from FastAPI validation errors', async () => {
    mockFetch(
      jsonResponse(
        {
          detail: [
            { loc: ['body', 'title'], msg: 'String should have at least 1 character', type: 'x' },
            { loc: ['body', 'text'], msg: 'Field required', type: 'y' },
          ],
        },
        422,
      ),
    )

    await expect(requestJson('/rules', schema)).rejects.toThrow(
      'title: String should have at least 1 character; text: Field required',
    )
  })

  it('falls back to a generic message for unparseable error bodies', async () => {
    mockFetch(new Response('<html>boom</html>', { status: 500 }))

    await expect(requestJson('/rules', schema)).rejects.toThrow('HTTP 500')
  })

  it('wraps network failures in an ApiError', async () => {
    mockFetch(new TypeError('Failed to fetch'))

    const error = await requestJson('/rules', schema).catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).message).toContain('Could not reach the server')
  })

  it('rejects responses that do not match the schema', async () => {
    mockFetch(jsonResponse({ id: 'nope' }, 200))

    await expect(requestJson('/rules', schema)).rejects.toThrow('unexpected response')
  })
})

describe('requestVoid', () => {
  it('resolves on 204', async () => {
    const fetchMock = mockFetch(new Response(null, { status: 204 }))

    await expect(requestVoid('/rules/1', { method: HttpMethod.Delete })).resolves.toBeUndefined()
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe('DELETE')
  })

  it('throws the API message on failure', async () => {
    mockFetch(jsonResponse({ detail: 'Not found' }, 404))

    await expect(requestVoid('/rules/1', { method: HttpMethod.Delete })).rejects.toThrow(
      'Not found',
    )
  })
})
