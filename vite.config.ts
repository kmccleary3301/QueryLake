import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// import SERVER_ADDR_HTTP from "./src/config_server_hostnames"

export default defineConfig({
  server: {
    cors: false,
    proxy: {
      '/api/': {
        target: 'http://localhost:8000/api/',
        changeOrigin: true,
        // timeout: 20000,
        // configure: (proxy, options) => {
        //   // proxy will be an instance of 'http-proxy'
        // },
        configure: () => {
          // proxy will be an instance of 'http-proxy'
        },
      },
      // '/ping': {
      //   target: 'http://localhost:8000/ping',
      //   changeOrigin: true,
      //   rewrite: (path) => path.replace(/^\/ping/, ''),
      //   // configure: (proxy, options) => {
      //   //   // proxy will be an instance of 'http-proxy'
      //   // },
      // },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})