import { fireEvent, render, screen } from "@testing-library/react"
import { expect, test, vi } from "vitest"
import { EvidenceReport } from "./EvidenceReport"

test("renders evidence identifiers as location buttons", () => {
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
      report="Grounded statement [pdf-page-1-part-1]"
      references={[reference]}
      activeEvidenceId={null}
      onEvidenceSelect={onSelect}
    />,
  )

  fireEvent.click(screen.getByRole("button", { name: "第 1 页" }))
  expect(onSelect).toHaveBeenCalledWith(reference)
})
