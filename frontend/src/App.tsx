import * as Tabs from "@radix-ui/react-tabs"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useMemo, useRef, useState } from "react"
import { ReportWorkbench } from "@/components/ReportWorkbench"
import { ThemeToggle } from "@/components/ThemeToggle"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api, type Job } from "@/services/api"

function StatusPill({ job }: { job: Job }) {
  return <span className={`status status-${job.status}`}>{job.status}</span>
}

export default function App() {
  const client = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>()
  const [githubUrl, setGithubUrl] = useState("")
  const [language, setLanguage] = useState("zh-CN")
  const [notice, setNotice] = useState("")
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [settingsDraft, setSettingsDraft] = useState<Record<string, string>>({})
  const folderInput = useRef<HTMLInputElement>(null)

  const jobs = useQuery({ queryKey: ["jobs"], queryFn: api.jobs, refetchInterval: 2500 })
  const capabilities = useQuery({ queryKey: ["capabilities"], queryFn: api.capabilities })
  const selected = useMemo(() => jobs.data?.find((job) => job.id === selectedId), [jobs.data, selectedId])
  const report = useQuery({
    queryKey: ["report", selectedId], queryFn: () => api.report(selectedId!),
    enabled: Boolean(selectedId && selected?.status === "completed"),
  })

  useEffect(() => {
    if (selectedId === undefined && jobs.data?.length) setSelectedId(jobs.data[0].id)
  }, [jobs.data, selectedId])

  useEffect(() => {
    if (!selectedId || !selected || !["queued", "running"].includes(selected.status)) return
    const stream = new EventSource(`/api/v1/analyses/${selectedId}/events`)
    stream.addEventListener("progress", () => client.invalidateQueries({ queryKey: ["jobs"] }))
    stream.onerror = () => stream.close()
    return () => stream.close()
  }, [client, selected, selectedId])

  const createJob = useMutation({
    mutationFn: async (action: () => Promise<{ job_id: string }>) => action(),
    onSuccess: ({ job_id }) => {
      setSelectedId(job_id)
      setNotice("分析任务已进入队列。")
      client.invalidateQueries({ queryKey: ["jobs"] })
    },
    onError: (error) => setNotice(error.message),
  })

  const submitFolder = (files: FileList | null) => {
    if (!files?.length) return
    const data = new FormData()
    Array.from(files).forEach((file) => {
      data.append("files", file)
      data.append("paths", file.webkitRelativePath || file.name)
    })
    data.append("language", language)
    createJob.mutate(() => api.upload("folder", data))
  }

  const submitPdf = (file?: File) => {
    if (!file) return
    const data = new FormData()
    data.append("file", file)
    data.append("language", language)
    data.append("parser", "auto")
    createJob.mutate(() => api.upload("pdf", data))
  }

  const saveSettings = async () => {
    await api.updateSettings(settingsDraft)
    setSettingsDraft({})
    setSettingsOpen(false)
    client.invalidateQueries({ queryKey: ["capabilities"] })
    setNotice("本机配置已更新。")
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">R/C</span>
          <strong>Repo2Career</strong>
        </div>
        <div className="capability-strip">
          <span>CodeGraph {capabilities.data?.codegraph.available ? "可用" : "降级模式"}</span>
          <span>PDF {capabilities.data?.pdf_parser ?? "检查中"}</span>
          <span>DeepSeek {capabilities.data?.deepseek.configured ? "已配置" : "待配置"}</span>
        </div>
        <div className="header-actions"><ThemeToggle /><Button variant="secondary" onClick={() => setSettingsOpen(true)}>本机配置</Button></div>
      </header>

      <div className="workspace-grid">
        <aside className="history-panel">
          <div className="panel-heading"><div><p className="eyebrow">分析记录</p><span>{jobs.data?.length ?? 0} 个项目</span></div><button onClick={() => setSelectedId(null)}>新建</button></div>
          <div className="history-list">
            {jobs.data?.map((job) => (
              <button key={job.id} className={job.id === selectedId ? "history-item active" : "history-item"} onClick={() => setSelectedId(job.id)}>
                <div><strong>{String(job.source.name ?? job.source.repo ?? job.source_kind)}</strong><StatusPill job={job} /></div>
                <small>{new Date(job.created_at).toLocaleString()} · {job.progress}%</small>
              </button>
            ))}
            {!jobs.data?.length && <p className="empty-copy">尚无分析记录。从右侧选择一个项目来源。</p>}
          </div>
        </aside>

        <section className="main-stage">
          {!selected && (
            <div className="source-console">
              <div className="page-header">
                <div><p className="eyebrow">项目分析</p><h1>新建分析</h1><p>选择代码仓库、本地项目或 PDF，生成带有证据索引的求职报告。</p></div>
                <div className="language-row"><label>报告语言</label><select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="zh-CN">简体中文</option><option value="en">English</option></select></div>
              </div>
              <div className="analysis-layout">
                <Tabs.Root defaultValue="github" className="source-tabs">
                  <Tabs.List><Tabs.Trigger value="github">GitHub 仓库</Tabs.Trigger><Tabs.Trigger value="folder">本地目录</Tabs.Trigger><Tabs.Trigger value="pdf">PDF 文档</Tabs.Trigger></Tabs.List>
                  <Tabs.Content value="github" className="source-form">
                    <h2>分析 GitHub 仓库</h2><p>支持公开仓库，也可以在配置中添加 Token 访问私有仓库。</p>
                    <label htmlFor="github-url">仓库地址</label>
                    <Input id="github-url" placeholder="https://github.com/owner/repository" value={githubUrl} onChange={(event) => setGithubUrl(event.target.value)} />
                    <Button disabled={!githubUrl || createJob.isPending} onClick={() => createJob.mutate(() => api.github(githubUrl, language))}>开始分析</Button>
                  </Tabs.Content>
                  <Tabs.Content value="folder" className="source-form">
                    <h2>分析本地项目</h2><p>依赖目录、二进制文件和敏感配置会在上传前被排除。</p>
                    <input ref={(node) => { folderInput.current = node; node?.setAttribute("webkitdirectory", "") }} type="file" multiple hidden onChange={(event) => submitFolder(event.target.files)} />
                    <Button onClick={() => folderInput.current?.click()}>选择项目目录</Button>
                  </Tabs.Content>
                  <Tabs.Content value="pdf" className="source-form">
                    <h2>分析 PDF 文档</h2><p>适用于项目说明书、技术方案和产品文档。</p>
                    <div className="parser-note"><strong>当前解析器</strong><span>{capabilities.data?.mineru.configured ? "MinerU 云解析（失败自动回退 pypdf）" : "pypdf 本地解析，不支持 OCR"}</span></div>
                    <label className="file-button">选择 PDF<input type="file" accept="application/pdf" onChange={(event) => submitPdf(event.target.files?.[0])} /></label>
                  </Tabs.Content>
                </Tabs.Root>
                <aside className="analysis-summary"><h2>报告内容</h2><ul><li>完整业务流程与用户角色</li><li>技术栈、架构与关键调用链</li><li>工程难点与证据缺口</li><li>简历要点、STAR 与面试问题</li></ul><div className="privacy-note"><strong>安全边界</strong><p>项目代码只用于静态分析，不会被执行。</p></div></aside>
              </div>
              {notice && <p className="notice">{notice}</p>}
            </div>
          )}

          {selected && selected.status !== "completed" && (
            <div className="progress-console">
              <button className="text-link" onClick={() => setSelectedId(null)}>返回新建分析</button>
              <p className="eyebrow">当前分析</p><h1>{String(selected.source.name ?? selected.source.repo ?? selected.source_kind)}</h1>
              <div className="progress-track"><span style={{ width: `${selected.progress}%` }} /></div>
              <div className="progress-meta"><strong>{selected.stage}</strong><span>{selected.progress}%</span></div>
              <p>{selected.error || "正在建立证据链。长仓库和复杂 PDF 可能需要一些时间。"}</p>
              <div className="action-row">
                {["running", "queued"].includes(selected.status) && <Button variant="secondary" onClick={() => api.cancel(selected.id).then(() => client.invalidateQueries({ queryKey: ["jobs"] }))}>取消任务</Button>}
                {["failed", "interrupted", "cancelled"].includes(selected.status) && <Button onClick={() => api.retry(selected.id).then(() => client.invalidateQueries({ queryKey: ["jobs"] }))}>重试任务</Button>}
              </div>
            </div>
          )}
          {selected?.status === "completed" && report.data && <ReportWorkbench report={report.data} jobId={selected.id} />}
        </section>
      </div>

      <nav className="workspace-dock" aria-label="工作台导航">
        <button className="dock-item is-active" type="button" onClick={() => setSelectedId(null)}><i aria-hidden="true" />新建分析</button>
        <button className="dock-item" type="button" onClick={() => document.querySelector(".history-panel")?.scrollIntoView({ behavior: "smooth" })}><i aria-hidden="true" />分析记录</button>
        <button className="dock-item" type="button" onClick={() => setSettingsOpen(true)}><i aria-hidden="true" />本机配置</button>
      </nav>

      {settingsOpen && <div className="modal-backdrop" role="presentation" onMouseDown={() => setSettingsOpen(false)}><section className="settings-sheet" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}><p className="eyebrow">本机配置</p><h2>模型与解析服务</h2><label>DeepSeek API Key<Input type="password" placeholder="仅保存到本机 .env" onChange={(event) => setSettingsDraft({ ...settingsDraft, DEEPSEEK_API_KEY: event.target.value })} /></label><label>DeepSeek 模型<Input placeholder={capabilities.data?.deepseek.model} onChange={(event) => setSettingsDraft({ ...settingsDraft, DEEPSEEK_MODEL: event.target.value })} /></label><label>MinerU API Key<Input type="password" placeholder="留空时使用 pypdf" onChange={(event) => setSettingsDraft({ ...settingsDraft, MINERU_API_KEY: event.target.value })} /></label><div className="action-row"><Button variant="ghost" onClick={() => setSettingsOpen(false)}>关闭</Button><Button onClick={saveSettings}>保存配置</Button></div></section></div>}
    </main>
  )
}
