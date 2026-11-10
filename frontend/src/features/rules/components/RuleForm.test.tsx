import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { EMPTY_RULE_FORM_VALUES } from '../schemas/ruleFormDefaults'
import { RuleForm } from './RuleForm'

function setup(overrides: Partial<Parameters<typeof RuleForm>[0]> = {}) {
  const onSubmit = vi.fn()
  const onCancel = vi.fn()
  render(
    <RuleForm
      defaultValues={EMPTY_RULE_FORM_VALUES}
      submitLabel="Add rule"
      isPending={false}
      errorMessage={null}
      onSubmit={onSubmit}
      onCancel={onCancel}
      {...overrides}
    />,
  )
  return { onSubmit, onCancel }
}

describe('RuleForm', () => {
  it('shows validation messages and does not submit empty values', async () => {
    const { onSubmit } = setup()

    await userEvent.click(screen.getByRole('button', { name: 'Add rule' }))

    expect(await screen.findByText('Title is required')).toBeInTheDocument()
    expect(screen.getByText('Rule text is required')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('rejects a title longer than 200 characters', async () => {
    const { onSubmit } = setup()

    await userEvent.click(screen.getByLabelText('Title'))
    await userEvent.paste('a'.repeat(201))
    await userEvent.click(screen.getByLabelText('Rule text'))
    await userEvent.paste('body')
    await userEvent.click(screen.getByRole('button', { name: 'Add rule' }))

    expect(await screen.findByText('Title must be at most 200 characters')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits trimmed validated values', async () => {
    const { onSubmit } = setup()

    await userEvent.type(screen.getByLabelText('Title'), '  No names ')
    await userEvent.type(screen.getByLabelText('Rule text'), 'Do not name people')
    await userEvent.click(screen.getByRole('button', { name: 'Add rule' }))

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1)
    })
    expect(onSubmit.mock.calls[0]?.[0]).toEqual({
      title: 'No names',
      text: 'Do not name people',
      is_active: true,
    })
  })

  it('disables inputs while pending and shows the API error', () => {
    setup({ isPending: true, errorMessage: 'Server said no' })

    expect(screen.getByLabelText('Title')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled()
    expect(screen.getByRole('alert')).toHaveTextContent('Server said no')
  })
})
