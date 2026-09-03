export type Job = {
  id: string
  source_kind: "github" | "folder" | "pdf" | "markdown"
  status: "queued" | "running" | "interrupted" | "completed" | "failed" | "cancelled"
  stage: string
  progress: number
  source: Record<string, unknown>
  options: Record<string, unknown>
  error?: string
  created_at: string
}

export type Capabilities = {
  codegraph: { available: boolean }
  archify: { available: boolean }
  deepseek: { configured: boolean; model: string }
  mineru: { configured: boolean }
  pdf_parser: "mineru" | "pypdf"
}

export type EvidenceRef = {
  id: string
  kind: "code" | "pdf" | "markdown" | "metadata"
  path: string
  excerpt: string
  start_line?: number | null
  end_line?: number | null
  page?: number | null
  bbox?: [number, number, number, number] | null
}

export type EvidenceBundle = {
  tree: string[]
  references: EvidenceRef[]
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(detail.detail ?? "Request failed")
  }
  return response.json() as Promise<T>
}

export const api = {
  jobs: () => request<Job[]>("/api/v1/analyses"),
  job: (id: string) => request<Job>(`/api/v1/analyses/${id}`),
  capabilities: () => request<Capabilities>("/api/v1/capabilities"),
  settings: () => request<{ settings: Array<Record<string, string | boolean>> }>("/api/v1/settings"),
  updateSettings: (values: Record<string, string>) => request("/api/v1/settings", {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ values }),
  }),
  github: (repository_url: string, language: string) => request<{ job_id: string }>("/api/v1/analyses/github", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ repository_url, language }),
  }),
  localFolder: (path: string, language: string) => request<{ job_id: string }>("/api/v1/analyses/local-folder", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path, language }),
  }),
  upload: (kind: "pdf" | "markdown", data: FormData) => request<{ job_id: string }>(`/api/v1/analyses/${kind}`, { method: "POST", body: data }),
  cancel: (id: string) => request<Job>(`/api/v1/analyses/${id}/cancel`, { method: "POST" }),
  retry: (id: string) => request<Job>(`/api/v1/analyses/${id}/retry`, { method: "POST" }),
  delete: (id: string) => request<{ job_id: string }>(`/api/v1/analyses/${id}`, { method: "DELETE" }),
  report: async (id: string) => {
    const response = await fetch(`/api/v1/analyses/${id}/artifacts/report.md`)
    if (!response.ok) throw new Error("Report is not ready")
    return response.text()
  },
  evidence: (id: string) => request<EvidenceBundle>(
    `/api/v1/analyses/${id}/artifacts/evidence.json`,
  ),
  sourceCode: (id: string, path: string) => request<{ path: string; content: string }>(
    `/api/v1/analyses/${id}/source/file?path=${encodeURIComponent(path)}`,
  ),
  sourceMarkdown: async (id: string) => {
    const response = await fetch(`/api/v1/analyses/${id}/source.md`)
    if (!response.ok) throw new Error("Markdown source is not available")
    return response.text()
  },
}
