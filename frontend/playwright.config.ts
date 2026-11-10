import { defineConfig, devices } from '@playwright/test'

const E2E_PORT = 4173

// `mocked` (default, `uv run poe fe-e2e`) mocks every /api call with page.route(); `backend`
// (`uv run poe fe-e2e-backend`) exercises the real API through Vite's /api proxy.
export default defineConfig({
  testDir: './src/test',
  testMatch: '**/*.spec.ts',
  reporter: 'list',
  use: { baseURL: `http://127.0.0.1:${E2E_PORT}`, trace: 'retain-on-failure' },
  projects: [
    {
      name: 'mocked',
      testIgnore: '**/backend/**',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      // Full stack: talks to the real backend on localhost:8000 (`uv run poe up`). Only rules
      // endpoints are used, so no Gemini call is ever made.
      name: 'backend',
      testMatch: 'backend/**/*.spec.ts',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: `npx vite --host 127.0.0.1 --port ${E2E_PORT} --strictPort`,
    url: `http://127.0.0.1:${E2E_PORT}`,
    reuseExistingServer: false,
  },
})
