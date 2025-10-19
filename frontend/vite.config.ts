// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // This proxies API requests to your backend server during development
    proxy: {
      '/api': 'http://localhost:5000' // Assuming your backend runs on port 5000
    }
  }
});