import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

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
    <section className="report-layout">
      <nav className="report-index" aria-label="报告章节">
        <p className="eyebrow">报告目录</p>
        {sections.map((section, index) => <a key={section} href={`#section-${index + 1}`}>{section}</a>)}
        <a className="download-link" href={`/api/v1/analyses/${jobId}/artifacts/report-bundle.zip`} download>下载完整报告包</a>
        <a href={`/api/v1/analyses/${jobId}/artifacts/report.md`} download>仅下载 Markdown</a>
      </nav>
      <article className="report-paper">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h2: ({ children, ...props }) => {
              const text = String(children)
              const number = sections.indexOf(text) + 1
              return <h2 id={`section-${number}`} {...props}>{children}</h2>
            },
            code: ({ children }) => <code>{children}</code>,
          }}
        >{visibleReport}</ReactMarkdown>
      </article>
    </section>
  )
}
