import { toast } from 'sonner'

import { Dialog } from '@/components/ui/dialog'
import { getErrorMessage } from '@/lib/api/getErrorMessage'

import { useCreateRule, useUpdateRule } from '../hooks/useRuleMutations'
import type { Rule, RuleFormData } from '../types/rule'
import { EMPTY_RULE_FORM_VALUES } from '../schemas/ruleFormDefaults'
import { RuleForm } from './RuleForm'

interface RuleFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule: Rule | null
}

export function RuleFormDialog({ open, onOpenChange, rule }: RuleFormDialogProps) {
  const createRule = useCreateRule()
  const updateRule = useUpdateRule()
  const mutation = rule ? updateRule : createRule

  const handleSubmit = (data: RuleFormData) => {
    const onSuccess = () => {
      toast.success(rule ? 'Rule updated' : 'Rule added')
      onOpenChange(false)
    }
    if (rule) {
      updateRule.mutate({ id: rule.id, payload: data }, { onSuccess })
    } else {
      createRule.mutate(data, { onSuccess })
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={rule ? 'Edit rule' : 'Add rule'}
      description="A rule is a plain-language requirement the document is checked against."
    >
      <RuleForm
        defaultValues={
          rule
            ? { title: rule.title, text: rule.text, is_active: rule.is_active }
            : EMPTY_RULE_FORM_VALUES
        }
        submitLabel={rule ? 'Save changes' : 'Add rule'}
        isPending={mutation.isPending}
        errorMessage={mutation.error ? getErrorMessage(mutation.error) : null}
        onSubmit={handleSubmit}
        onCancel={() => {
          onOpenChange(false)
        }}
      />
    </Dialog>
  )
}
