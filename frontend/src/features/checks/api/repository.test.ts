import { afterEach, describe, expect, it, vi } from 'vitest'

import { makeCheckRun } from '../utils/checkRunFixtures'
import { buildCheckFormData, deleteCheck, getCheck, listChecks, runCheck } from './repository'

function mockFetch(response: Response) {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('buildCheckFormData', () => {
  it('appends the file and one rule_ids field per rule', () => {
    const file = new File(['hello'], 'a.txt')

    const form = buildCheckFormData({ file, ruleIds: [1, 5] })

    expect((form.get('file') as File).name).toBe('a.txt')
    expect(form.getAll('rule_ids')).toEqual(['1', '5'])
  })
})

describe('checks repository', () => {
  it('posts multipart form data without a manual content type', async () => {
    const fetchMock = mockFetch(Response.json(makeCheckRun(), { status: 201 }))

    const run = await runCheck({ file: new File(['x'], 'a.txt'), ruleIds: [2] })

    const [url, init] = fetchMock.mock.calls[0] ?? []
    expect(url).toBe('/api/checks')
    expect(init?.method).toBe('POST')
    expect(init?.body).toBeInstanceOf(FormData)
    expect(init?.headers).toBeUndefined()
    expect(run.id).toBe(42)
  })

  it('surfaces the API message when the check fails', async () => {
    mockFetch(Response.json({ detail: 'Unsupported file type' }, { status: 415 }))

    await expect(runCheck({ file: new File(['x'], 'a.txt'), ruleIds: [1] })).rejects.toThrow(
      'Unsupported file type',
    )
  })

  it('lists with default pagination', async () => {
    const fetchMock = mockFetch(Response.json([]))

    await expect(listChecks()).resolves.toEqual([])
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/checks?limit=50&offset=0')
  })

  it('gets one run and validates it', async () => {
    const fetchMock = mockFetch(Response.json(makeCheckRun()))

    const run = await getCheck(42)

    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/checks/42')
    expect(run.result.violations).toHaveLength(3)
  })

  it('rejects an inconsistent run', async () => {
    mockFetch(Response.json({ ...makeCheckRun(), result: { nope: true } }))

    await expect(getCheck(42)).rejects.toThrow('unexpected response')
  })

  it('deletes a run', async () => {
    const fetchMock = mockFetch(new Response(null, { status: 204 }))

    await deleteCheck(42)

    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/checks/42')
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe('DELETE')
  })
})
