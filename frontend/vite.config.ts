import tailwindcss from '@tailwindcss/vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import { defineConfig, type PluginOption } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom']
        }
      }
    },
    sourcemap: false
  },
  define: {
    'process.env': {
      VITE_SECURE_LOCAL_STORAGE_HASH_KEY:
        process.env.VITE_SECURE_LOCAL_STORAGE_HASH_KEY,
      VITE_SECURE_LOCAL_STORAGE_PREFIX:
        process.env.VITE_SECURE_LOCAL_STORAGE_PREFIX
    }
  },
  plugins: [
    visualizer({
      open: false
    }) as PluginOption,
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true
    }),
    react(),
    tailwindcss()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
