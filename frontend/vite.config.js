import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [
      vue(),
      vueDevTools(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    clearScreen: false,
    server: {
      host: 'localhost',
      port: 5173,
      strictPort: true,
      proxy: {
        '/auth': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true
        },
        '/events': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true
        },
        '/tasks': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true
        },
        '/agent': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true,
          ws: true
        },
        '/sync': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true
        },
        '/api/v1/tis': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true
        },
        '/api/v1/blackboard': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true
        },
        '/api/v1/email': {
          target: env.VITE_API_URL || 'http://localhost:8002',
          changeOrigin: true
        }
      },
    },
    envPrefix: ['VITE_', 'TAURI_'],
    test: {
      environment: 'happy-dom',
      include: ['src/__tests__/**/*.test.js'],
      setupFiles: ['src/__tests__/setup.js'],
    },
    build: {
      target: process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari13',
      outDir: 'dist',
      sourcemap: !!process.env.TAURI_ENV_DEBUG,
    }
  }
})
