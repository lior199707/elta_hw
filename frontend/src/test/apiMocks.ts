import type { Page, Route } from '@playwright/test'

const API_PATH_PREFIX = '/api/'
export const CREATED_STATUS = 201
export const NO_CONTENT_STATUS = 204
export const NOT_FOUND_STATUS = 404

export interface MockRule {
  id: number
  title: string
  text: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export function makeMockRule(id: number, overrides: Partial<MockRule> = {}): MockRule {
  return {
    id,
    title: `Rule ${id}`,
    text: `Text of rule ${id}`,
    is_active: true,
    created_at: '2026-11-10T18:40:24Z',
    updated_at: '2026-11-10T18:40:24Z',
    ...overrides,
  }
}

export type ApiHandler = (route: Route) => Promise<void> | void

export async function mockApi(page: Page, handler: ApiHandler): Promise<void> {
  await page.route((url) => url.pathname.startsWith(API_PATH_PREFIX), handler)
}

export function apiPath(route: Route): string {
  const url = new URL(route.request().url())
  return `${url.pathname}${url.search}`
}
