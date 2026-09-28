import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  build: {
    format: 'file',
  },
  vite: {
    ssr: {
      external: ['better-sqlite3'],
    },
  },
});
