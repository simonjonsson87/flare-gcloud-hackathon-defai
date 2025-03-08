import { defineConfig } from 'vite';

export default defineConfig({
  root: './',  // Root is where index.html lives
  build: {
    rollupOptions: {
      input: {
        main: './src/main.js',
        google: './src/google.js',
        app: './index.html'  // Explicitly include index.html as an entry
      }
    }
  }
});