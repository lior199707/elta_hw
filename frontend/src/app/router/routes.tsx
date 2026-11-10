import type { RouteObject } from 'react-router'

import { AppLayout } from '@/components/layout/AppLayout'
import { HISTORY_DETAIL_PATTERN, ROUTES } from '@/lib/routes'
import { CheckPage } from '@/pages/CheckPage'
import { CheckResultPage } from '@/pages/CheckResultPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { RulesPage } from '@/pages/RulesPage'

const NOT_FOUND_PATH = '*'

export const routes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.check, element: <CheckPage /> },
      { path: ROUTES.rules, element: <RulesPage /> },
      { path: ROUTES.history, element: <HistoryPage /> },
      { path: HISTORY_DETAIL_PATTERN, element: <CheckResultPage /> },
      { path: NOT_FOUND_PATH, element: <NotFoundPage /> },
    ],
  },
]
