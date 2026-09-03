import { useEffect, useMemo, useRef, useState } from "react"
import { ChevronLeft, ChevronRight, Minus, Plus } from "lucide-react"
import type { PDFDocumentLoadingTask, PDFDocumentProxy } from "pdfjs-dist/legacy/build/pdf.mjs"
import pdfWorkerUrl from "pdfjs-dist/legacy/build/pdf.worker.min.mjs?url"
import type { EvidenceRef } from "./evidence"

type PdfJs = typeof import("pdfjs-dist/legacy/build/pdf.mjs")
type HighlightBox = { id: string; left: number; top: number; width: number; height: number }
type TextBox = { text: string; left: number; top: number; width: number; height: number }

type Props = {
  jobId: string
  references: EvidenceRef[]
  activeEvidenceId: string | null
  onEvidenceSelect: (reference: EvidenceRef) => void
}

function sourcePdfUrl(jobId: string): string {
  return `/api/v1/analyses/${jobId}/source/content`
}

export function PdfSourceViewer({ jobId, references, activeEvidenceId, onEvidenceSelect }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [pdfJs, setPdfJs] = useState<PdfJs | null>(null)
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null)
  const [page, setPage] = useState(1)
  const [scale, setScale] = useState(1.2)
  const [size, setSize] = useState({ width: 0, height: 0 })
  const [boxes, setBoxes] = useState<HighlightBox[]>([])
  const [loadError, setLoadError] = useState("")
  const pageReferences = useMemo(
    () => references.filter((reference) => reference.kind === "pdf" && reference.page === page),
    [page, references],
  )

  useEffect(() => {
    let disposed = false
    let loadingTask: PDFDocumentLoadingTask | null = null
    void import("pdfjs-dist/legacy/build/pdf.mjs").then(async (module) => {
      module.GlobalWorkerOptions.workerSrc = pdfWorkerUrl
      const response = await fetch(sourcePdfUrl(jobId), {
        cache: "no-store",
      })
      if (!response.ok) throw new Error(`PDF 请求失败（${response.status}）`)
      const data = new Uint8Array(await response.arrayBuffer())
      if (!data.byteLength) throw new Error("PDF 响应为空")
      if (disposed) return
      loadingTask = module.getDocument({ data })
      const loaded = await loadingTask.promise
      if (!disposed) {
        setPdfJs(module)
        setDocument(loaded)
        setLoadError("")
      }
    }).catch((error: unknown) => {
      if (disposed) return
      console.error("PDF preview failed", error)
      setDocument(null)
      setLoadError(error instanceof Error ? error.message : "未知错误")
    })
    return () => {
      disposed = true
      void loadingTask?.destroy()
    }
  }, [jobId])

  useEffect(() => {
    const reference = references.find((item) => item.id === activeEvidenceId)
    if (reference?.page) setPage(reference.page)
  }, [activeEvidenceId, references])

  useEffect(() => {
    if (!document || !pdfJs || !canvasRef.current) return
    let cancelled = false
    let renderTask: { cancel: () => void; promise: Promise<unknown> } | null = null
    void document.getPage(page).then(async (pdfPage) => {
      if (cancelled || !canvasRef.current) return
      const viewport = pdfPage.getViewport({ scale })
      const outputScale = window.devicePixelRatio || 1
      const canvas = canvasRef.current
      canvas.width = Math.floor(viewport.width * outputScale)
      canvas.height = Math.floor(viewport.height * outputScale)
      canvas.style.width = `${viewport.width}px`
      canvas.style.height = `${viewport.height}px`
      setSize({ width: viewport.width, height: viewport.height })
      renderTask = pdfPage.render({
        canvas,
        viewport,
        transform: outputScale === 1 ? undefined : [outputScale, 0, 0, outputScale, 0, 0],
      })
      const textContent = await pdfPage.getTextContent()
      await renderTask.promise
      if (cancelled) return
      const textBoxes: TextBox[] = textContent.items.flatMap((item) => {
        if (!("str" in item) || !item.str) return []
        const transform = pdfJs.Util.transform(viewport.transform, item.transform)
        const height = Math.max(Math.hypot(transform[2], transform[3]), 8)
        return [{
          text: item.str,
          left: transform[4],
          top: transform[5] - height,
          width: Math.max(item.width * scale, 2),
          height,
        }]
      })
      setBoxes(pageReferences.flatMap((reference) => (
        matchHighlightBoxes(reference, textBoxes, viewport.width, viewport.height)
      )))
    }).catch((error: unknown) => {
      if (cancelled) return
      console.error("PDF page render failed", error)
      setBoxes([])
    })
    return () => {
      cancelled = true
      renderTask?.cancel()
    }
  }, [document, page, pageReferences, pdfJs, scale])

  const total = document?.numPages ?? 0
  return (
    <div className="pdf-source-viewer">
      <div className="source-toolbar">
        <button type="button" onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={page <= 1} aria-label="上一页"><ChevronLeft /></button>
        <span><strong>{page}</strong> / {total || "—"}</span>
        <button type="button" onClick={() => setPage((value) => Math.min(total, value + 1))} disabled={!total || page >= total} aria-label="下一页"><ChevronRight /></button>
        <span className="source-toolbar-separator" />
        <button type="button" onClick={() => setScale((value) => Math.max(0.7, value - 0.1))} aria-label="缩小"><Minus /></button>
        <span>{Math.round(scale * 100)}%</span>
        <button type="button" onClick={() => setScale((value) => Math.min(2.2, value + 0.1))} aria-label="放大"><Plus /></button>
      </div>
      <div className="pdf-stage app-scrollbar">
        {!document && !loadError && <div className="source-empty">正在加载原始 PDF…</div>}
        {loadError && (
          <div className="source-empty">
            <span>无法加载原始 PDF</span>
            <small>{loadError}</small>
          </div>
        )}
        <div className="pdf-page" style={{ width: size.width, height: size.height }}>
          <canvas ref={canvasRef} />
          {boxes.map((box, index) => {
            const reference = pageReferences.find((item) => item.id === box.id)
            return (
              <button
                key={`${box.id}-${index}`}
                type="button"
                className="pdf-highlight"
                data-active={activeEvidenceId === box.id}
                style={{ left: box.left, top: box.top, width: box.width, height: box.height }}
                onClick={() => reference && onEvidenceSelect(reference)}
                aria-label={`引用区域 ${box.id}`}
              >
                {activeEvidenceId === box.id && <span className="pdf-highlight-label">文本</span>}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function normalize(value: string): string {
  return value.replace(/\s+/g, "").toLocaleLowerCase()
}

function matchHighlightBoxes(
  reference: EvidenceRef,
  items: TextBox[],
  pageWidth: number,
  pageHeight: number,
): HighlightBox[] {
  if (reference.bbox) {
    const [x0, y0, x1, y1] = reference.bbox
    return [{
      id: reference.id,
      left: x0 / 1000 * pageWidth,
      top: y0 / 1000 * pageHeight,
      width: (x1 - x0) / 1000 * pageWidth,
      height: (y1 - y0) / 1000 * pageHeight,
    }]
  }
  const haystackParts: string[] = []
  const itemIndexes: number[] = []
  items.forEach((item, index) => {
    for (const character of normalize(item.text)) {
      haystackParts.push(character)
      itemIndexes.push(index)
    }
  })
  const haystack = haystackParts.join("")
  const candidates = [normalize(reference.excerpt).slice(0, 400)]
  candidates.push(...reference.excerpt.split("\n").map(normalize).filter((part) => part.length >= 16))
  const needle = candidates.find((candidate) => candidate.length >= 16 && haystack.includes(candidate))
  if (!needle) return []
  const start = haystack.indexOf(needle)
  const indexes = new Set(itemIndexes.slice(start, start + needle.length))
  const matched = [...indexes].map((index) => items[index]).sort((left, right) => left.top - right.top || left.left - right.left)
  const rows: TextBox[] = []
  matched.forEach((box) => {
    const row = rows.find((candidate) => Math.abs(candidate.top - box.top) < Math.max(4, box.height * 0.45))
    if (!row) rows.push({ ...box })
    else {
      const right = Math.max(row.left + row.width, box.left + box.width)
      row.left = Math.min(row.left, box.left)
      row.top = Math.min(row.top, box.top)
      row.width = right - row.left
      row.height = Math.max(row.height, box.height)
    }
  })
  return rows.map((box) => ({ id: reference.id, ...box }))
}
