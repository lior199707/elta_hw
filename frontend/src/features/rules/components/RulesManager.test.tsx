import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/lib/test-utils/renderWithProviders'

import { RulesManager } from './RulesManager'

const rule = {
  id: 1,
  title: 'No names',
  text: 'Do not mention people.',
  is_active: true,
  created_at: '2026-11-10T18:40:24Z',
  updated_at: '2026-11-10T18:40:24Z',
}

function mockFetch(handler: (url: string, init?: RequestInit) => Response) {
  const fetchMock = vi.fn<typeof fetch>((input, init) =>
    Promise.resolve(handler(String(input), init)),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('RulesManager', () => {
  it('lists rules with an active toggle', async () => {
    mockFetch(() => Response.json([rule]))

    renderWithProviders(<RulesManager />)

    expect(await screen.findByText('No names')).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Active: No names' })).toBeChecked()
  })

  it('shows the empty state', async () => {
    mockFetch(() => Response.json([]))

    renderWithProviders(<RulesManager />)

    expect(await screen.findByText(/No rules yet/)).toBeInTheDocument()
  })

  it('shows an error with the API message', async () => {
    mockFetch(() => Response.json({ detail: 'Database down' }, { status: 500 }))

    renderWithProviders(<RulesManager />)

    expect(await screen.findByText(/Database down/)).toBeInTheDocument()
  })

  it('patches is_active when the toggle is clicked', async () => {
    const fetchMock = mockFetch((_url, init) =>
      init?.method === 'PATCH'
        ? Response.json({ ...rule, is_active: false })
        : Response.json([rule]),
    )

    renderWithProviders(<RulesManager />)
    await userEvent.click(await screen.findByRole('switch', { name: 'Active: No names' }))

    await vi.waitFor(() => {
      const patch = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')
      expect(patch?.[0]).toBe('/api/rules/1')
      expect(patch?.[1]?.body).toBe('{"is_active":false}')
    })
  })

  it('confirms in an in-app dialog before deleting', async () => {
    const fetchMock = mockFetch((_url, init) =>
      init?.method === 'DELETE' ? new Response(null, { status: 204 }) : Response.json([rule]),
    )

    renderWithProviders(<RulesManager />)
    await userEvent.click(await screen.findByRole('button', { name: 'Delete No names' }))
    const dialog = await screen.findByRole('dialog')
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false)
    await userEvent.click(within(dialog).getByRole('button', { name: 'Delete rule' }))

    await vi.waitFor(() => {
      expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(true)
    })
  })
})
