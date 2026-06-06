import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Garante uma única instância do Leaflet (evita que o leaflet.heat
  // augmente uma cópia diferente do `L` após a re-otimização de deps).
  resolve: {
    dedupe: ['leaflet', 'react-leaflet'],
  },
  optimizeDeps: {
    include: ['leaflet', 'leaflet.heat', 'react-leaflet'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
