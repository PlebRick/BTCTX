import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',  // Specify output directory for build artifacts
    emptyOutDir: true,  // Remove old files before building
  },
});