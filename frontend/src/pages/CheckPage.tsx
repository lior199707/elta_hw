import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { CheckForm } from '@/features/checks/components/CheckForm'
import { useRules } from '@/features/rules/hooks/useRules'
import { RuleActiveFilter } from '@/features/rules/types/rule'
import { getErrorMessage } from '@/lib/api/getErrorMessage'

export function CheckPage() {
  const rulesQuery = useRules(RuleActiveFilter.Active)

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
  } else {
    content = <CheckForm rules={rulesQuery.data} />
  }

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Check a document</h1>
        <p className="text-sm text-slate-600">
          Upload a document and choose the rules it must follow.
        </p>
      </div>
      {content}
    </section>
  )
}
