import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, expect, test, vi } from "vitest"
import App from "./App"

vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
  const url = String(input)
  const body = url.includes("capabilities")
    ? { codegraph: { available: true }, archify: { available: false }, deepseek: { configured: false, model: "deepseek-v4-pro" }, mineru: { configured: false }, pdf_parser: "pypdf" }
    : []
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } })
}))

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  delete document.documentElement.dataset.theme
})

test("renders the three source choices", async () => {
  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
  expect(await screen.findByRole("tab", { name: "GitHub 仓库" })).toBeInTheDocument()
  expect(screen.getByRole("tab", { name: "本地目录" })).toBeInTheDocument()
  expect(screen.getByRole("tab", { name: "PDF 文档" })).toBeInTheDocument()
})

test("persists theme changes on the document root", async () => {
  window.localStorage.setItem("repo2career-theme", "light")
  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
  const toggle = await screen.findByRole("button", { name: "切换为暗色主题" })
  fireEvent.click(toggle)
  expect(document.documentElement.dataset.theme).toBe("dark")
  expect(window.localStorage.getItem("repo2career-theme")).toBe("dark")
})
