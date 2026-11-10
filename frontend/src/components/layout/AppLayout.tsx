import { NavLink, Outlet } from 'react-router'

import { ROUTES } from '@/lib/routes'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Check', to: ROUTES.check, end: true },
  { label: 'Rules', to: ROUTES.rules, end: false },
  { label: 'History', to: ROUTES.history, end: false },
] as const

export function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <span className="text-lg font-semibold">Document Rule Checker</span>
          <nav aria-label="Main">
            <ul className="flex gap-1">
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) =>
                      cn(
                        'rounded-md px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-indigo-600',
                        isActive
                          ? 'bg-indigo-50 text-indigo-700'
                          : 'text-slate-700 hover:bg-slate-100',
                      )
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
