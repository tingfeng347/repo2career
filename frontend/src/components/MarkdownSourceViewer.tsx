import { useEffect, useMemo, useRef } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/services/api"
import { evidenceLabel, evidenceStyle, type EvidenceRef } from "./evidence"

type Props = {
  jobId: string
  references: EvidenceRef[]
  activeEvidenceId: string | null
  onEvidenceSelect: (reference: EvidenceRef) => void
}

export function MarkdownSourceViewer({ jobId, references, activeEvidenceId, onEvidenceSelect }: Props) {
  const activeElement = useRef<HTMLButtonElement | null>(null)
  const source = useQuery({
    queryKey: ["source-markdown", jobId],
    queryFn: () => api.sourceMarkdown(jobId),
  })
  const lines = useMemo(() => (source.data ?? "").split("\n"), [source.data])
  const documentReferences = useMemo(
    () => references
      .filter((reference) => reference.kind === "markdown")
      .map((reference) => locateReference(reference, source.data ?? ""))
      .filter((reference) => reference.start_line)
      .sort((left, right) => (left.start_line ?? 0) - (right.start_line ?? 0)),
    [references, source.data],
  )

  useEffect(() => {
    activeElement.current?.scrollIntoView?.({ behavior: "smooth", block: "center" })
  }, [activeEvidenceId])

  if (source.isLoading) return <div className="source-empty">正在读取原始 Markdown…</div>
  if (source.isError) return <div className="source-empty">无法读取原始 Markdown。</div>

  let cursor = 1
  return (
    <div className="source-document app-scrollbar">
      {documentReferences.map((reference) => {
        const start = reference.start_line ?? cursor
        const end = reference.end_line ?? start
        const before = lines.slice(cursor - 1, start - 1)
        const excerpt = lines.slice(start - 1, end)
        cursor = end + 1
        return (
          <div key={reference.id}>
            {before.length > 0 && <SourceLines lines={before} start={start - before.length} />}
            <button
              ref={activeEvidenceId === reference.id ? activeElement : undefined}
              type="button"
              className="source-evidence-block"
              data-active={activeEvidenceId === reference.id}
              style={evidenceStyle(reference.id)}
              onClick={() => onEvidenceSelect(reference)}
              aria-label={`查看引用：${evidenceLabel(reference)}`}
            >
              <span className="source-evidence-label">{evidenceLabel(reference)}</span>
              <SourceLines lines={excerpt} start={start} />
            </button>
          </div>
        )
      })}
      {documentReferences.length > 0 && cursor <= lines.length && (
        <SourceLines lines={lines.slice(cursor - 1)} start={cursor} />
      )}
      {documentReferences.length === 0 && <SourceLines lines={lines} start={1} />}
    </div>
  )
}

function SourceLines({ lines, start }: { lines: string[]; start: number }) {
  return (
    <span className="source-lines">
      {lines.map((line, index) => (
        <span className="source-line" key={`${start + index}-${line}`}>
          <span className="source-line-number">{start + index}</span>
          <span>{line || " "}</span>
        </span>
      ))}
    </span>
  )
}

function locateReference(reference: EvidenceRef, source: string): EvidenceRef {
  if (reference.start_line || !reference.excerpt) return reference
  let offset = source.indexOf(reference.excerpt)
  if (offset < 0) {
    const firstMeaningfulLine = reference.excerpt.split("\n").find((line) => line.trim().length > 12)
    offset = firstMeaningfulLine ? source.indexOf(firstMeaningfulLine) : -1
  }
  if (offset < 0) return reference
  const startLine = source.slice(0, offset).split("\n").length
  const endLine = startLine + reference.excerpt.split("\n").length - 1
  return { ...reference, start_line: startLine, end_line: endLine }
}
