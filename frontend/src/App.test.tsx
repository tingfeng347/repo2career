import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, expect, test, vi } from "vitest"
import App from "./App"

const defaultFetch = async (input: RequestInfo | URL) => {
  const url = String(input)
  const body = url.includes("capabilities")
    ? { codegraph: { available: true }, archify: { available: false }, deepseek: { configured: false, model: "deepseek-v4-pro" }, mineru: { configured: false }, pdf_parser: "pypdf" }
    : []
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } })
}

const fetchMock = vi.fn(defaultFetch)
vi.stubGlobal("fetch", fetchMock)

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  delete document.documentElement.dataset.theme
  fetchMock.mockReset()
  fetchMock.mockImplementation(defaultFetch)
})

test("renders the four source choices", async () => {
  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
  expect(await screen.findByRole("tab", { name: "GitHub 仓库" })).toBeInTheDocument()
  expect(screen.getByRole("tab", { name: "本地目录" })).toBeInTheDocument()
  expect(screen.getByRole("tab", { name: "PDF 文档" })).toBeInTheDocument()
  expect(screen.getByRole("tab", { name: "Markdown" })).toBeInTheDocument()
})

test("persists theme changes on the document root", async () => {
  window.localStorage.setItem("repo2career-theme", "light")
  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
  const toggle = await screen.findByRole("button", { name: "切换为暗色主题" })
  fireEvent.click(toggle)
  expect(document.documentElement.dataset.theme).toBe("dark")
  expect(window.localStorage.getItem("repo2career-theme")).toBe("dark")
})

test("shows the original PDF beside its generated Markdown", async () => {
  const pdfJob = {
    id: "pdf-job",
    source_kind: "pdf",
    status: "completed",
    stage: "completed",
    progress: 100,
    source: { name: "project.pdf" },
    options: {},
    created_at: "2026-09-02T00:00:00Z",
  }
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes("capabilities")) return defaultFetch(input)
    if (url.endsWith("report.md")) return new Response("# 报告\n\n## 摘要\n内容")
    return new Response(JSON.stringify([pdfJob]), { headers: { "Content-Type": "application/json" } })
  })

  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)

  expect(await screen.findByText("原始 PDF")).toBeInTheDocument()
  expect(screen.getByText("生成的 Markdown")).toBeInTheDocument()
  expect(screen.getByTitle("原始 PDF 预览")).toHaveAttribute(
    "src",
    "/api/v1/analyses/pdf-job/source.pdf#navpanes=0",
  )
  expect(screen.getByRole("article")).toHaveClass("hide-scrollbar")
})

test("uploads Markdown through the direct document endpoint", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes("capabilities")) return defaultFetch(input)
    if (url.endsWith("/markdown")) {
      return new Response(JSON.stringify({ job_id: "markdown-job" }), {
        headers: { "Content-Type": "application/json" },
      })
    }
    return new Response(JSON.stringify([]), { headers: { "Content-Type": "application/json" } })
  })

  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
  const markdownTab = await screen.findByRole("tab", { name: "Markdown" })
  fireEvent.mouseDown(markdownTab, { button: 0, ctrlKey: false })
  const description = await screen.findByText(/直接读取 UTF-8 Markdown/)
  const input = description.parentElement?.parentElement?.querySelector("input")
  expect(input).toBeTruthy()
  fireEvent.change(input!, {
    target: { files: [new File(["# Project"], "project.md", { type: "text/markdown" })] },
  })

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/analyses/markdown",
    expect.objectContaining({ method: "POST" }),
  ))
})

test("submits a local path without uploading directory files", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes("capabilities")) return defaultFetch(input)
    if (url.endsWith("/local-folder")) {
      return new Response(JSON.stringify({ job_id: "local-folder-job" }), {
        headers: { "Content-Type": "application/json" },
      })
    }
    return new Response(JSON.stringify([]), { headers: { "Content-Type": "application/json" } })
  })

  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
  fireEvent.mouseDown(await screen.findByRole("tab", { name: "本地目录" }), { button: 0, ctrlKey: false })
  fireEvent.change(await screen.findByLabelText("本地目录路径"), { target: { value: "/tmp/project" } })
  fireEvent.click(screen.getByRole("button", { name: "开始分析" }))

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/analyses/local-folder",
    expect.objectContaining({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: "/tmp/project", language: "zh-CN" }),
    }),
  ))
  expect(document.querySelector('input[type="file"][multiple]')).toBeNull()
})

test("deletes a project only after confirmation", async () => {
  let deleted = false
  const job = {
    id: "folder-job",
    source_kind: "folder",
    status: "completed",
    stage: "completed",
    progress: 100,
    source: { name: "demo" },
    options: {},
    created_at: "2026-09-02T00:00:00Z",
  }
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.includes("capabilities")) return defaultFetch(input)
    if (url.endsWith("report.md")) return new Response("# 报告")
    if (init?.method === "DELETE") {
      deleted = true
      return new Response(JSON.stringify({ job_id: job.id }), { headers: { "Content-Type": "application/json" } })
    }
    return new Response(JSON.stringify(deleted ? [] : [job]), { headers: { "Content-Type": "application/json" } })
  })

  render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
  fireEvent.click(await screen.findByRole("button", { name: "删除项目 demo" }))

  expect(screen.getByRole("alertdialog")).toBeInTheDocument()
  expect(deleted).toBe(false)
  fireEvent.click(screen.getByRole("button", { name: "删除项目" }))

  await waitFor(() => expect(deleted).toBe(true))
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/analyses/folder-job",
    expect.objectContaining({ method: "DELETE" }),
  )
})
