import { useMemo } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { evidenceLabel, evidenceStyle, linkEvidenceCitations, type EvidenceRef } from "./evidence"

type Props = {
  report: string
  references: EvidenceRef[]
  activeEvidenceId: string | null
  onEvidenceSelect: (reference: EvidenceRef) => void
}

export function EvidenceReport({ report, references, activeEvidenceId, onEvidenceSelect }: Props) {
  const linkedReport = useMemo(
    () => linkEvidenceCitations(report, references),
    [report, references],
  )
  const referenceMap = useMemo(
    () => new Map(references.map((reference) => [reference.id, reference])),
    [references],
  )

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children, ...props }) => {
          const id = href?.startsWith("#evidence-")
            ? decodeURIComponent(href.slice("#evidence-".length))
            : null
          const reference = id ? referenceMap.get(id) : undefined
          if (!reference) return <a href={href} {...props}>{children}</a>
          return (
            <button
              type="button"
              className="evidence-citation"
              data-active={activeEvidenceId === reference.id}
              style={evidenceStyle(reference.id)}
              title={`${evidenceLabel(reference)}：${reference.excerpt.slice(0, 120)}`}
              onClick={() => onEvidenceSelect(reference)}
            >
              {evidenceLabel(reference)}
            </button>
          )
        },
      }}
    >
      {linkedReport}
    </ReactMarkdown>
  )
}
