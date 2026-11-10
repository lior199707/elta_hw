import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { RouterProvider, createMemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { createQueryClient } from '@/lib/query/queryClient'

import { routes } from './routes'

function renderAt(path: string) {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockImplementation(() => Promise.resolve(Response.json([]))),
  )
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  return render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('routes', () => {
  it('renders the main navigation with Check, Rules and History', async () => {
    renderAt('/')

    const nav = screen.getByRole('navigation', { name: 'Main' })
    expect(nav).toHaveTextContent('Check')
    expect(screen.getByRole('link', { name: 'Rules' })).toHaveAttribute('href', '/rules')
    expect(screen.getByRole('link', { name: 'History' })).toHaveAttribute('href', '/history')
    expect(await screen.findByText(/no active rules/i)).toBeInTheDocument()
  })

  it('renders the history page', async () => {
    renderAt('/history')

    expect(await screen.findByText('No checks have been run yet.')).toBeInTheDocument()
  })

  it('renders a not found page for unknown paths', () => {
    renderAt('/does-not-exist')

    expect(screen.getByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
  })

  it('rejects an invalid run id', () => {
    renderAt('/history/abc')

    expect(screen.getByText('This check run id is not valid.')).toBeInTheDocument()
  })
})
