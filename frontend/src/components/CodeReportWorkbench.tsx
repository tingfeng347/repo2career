import { useEffect, useMemo, useRef, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ChevronRight, Download, File, FileCode2, Folder, FolderOpen, Link2 } from "lucide-react"
import { api } from "@/services/api"
import { EvidenceReport } from "./EvidenceReport"
import { presentableReport } from "./ReportWorkbench"
import type { EvidenceRef } from "./evidence"

type Props = { report: string; jobId: string }

type TreeNode = {
  name: string
  path: string
  directory: boolean
  children: TreeNode[]
}

export function CodeReportWorkbench({ report, jobId }: Props) {
  const evidence = useQuery({
    queryKey: ["evidence", jobId],
    queryFn: () => api.evidence(jobId),
  })
  const references = useMemo(
    () => (evidence.data?.references ?? []).filter((item) => item.kind === "code"),
    [evidence.data],
  )
  const tree = useMemo(() => buildTree(evidence.data?.tree ?? []), [evidence.data?.tree])
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null)
  const [selectedPath, setSelectedPath] = useState("")
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const effectiveEvidenceId = activeEvidenceId ?? references[0]?.id ?? null
  const effectivePath = selectedPath || references[0]?.path || evidence.data?.tree[0] || ""
  const visibleExpanded = useMemo(
    () => new Set([...expanded, ...parentPaths(effectivePath)]),
    [effectivePath, expanded],
  )
  const codePaneRef = useRef<HTMLDivElement | null>(null)
  const activeReference = references.find((item) => item.id === effectiveEvidenceId)

  const source = useQuery({
    queryKey: ["source-code", jobId, effectivePath],
    queryFn: () => api.sourceCode(jobId, effectivePath),
    enabled: Boolean(effectivePath),
  })

  useEffect(() => {
    if (!source.data || !activeReference?.start_line || activeReference.path !== effectivePath) return
    requestAnimationFrame(() => {
      const target = codePaneRef.current
        ?.querySelector(`[data-line="${activeReference.start_line}"]`)
      if (target instanceof HTMLElement && typeof target.scrollIntoView === "function") {
        target.scrollIntoView({ block: "center" })
      }
    })
  }, [activeReference, effectivePath, source.data])

  const selectReference = (reference: EvidenceRef) => {
    setActiveEvidenceId(reference.id)
    setSelectedPath(reference.path)
    setExpanded((current) => new Set([...current, ...parentPaths(reference.path)]))
  }

  const selectFile = (path: string) => {
    setSelectedPath(path)
    const reference = references.find((item) => item.path === path)
    setActiveEvidenceId(reference?.id ?? null)
  }

  const toggleDirectory = (path: string) => {
    setExpanded((current) => {
      const next = new Set(current)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }

  return (
    <div className="code-report-workbench">
      <section className="document-pane code-source-pane">
        <header className="document-pane-header">
          <div className="flex min-w-0 items-center gap-2">
            <FileCode2 className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate text-sm font-medium">代码证据</span>
            <span className="font-mono text-[10px] text-muted-foreground">{evidence.data?.tree.length ?? 0} files</span>
          </div>
        </header>
        <div className="code-source-layout">
          <nav className="code-tree app-scrollbar" aria-label="代码文件树">
            {tree.map((node) => (
              <TreeItem
                key={node.path}
                node={node}
                depth={0}
                expanded={visibleExpanded}
                selectedPath={effectivePath}
                onToggle={toggleDirectory}
                onSelect={selectFile}
              />
            ))}
          </nav>
          <div className="code-viewer">
            <div className="code-viewer-header">
              <span className="truncate font-mono text-xs">{effectivePath || "选择文件"}</span>
              {activeReference?.start_line && activeReference.path === effectivePath && (
                <span className="code-location">L{activeReference.start_line}{activeReference.end_line && activeReference.end_line !== activeReference.start_line ? `–${activeReference.end_line}` : ""}</span>
              )}
            </div>
            <div ref={codePaneRef} className="code-lines app-scrollbar">
              {source.isPending && effectivePath && <div className="source-empty">正在读取源码…</div>}
              {source.isError && <div className="source-empty">无法读取该文件</div>}
              {source.data?.content.split("\n").map((line, index) => {
                const lineNumber = index + 1
                const highlighted = Boolean(
                  activeReference?.path === effectivePath
                  && activeReference.start_line
                  && lineNumber >= activeReference.start_line
                  && lineNumber <= (activeReference.end_line ?? activeReference.start_line),
                )
                return (
                  <div key={lineNumber} className="code-line" data-active={highlighted} data-line={lineNumber}>
                    <span className="code-line-number">{lineNumber}</span>
                    <code>{line || " "}</code>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="document-pane document-report-pane">
        <header className="document-pane-header">
          <div className="flex min-w-0 items-center gap-2">
            <FileCode2 className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate text-sm font-medium">生成的 Markdown</span>
            <span className="hidden items-center gap-1 text-[11px] text-muted-foreground xl:inline-flex">
              <Link2 className="size-3" /> 点击引用，定位左侧代码
            </span>
          </div>
          <a href={`/api/v1/analyses/${jobId}/artifacts/report.md`} download className="document-download" aria-label="下载生成的 Markdown">
            <Download className="size-4" />
          </a>
        </header>
        <article className="report-paper app-scrollbar min-h-0 flex-1 overflow-y-auto px-6 py-8 xl:px-10">
          <EvidenceReport
            report={presentableReport(report)}
            references={references}
            activeEvidenceId={effectiveEvidenceId}
            onEvidenceSelect={selectReference}
          />
        </article>
      </section>
    </div>
  )
}

function TreeItem({ node, depth, expanded, selectedPath, onToggle, onSelect }: {
  node: TreeNode
  depth: number
  expanded: Set<string>
  selectedPath: string
  onToggle: (path: string) => void
  onSelect: (path: string) => void
}) {
  const open = expanded.has(node.path)
  return (
    <div>
      <button
        type="button"
        className="code-tree-item"
        data-active={!node.directory && selectedPath === node.path}
        style={{ paddingLeft: `${0.55 + depth * 0.85}rem` }}
        onClick={() => node.directory ? onToggle(node.path) : onSelect(node.path)}
        aria-expanded={node.directory ? open : undefined}
        title={node.path}
      >
        {node.directory ? <ChevronRight className="code-tree-chevron" data-open={open} /> : <span className="code-tree-spacer" />}
        {node.directory ? (open ? <FolderOpen /> : <Folder />) : <File />}
        <span className="truncate">{node.name}</span>
      </button>
      {node.directory && open && node.children.map((child) => (
        <TreeItem
          key={child.path}
          node={child}
          depth={depth + 1}
          expanded={expanded}
          selectedPath={selectedPath}
          onToggle={onToggle}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}

function buildTree(paths: string[]): TreeNode[] {
  const root: TreeNode = { name: "", path: "", directory: true, children: [] }
  for (const path of paths) {
    let parent = root
    const parts = path.split("/").filter(Boolean)
    parts.forEach((name, index) => {
      const nodePath = parts.slice(0, index + 1).join("/")
      let node = parent.children.find((item) => item.name === name)
      if (!node) {
        node = { name, path: nodePath, directory: index < parts.length - 1, children: [] }
        parent.children.push(node)
      }
      parent = node
    })
  }
  const sort = (nodes: TreeNode[]): TreeNode[] => nodes
    .map((node) => ({ ...node, children: sort(node.children) }))
    .sort((left, right) => Number(right.directory) - Number(left.directory) || left.name.localeCompare(right.name))
  return sort(root.children)
}

function parentPaths(path: string): Set<string> {
  const parts = path.split("/")
  return new Set(parts.slice(0, -1).map((_, index) => parts.slice(0, index + 1).join("/")))
}
