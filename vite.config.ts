import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';
import { defineConfig } from 'vite';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    build: {
      target: 'esnext',
      chunkSizeWarningLimit: 2000,
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      watch: {
        ignored: [
          '**/*.db',
          '**/*.db-*',
          '**/*.sqlite',
          '**/*.sqlite-*',
          '**/haybatalsultan.db*',
          '**/backups/**',
          '**/uploads/**',
          '**/*.log',
          '**/.git/**',
          '**/server_*.cjs',
          '**/release/**',
        ],
      },
      proxy: {
        '/api': {
          target: 'http://localhost:3001',
          changeOrigin: true,
        },
        '/socket.io': {
          target: 'http://localhost:3001',
          ws: true,
          changeOrigin: true,
        },
      },
    },
  };
});
