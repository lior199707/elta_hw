/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'

const DEFAULT_API_PROXY_TARGET = 'http://localhost:8000'

// In Docker dev the API lives at http://backend:8000; set API_PROXY_TARGET there.
const apiProxyTarget = process.env.API_PROXY_TARGET ?? DEFAULT_API_PROXY_TARGET
// Bind mounts from Windows do not deliver file-change events into the Linux VM.
const usePolling = process.env.VITE_USE_POLLING === 'true'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    proxy: { '/api': { target: apiProxyTarget, changeOrigin: true } },
    watch: usePolling ? { usePolling: true, interval: 300 } : undefined,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    restoreMocks: true,
  },
})
