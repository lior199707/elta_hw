import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

import { RULE_TEXT_MAX_LENGTH, ruleFormSchema } from '../schemas/rule.schema'
import type { RuleFormData, RuleFormValues } from '../types/rule'

interface RuleFormProps {
  defaultValues: RuleFormValues
  submitLabel: string
  isPending: boolean
  errorMessage: string | null
  onSubmit: (data: RuleFormData) => void
  onCancel: () => void
}

export function RuleForm({
  defaultValues,
  submitLabel,
  isPending,
  errorMessage,
  onSubmit,
  onCancel,
}: RuleFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RuleFormValues, unknown, RuleFormData>({
    resolver: zodResolver(ruleFormSchema),
    defaultValues,
  })

  return (
    <form
      onSubmit={(event) => {
        void handleSubmit(onSubmit)(event)
      }}
      noValidate
      className="space-y-4"
    >
      <div className="space-y-1">
        <label htmlFor="rule-title" className="text-sm font-medium text-slate-800">
          Title
        </label>
        <Input
          id="rule-title"
          aria-invalid={errors.title ? true : undefined}
          aria-describedby={errors.title ? 'rule-title-error' : undefined}
          disabled={isPending}
          {...register('title')}
        />
        {errors.title ? (
          <p id="rule-title-error" className="text-sm text-red-700">
            {errors.title.message}
          </p>
        ) : null}
      </div>
      <div className="space-y-1">
        <label htmlFor="rule-text" className="text-sm font-medium text-slate-800">
          Rule text
        </label>
        <Textarea
          id="rule-text"
          aria-invalid={errors.text ? true : undefined}
          aria-describedby={errors.text ? 'rule-text-error' : undefined}
          disabled={isPending}
          {...register('text')}
        />
        <p className="text-xs text-slate-500">
          Describe what the document must or must not contain (max {RULE_TEXT_MAX_LENGTH}{' '}
          characters).
        </p>
        {errors.text ? (
          <p id="rule-text-error" className="text-sm text-red-700">
            {errors.text.message}
          </p>
        ) : null}
      </div>
      <label className="flex items-center gap-2 text-sm text-slate-800">
        <input
          type="checkbox"
          className="size-4 accent-indigo-600"
          disabled={isPending}
          {...register('is_active')}
        />
        Active (included in checks by default)
      </label>
      {errorMessage ? <Alert tone="error">{errorMessage}</Alert> : null}
      <div className="flex justify-end gap-2">
        <Button variant="secondary" disabled={isPending} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving...' : submitLabel}
        </Button>
      </div>
    </form>
  )
}
