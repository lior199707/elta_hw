import { afterEach, describe, expect, it, vi } from 'vitest'

import { RuleActiveFilter } from '../types/rule'
import { createRule, deleteRule, listRules, updateRule } from './repository'

const rule = {
  id: 7,
  title: 'T',
  text: 'X',
  is_active: true,
  created_at: '2026-11-10T18:40:24Z',
  updated_at: '2026-11-10T18:40:24Z',
}

function mockFetch(response: Response) {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('rules repository', () => {
  it('lists all rules without a query string', async () => {
    const fetchMock = mockFetch(Response.json([rule]))

    const rules = await listRules(RuleActiveFilter.All)

    expect(rules).toEqual([rule])
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/rules')
  })

  it('lists only active rules with active=true', async () => {
    const fetchMock = mockFetch(Response.json([]))

    await listRules(RuleActiveFilter.Active)

    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/rules?active=true')
  })

  it('posts a new rule as JSON', async () => {
    const fetchMock = mockFetch(Response.json(rule, { status: 201 }))

    await createRule({ title: 'T', text: 'X', is_active: true })

    const init = fetchMock.mock.calls[0]?.[1]
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/rules')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(String(init?.body))).toEqual({ title: 'T', text: 'X', is_active: true })
  })

  it('patches a rule by id with a partial payload', async () => {
    const fetchMock = mockFetch(Response.json(rule))

    await updateRule(7, { is_active: false })

    const init = fetchMock.mock.calls[0]?.[1]
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/rules/7')
    expect(init?.method).toBe('PATCH')
    expect(init?.body).toBe('{"is_active":false}')
  })

  it('deletes a rule by id', async () => {
    const fetchMock = mockFetch(new Response(null, { status: 204 }))

    await deleteRule(7)

    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/rules/7')
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe('DELETE')
  })

  it('surfaces the API error message', async () => {
    mockFetch(Response.json({ detail: 'Rule not found' }, { status: 404 }))

    await expect(deleteRule(99)).rejects.toThrow('Rule not found')
  })

  it('rejects a malformed list response', async () => {
    mockFetch(Response.json([{ id: 'x' }]))

    await expect(listRules(RuleActiveFilter.All)).rejects.toThrow('unexpected response')
  })
})
