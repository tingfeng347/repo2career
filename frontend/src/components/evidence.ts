import type { CSSProperties } from "react"

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
  references: EvidenceRef[]
}

const COLORS = ["#2878d0", "#d0643b", "#188b69", "#9a5bc4", "#bd8b16", "#c34f72"]

export function evidenceColor(id: string): string {
  let hash = 0
  for (const character of id) hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0
  return COLORS[Math.abs(hash) % COLORS.length]
}

export function evidenceStyle(id: string): CSSProperties {
  return { "--evidence-color": evidenceColor(id) } as CSSProperties
}

export function linkEvidenceCitations(markdown: string, references: EvidenceRef[]): string {
  const ids = new Set(references.map((reference) => reference.id))
  return markdown.replace(/\[([A-Za-z0-9][A-Za-z0-9_.:-]*)\]/g, (token, id: string) => (
    ids.has(id) ? `[${id}](#evidence-${encodeURIComponent(id)})` : token
  ))
}

export function evidenceLabel(reference: EvidenceRef): string {
  if (reference.kind === "pdf" && reference.page) return `第 ${reference.page} 页`
  if (reference.kind === "code" && reference.start_line) {
    const filename = reference.path.split("/").at(-1) ?? reference.path
    const lines = reference.end_line && reference.end_line !== reference.start_line
      ? `${reference.start_line}–${reference.end_line}`
      : String(reference.start_line)
    return `${filename}:${lines}`
  }
  if (reference.start_line) {
    return reference.end_line && reference.end_line !== reference.start_line
      ? `${reference.start_line}–${reference.end_line} 行`
      : `第 ${reference.start_line} 行`
  }
  return reference.id
}
