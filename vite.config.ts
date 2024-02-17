import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
 
export default defineConfig({
  server: {
    cors: false,
    proxy: {
      // '/api': {
      //   target: 'http://localhost:8000',
      //   // changeOrigin: true,
      //   // configure: (proxy, options) => {
      //   //   // proxy will be an instance of 'http-proxy'
      //   // },
      // },
      '/api': {
        target: 'http://localhost:8000/api',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})