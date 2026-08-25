import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import cesium from 'vite-plugin-cesium'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    (cesium as any)(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    watch: {
      ignored: ['**/dist/**', '**/node_modules/**'],
    },
  },
  build: {
    // CesiumJS + Leaflet are inherently large (>500KB gzipped is expected for 3D globe apps)
    chunkSizeWarningLimit: 1000,
    rolldownOptions: {
      output: {
        // Manually split vendor chunks to improve caching and parallel loading
        manualChunks(id: string) {
          if (id.includes('cesium') || id.includes('resium')) return 'vendor-cesium';
          if (id.includes('leaflet') || id.includes('react-leaflet')) return 'vendor-leaflet';
          if (id.includes('recharts') || id.includes('d3-')) return 'vendor-charts';
          if (id.includes('node_modules')) return 'vendor';
        },
      },
    },
  },
  optimizeDeps: {
    include: ['cesium', 'leaflet', 'recharts', 'axios', 'gsap'],
  },
})

