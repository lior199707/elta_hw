import { Link } from 'react-router'

import { ROUTES } from '@/lib/routes'

export function NotFoundPage() {
  return (
    <section className="space-y-3 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Page not found</h1>
      <p className="text-slate-600">The page you are looking for does not exist.</p>
      <Link to={ROUTES.check} className="font-medium text-indigo-700 underline">
        Go to the check page
      </Link>
    </section>
  )
}
