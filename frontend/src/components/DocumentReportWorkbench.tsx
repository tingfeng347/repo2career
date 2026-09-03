import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Download, FileText, Link2 } from "lucide-react"
import { api } from "@/services/api"
import { EvidenceReport } from "./EvidenceReport"
import { MarkdownSourceViewer } from "./MarkdownSourceViewer"
import { PdfSourceViewer } from "./PdfSourceViewer"
import { presentableReport } from "./ReportWorkbench"
import type { EvidenceRef } from "./evidence"

type Props = {
  report: string
  jobId: string
  sourceKind: "pdf" | "markdown"
}

export function DocumentReportWorkbench({ report, jobId, sourceKind }: Props) {
  const evidence = useQuery({
    queryKey: ["evidence", jobId],
    queryFn: () => api.evidence(jobId),
  })
  const references = useMemo(
    () => (evidence.data?.references ?? []).filter((reference) => reference.kind === sourceKind),
    [evidence.data, sourceKind],
  )
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null)

  useEffect(() => {
    if (!activeEvidenceId && references.length > 0) setActiveEvidenceId(references[0].id)
  }, [activeEvidenceId, references])

  const selectEvidence = (reference: EvidenceRef) => setActiveEvidenceId(reference.id)
  const sourceLabel = sourceKind === "pdf" ? "原始 PDF" : "原始 Markdown"
  const sourceUrl = `/api/v1/analyses/${jobId}/source.${sourceKind === "pdf" ? "pdf" : "md"}`

  return (
    <div className="document-workbench">
      <section className="document-pane document-source-pane">
        <PaneHeader title={sourceLabel} downloadUrl={sourceUrl} downloadLabel={`下载${sourceLabel}`} />
        {sourceKind === "pdf" ? (
          <PdfSourceViewer
            jobId={jobId}
            references={references}
            activeEvidenceId={activeEvidenceId}
            onEvidenceSelect={selectEvidence}
          />
        ) : (
          <MarkdownSourceViewer
            jobId={jobId}
            references={references}
            activeEvidenceId={activeEvidenceId}
            onEvidenceSelect={selectEvidence}
          />
        )}
      </section>

      <section className="document-pane document-report-pane">
        <PaneHeader
          title="生成的 Markdown"
          downloadUrl={`/api/v1/analyses/${jobId}/artifacts/report.md`}
          downloadLabel="下载生成的 Markdown"
          hint="点击彩色引用，定位左侧原文"
        />
        <article className="report-paper app-scrollbar min-h-0 flex-1 overflow-y-auto px-6 py-8 xl:px-10">
          <EvidenceReport
            report={presentableReport(report)}
            references={references}
            activeEvidenceId={activeEvidenceId}
            onEvidenceSelect={selectEvidence}
          />
        </article>
      </section>
    </div>
  )
}

function PaneHeader({ title, downloadUrl, downloadLabel, hint }: {
  title: string
  downloadUrl: string
  downloadLabel: string
  hint?: string
}) {
  return (
    <header className="document-pane-header">
      <div className="flex min-w-0 items-center gap-2">
        <FileText className="size-4 shrink-0 text-muted-foreground" />
        <span className="truncate text-sm font-medium">{title}</span>
        {hint && (
          <span className="hidden items-center gap-1 text-[11px] text-muted-foreground xl:inline-flex">
            <Link2 className="size-3" /> {hint}
          </span>
        )}
      </div>
      <a href={downloadUrl} download className="document-download" aria-label={downloadLabel} title={downloadLabel}>
        <Download className="size-4" />
      </a>
    </header>
  )
}
