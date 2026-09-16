import { useEffect, useMemo, useState } from "react"
import { Copy, Plus, Save, Trash2, X } from "lucide-react"
import { api, type ReportTemplate } from "@/services/api"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"

type Props = {
  templates: ReportTemplate[]
  selectedId: string
  onSelect: (id: string) => void
  onChanged: () => Promise<unknown> | void
  onClose: () => void
}

const EMPTY = { id: undefined as string | undefined, name: "", description: "", body: "" }

export function ReportTemplateManager({ templates, selectedId, onSelect, onChanged, onClose }: Props) {
  const selected = useMemo(
    () => templates.find((template) => template.id === selectedId) ?? templates[0],
    [selectedId, templates],
  )
  const [draft, setDraft] = useState(EMPTY)
  const [message, setMessage] = useState("")
  const [saving, setSaving] = useState(false)

  const load = (template: ReportTemplate, clone = false) => {
    setDraft({
      id: clone || template.builtin ? undefined : template.id,
      name: clone ? `${template.name} - 副本` : template.name,
      description: template.description,
      body: template.body,
    })
    setMessage("")
  }

  useEffect(() => {
    if (selected) load(selected)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.id])

  const builtinPreview = Boolean(selected?.builtin && !draft.id && draft.name === selected.name)

  const save = async () => {
    if (!draft.name.trim() || draft.body.trim().length < 40) {
      setMessage("模板名称不能为空，正文至少需要 40 个字符。")
      return
    }
    setSaving(true)
    try {
      const saved = await api.saveTemplate({ ...draft, name: draft.name.trim(), body: draft.body.trim() })
      await onChanged()
      onSelect(saved.id)
      setDraft({ id: saved.id, name: saved.name, description: saved.description, body: saved.body })
      setMessage("模板已保存。")
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "模板保存失败")
    } finally {
      setSaving(false)
    }
  }

  const remove = async () => {
    if (!draft.id) return
    try {
      await api.deleteTemplate(draft.id)
      await onChanged()
      onSelect("career-deep-dive")
      setMessage("自定义模板已删除。")
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "模板删除失败")
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4" onMouseDown={onClose}>
      <section className="grid h-[min(780px,92vh)] w-full max-w-6xl grid-cols-[260px_1fr] overflow-hidden rounded-xl border bg-card shadow-2xl" onMouseDown={(event) => event.stopPropagation()}>
        <aside className="flex min-h-0 flex-col border-r">
          <div className="border-b p-4">
            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="text-xs text-muted-foreground">报告生成</p>
                <h2 className="font-heading text-lg font-semibold">模板管理</h2>
              </div>
              <Button variant="ghost" size="icon-sm" aria-label="关闭模板管理" onClick={onClose}><X /></Button>
            </div>
            <Button className="mt-3 w-full" variant="secondary" onClick={() => { setDraft(EMPTY); setMessage("") }}><Plus /> 新建空白模板</Button>
          </div>
          <div className="min-h-0 flex-1 space-y-1 overflow-y-auto p-2">
            {templates.map((template) => (
              <button
                key={template.id}
                type="button"
                className="w-full rounded-lg px-3 py-2 text-left hover:bg-muted data-[active=true]:bg-muted"
                data-active={template.id === selectedId}
                onClick={() => { onSelect(template.id); load(template) }}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium">{template.name}</span>
                  {template.builtin && <span className="text-[10px] text-muted-foreground">内置</span>}
                </div>
                <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">{template.description || "自定义 Markdown 报告结构"}</p>
              </button>
            ))}
          </div>
        </aside>

        <div className="flex min-h-0 flex-col">
          <header className="flex items-center justify-between gap-3 border-b px-5 py-3">
            <div>
              <p className="text-sm font-medium">{draft.id ? "编辑自定义模板" : builtinPreview ? "内置模板预览" : "新建自定义模板"}</p>
              <p className="text-xs text-muted-foreground">Markdown 决定章节、标题层级、表格和流程图要求；系统仍强制保留证据引用。</p>
            </div>
            <div className="flex gap-2">
              {builtinPreview && selected && <Button variant="secondary" onClick={() => load(selected, true)}><Copy /> 基于此模板新建</Button>}
              {draft.id && <Button variant="ghost" className="text-destructive" onClick={remove}><Trash2 /> 删除</Button>}
              {!builtinPreview && <Button onClick={save} disabled={saving}><Save /> {saving ? "保存中…" : "保存模板"}</Button>}
            </div>
          </header>
          <div className="grid min-h-0 flex-1 grid-rows-[auto_1fr] gap-4 overflow-hidden p-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="template-name">模板名称</Label>
                <Input id="template-name" value={draft.name} disabled={builtinPreview} onChange={(event) => setDraft({ ...draft, name: event.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="template-description">说明</Label>
                <Input id="template-description" value={draft.description} disabled={builtinPreview} onChange={(event) => setDraft({ ...draft, description: event.target.value })} />
              </div>
            </div>
            <div className="flex min-h-0 flex-col gap-1.5">
              <Label htmlFor="template-body">Markdown 模板正文</Label>
              <textarea
                id="template-body"
                value={draft.body}
                readOnly={builtinPreview}
                onChange={(event) => setDraft({ ...draft, body: event.target.value })}
                className="min-h-0 flex-1 resize-none rounded-lg border border-input bg-background p-4 font-mono text-xs leading-6 outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                spellCheck={false}
              />
              <div className="flex justify-between text-[11px] text-muted-foreground">
                <span>可使用 <code>{"{{project_name}}"}</code> 占位符。</span>
                <span>{draft.body.length.toLocaleString()} 字符</span>
              </div>
              {message && <p className="text-xs text-muted-foreground">{message}</p>}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
