import { useState } from 'react'
import type { SyntheticEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'

import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { getErrorMessage } from '@/lib/api/getErrorMessage'
import { ROUTES } from '@/lib/routes'

import { useRunCheck } from '../hooks/useCheckMutations'
import type { SelectableRule } from '../types/checkRun'
import { validateDocumentFile } from '../utils/validateDocumentFile'
import { FileDropzone } from './FileDropzone'
import { RuleSelector } from './RuleSelector'

export function CheckForm({ rules }: { rules: SelectableRule[] }) {
  const navigate = useNavigate()
  const runCheck = useRunCheck()
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<ReadonlySet<number>>(
    () => new Set(rules.map((rule) => rule.id)),
  )

  if (rules.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
        <p className="text-slate-700">There are no active rules to check against.</p>
        <p className="mt-1 text-sm text-slate-600">
          <Link to={ROUTES.rules} className="font-medium text-indigo-700 underline">
            Add or activate a rule
          </Link>{' '}
          to run a check.
        </p>
      </div>
    )
  }

  const isRunning = runCheck.isPending
  const ruleIds = rules.filter((rule) => selectedIds.has(rule.id)).map((rule) => rule.id)
  const canRun = file !== null && fileError === null && ruleIds.length > 0 && !isRunning

  const handleFileSelected = (selected: File) => {
    const error = validateDocumentFile(selected)
    setFileError(error)
    setFile(error ? null : selected)
    runCheck.reset()
  }

  const handleToggleRule = (ruleId: number) => {
    setSelectedIds((previous) => {
      const next = new Set(previous)
      if (!next.delete(ruleId)) {
        next.add(ruleId)
      }
      return next
    })
  }

  const handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!file || !canRun) {
      return
    }
    runCheck.mutate(
      { file, ruleIds },
      {
        onSuccess: (run) => {
          void navigate(ROUTES.historyDetail(run.id))
        },
        onError: (error) => {
          toast.error(getErrorMessage(error))
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <FileDropzone
        file={file}
        error={fileError}
        disabled={isRunning}
        onFileSelected={handleFileSelected}
      />
      <RuleSelector
        rules={rules}
        selectedIds={selectedIds}
        disabled={isRunning}
        onToggle={handleToggleRule}
        onSelectAll={() => {
          setSelectedIds(new Set(rules.map((rule) => rule.id)))
        }}
        onSelectNone={() => {
          setSelectedIds(new Set())
        }}
      />
      {runCheck.isError ? <Alert tone="error">{getErrorMessage(runCheck.error)}</Alert> : null}
      {isRunning ? (
        <p role="status" className="flex items-center gap-2 text-sm text-slate-700">
          <Spinner /> Checking document... this can take a minute
        </p>
      ) : null}
      <Button type="submit" disabled={!canRun}>
        {isRunning ? 'Checking...' : 'Run check'}
      </Button>
    </form>
  )
}
