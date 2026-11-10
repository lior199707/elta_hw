import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/lib/test-utils/renderWithProviders'

import { makeCheckRun } from '../utils/checkRunFixtures'
import { CheckForm } from './CheckForm'

const rules = [
  { id: 1, title: 'No names', text: 'No people.' },
  { id: 2, title: 'No places', text: 'No locations.' },
]

function renderForm(formRules = rules) {
  return renderWithProviders(
    <Routes>
      <Route path="/" element={<CheckForm rules={formRules} />} />
      <Route path="/history/:id" element={<p>Result page</p>} />
    </Routes>,
  )
}

function mockFetch(response: Response | Promise<Response>) {
  const fetchMock = vi.fn<typeof fetch>().mockReturnValue(Promise.resolve(response))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function documentInput(): HTMLInputElement {
  const input = document.querySelector<HTMLInputElement>('input[type="file"]')
  if (!input) {
    throw new Error('File input not found')
  }
  return input
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('CheckForm', () => {
  it('disables Run check until a file is chosen', async () => {
    const user = userEvent.setup()
    renderForm()

    expect(screen.getByRole('button', { name: 'Run check' })).toBeDisabled()
    await user.upload(documentInput(), new File(['hello'], 'doc.txt'))

    expect(screen.getByRole('button', { name: 'Run check' })).toBeEnabled()
    expect(screen.getByText('doc.txt')).toBeInTheDocument()
  })

  it('checks every rule by default and supports select none and select all', async () => {
    const user = userEvent.setup()
    renderForm()

    expect(screen.getByRole('checkbox', { name: /No names/ })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: /No places/ })).toBeChecked()
    await user.click(screen.getByRole('button', { name: 'Select none' }))
    expect(screen.getByRole('checkbox', { name: /No names/ })).not.toBeChecked()
    await user.click(screen.getByRole('button', { name: 'Select all' }))

    expect(screen.getByRole('checkbox', { name: /No places/ })).toBeChecked()
  })

  it('disables Run check when no rule is selected', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.upload(documentInput(), new File(['hello'], 'doc.txt'))
    await user.click(screen.getByRole('button', { name: 'Select none' }))

    expect(screen.getByRole('button', { name: 'Run check' })).toBeDisabled()
  })

  it('rejects unsupported file types with a clear message', async () => {
    const user = userEvent.setup({ applyAccept: false })
    renderForm()

    await user.upload(documentInput(), new File(['x'], 'doc.pdf'))

    expect(screen.getByRole('alert')).toHaveTextContent('Unsupported file type')
    expect(screen.getByRole('button', { name: 'Run check' })).toBeDisabled()
  })

  it('shows an empty state linking to rules when there are no active rules', () => {
    renderForm([])

    expect(screen.getByText(/no active rules/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Add or activate a rule' })).toHaveAttribute(
      'href',
      '/rules',
    )
  })

  it('submits selected rule ids and navigates to the result', async () => {
    const user = userEvent.setup()
    const fetchMock = mockFetch(Response.json(makeCheckRun(), { status: 201 }))
    renderForm()

    await user.upload(documentInput(), new File(['hello'], 'doc.txt'))
    await user.click(screen.getByRole('checkbox', { name: /No places/ }))
    await user.click(screen.getByRole('button', { name: 'Run check' }))

    expect(await screen.findByText('Result page')).toBeInTheDocument()
    const body = fetchMock.mock.calls[0]?.[1]?.body as FormData
    expect(body.getAll('rule_ids')).toEqual(['1'])
  })

  it('shows pending state and disables inputs while running', async () => {
    const user = userEvent.setup()
    mockFetch(new Promise<Response>(() => undefined))
    renderForm()

    await user.upload(documentInput(), new File(['hello'], 'doc.txt'))
    await user.click(screen.getByRole('button', { name: 'Run check' }))

    expect(await screen.findByText(/Checking document... this can take a minute/)).toBeVisible()
    expect(screen.getByRole('button', { name: 'Checking...' })).toBeDisabled()
    expect(screen.getByRole('checkbox', { name: /No names/ })).toBeDisabled()
    expect(documentInput()).toBeDisabled()
  })

  it('shows the API error inline when the check fails', async () => {
    const user = userEvent.setup()
    mockFetch(Response.json({ detail: 'Document is empty' }, { status: 422 }))
    renderForm()

    await user.upload(documentInput(), new File(['hello'], 'doc.txt'))
    await user.click(screen.getByRole('button', { name: 'Run check' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Document is empty')
  })
})
