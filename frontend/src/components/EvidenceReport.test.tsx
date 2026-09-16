import { fireEvent, render, screen } from "@testing-library/react"
import { expect, test, vi } from "vitest"
import { EvidenceReport } from "./EvidenceReport"

test("keeps evidence navigation without exposing source locations in report text", () => {
  const onSelect = vi.fn()
  const reference = {
    id: "pdf-page-1-part-1",
    kind: "pdf" as const,
    path: "project.pdf",
    excerpt: "Grounded statement",
    page: 1,
  }
  render(
    <EvidenceReport
      report="Grounded statement <!-- evidence:pdf-page-1-part-1 -->"
      references={[reference]}
      activeEvidenceId={null}
      onEvidenceSelect={onSelect}
    />,
  )

  expect(screen.queryByText("第 1 页")).not.toBeInTheDocument()
  expect(screen.queryByText("project.pdf")).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole("button", { name: "查看证据" }))
  expect(onSelect).toHaveBeenCalledWith(reference)
})
