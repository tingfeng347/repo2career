export type Job = {
  id: string
  source_kind: "github" | "folder" | "pdf"
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
  upload: (kind: "folder" | "pdf", data: FormData) => request<{ job_id: string }>(`/api/v1/analyses/${kind}`, { method: "POST", body: data }),
  cancel: (id: string) => request<Job>(`/api/v1/analyses/${id}/cancel`, { method: "POST" }),
  retry: (id: string) => request<Job>(`/api/v1/analyses/${id}/retry`, { method: "POST" }),
  report: async (id: string) => {
    const response = await fetch(`/api/v1/analyses/${id}/artifacts/report.md`)
    if (!response.ok) throw new Error("Report is not ready")
    return response.text()
  },
}

