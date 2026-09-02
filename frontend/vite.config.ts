import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    proxy: { "/api": process.env.REPO2CAREER_API_TARGET ?? "http://127.0.0.1:8000" },
  },
  test: { environment: "jsdom", setupFiles: "./src/test/setup.ts" },
})
