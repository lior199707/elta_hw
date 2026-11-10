import { HistoryList } from '@/features/checks/components/HistoryList'

export function HistoryPage() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">History</h1>
        <p className="text-sm text-slate-600">Previous check runs, newest first.</p>
      </div>
      <HistoryList />
    </section>
  )
}
