import { useState } from 'react'
import { toast } from 'sonner'

import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/dialog'
import { Spinner } from '@/components/ui/spinner'
import { getErrorMessage } from '@/lib/api/getErrorMessage'

import { useDeleteRule, useUpdateRule } from '../hooks/useRuleMutations'
import { useRules } from '../hooks/useRules'
import { RuleActiveFilter } from '../types/rule'
import type { Rule } from '../types/rule'
import { RuleFormDialog } from './RuleFormDialog'
import { RuleListItem } from './RuleListItem'

type DialogState = { kind: 'closed' } | { kind: 'form'; rule: Rule | null }

export function RulesManager() {
  const rulesQuery = useRules(RuleActiveFilter.All)
  const updateRule = useUpdateRule()
  const deleteRule = useDeleteRule()
  const [dialog, setDialog] = useState<DialogState>({ kind: 'closed' })
  const [ruleToDelete, setRuleToDelete] = useState<Rule | null>(null)

  const handleToggle = (rule: Rule, isActive: boolean) => {
    updateRule.mutate(
      { id: rule.id, payload: { is_active: isActive } },
      {
        onError: (error) => toast.error(getErrorMessage(error)),
      },
    )
  }

  const handleDelete = (rule: Rule) => {
    deleteRule.mutate(rule.id, {
      onSuccess: () => {
        toast.success('Rule deleted')
        setRuleToDelete(null)
      },
    })
  }

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Rules</h1>
        <p className="text-sm text-slate-600">Requirements that documents are checked against.</p>
      </div>
      <Button
        onClick={() => {
          setDialog({ kind: 'form', rule: null })
        }}
      >
        Add rule
      </Button>
    </div>
  )

  let content
  if (rulesQuery.isPending) {
    content = (
      <p role="status" className="flex items-center gap-2 text-slate-600">
        <Spinner /> Loading rules...
      </p>
    )
  } else if (rulesQuery.isError) {
    content = (
      <Alert tone="error">
        <p>Could not load rules: {getErrorMessage(rulesQuery.error)}</p>
        <Button
          variant="secondary"
          size="sm"
          className="mt-2"
          onClick={() => {
            void rulesQuery.refetch()
          }}
        >
          Retry
        </Button>
      </Alert>
    )
  } else if (rulesQuery.data.length === 0) {
    content = (
      <p className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-slate-600">
        No rules yet. Add your first rule to start checking documents.
      </p>
    )
  } else {
    content = (
      <ul className="space-y-3">
        {rulesQuery.data.map((rule) => (
          <RuleListItem
            key={rule.id}
            rule={rule}
            isToggling={updateRule.isPending && updateRule.variables.id === rule.id}
            onToggleActive={handleToggle}
            onEdit={(selected) => {
              setDialog({ kind: 'form', rule: selected })
            }}
            onDelete={(selected) => {
              deleteRule.reset()
              setRuleToDelete(selected)
            }}
          />
        ))}
      </ul>
    )
  }

  return (
    <section className="space-y-6">
      {header}
      {content}
      <RuleFormDialog
        key={dialog.kind === 'form' ? (dialog.rule?.id ?? 'new') : 'closed'}
        open={dialog.kind === 'form'}
        onOpenChange={(open) => {
          if (!open) {
            setDialog({ kind: 'closed' })
          }
        }}
        rule={dialog.kind === 'form' ? dialog.rule : null}
      />
      <ConfirmDialog
        open={ruleToDelete !== null}
        onOpenChange={(open) => {
          if (!open) {
            setRuleToDelete(null)
          }
        }}
        title="Delete rule"
        description={`Delete "${ruleToDelete?.title ?? ''}"? Past check results keep their own copy of the rule.`}
        confirmLabel="Delete rule"
        isPending={deleteRule.isPending}
        errorMessage={deleteRule.error ? getErrorMessage(deleteRule.error) : null}
        onConfirm={() => {
          if (ruleToDelete) {
            handleDelete(ruleToDelete)
          }
        }}
      />
    </section>
  )
}
