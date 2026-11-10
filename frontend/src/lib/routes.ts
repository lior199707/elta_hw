export const ROUTES = {
  check: '/',
  rules: '/rules',
  history: '/history',
  historyDetail: (id: number | string) => `/history/${id}`,
} as const

export const HISTORY_ID_PARAM = 'id'
export const HISTORY_DETAIL_PATTERN = `/history/:${HISTORY_ID_PARAM}`
