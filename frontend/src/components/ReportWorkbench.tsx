import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Download, FileText } from "lucide-react"

type Props = { report: string; jobId: string }

const INTERNAL_SECTIONS = /(?:项目快照与分析范围|风险、证据缺口和置信度|证据索引|Project Snapshot and Analysis Scope|Risks, Evidence Gaps, and Confidence|Evidence Index)/i

function presentableReport(report: string): string {
  const output: string[] = []
  let hidden = false
  let sectionNumber = 0
  for (const line of report.split("\n")) {
    if (line.startsWith("## ")) {
      const title = line.slice(3).replace(/^\d+\.\s*/, "")
      hidden = INTERNAL_SECTIONS.test(title)
      if (!hidden) {
        sectionNumber += 1
        output.push(`## ${sectionNumber}. ${title}`)
      }
      continue
    }
    if (hidden || /^>\s*(模型|Model):/i.test(line)) continue
    output.push(line)
  }
  return output.join("\n").replace(/\n{3,}/g, "\n\n")
}

export function ReportWorkbench({ report, jobId }: Props) {
  const visibleReport = presentableReport(report)
  const sections = visibleReport.split(/^## /m).slice(1).map((section) => section.split("\n", 1)[0])
  return (
    <div className="mx-auto flex max-w-6xl items-start gap-8 px-6 py-8">
      <nav aria-label="报告章节" className="sticky top-6 hidden w-44 shrink-0 flex-col gap-0.5 text-xs lg:flex">
        <p className="mb-2 text-xs font-medium text-muted-foreground">报告目录</p>
        {sections.map((section, index) => (
          <a
            key={section}
            href={`#section-${index + 1}`}
            className="truncate rounded-md px-2 py-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {section}
          </a>
        ))}
        <div className="mt-3 flex flex-col gap-1.5 border-t pt-3">
          <a href={`/api/v1/analyses/${jobId}/artifacts/report-bundle.zip`} download className="inline-flex items-center gap-1.5 font-medium text-foreground hover:underline">
            <Download className="size-3.5" /> 下载完整报告包
          </a>
          <a href={`/api/v1/analyses/${jobId}/artifacts/report.md`} download className="inline-flex items-center gap-1.5 text-muted-foreground hover:underline">
            <FileText className="size-3.5" /> 仅下载 Markdown
          </a>
        </div>
      </nav>
      <article className="report-paper min-w-0 flex-1 rounded-xl border bg-card px-8 py-10 sm:px-12">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h2: ({ children, ...props }) => {
              const text = String(children)
              const number = sections.indexOf(text) + 1
              return <h2 id={`section-${number}`} {...props}>{children}</h2>
            },
          }}
        >{visibleReport}</ReactMarkdown>
      </article>
    </div>
  )
}
