import * as Tabs from "@radix-ui/react-tabs"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useMemo, useState } from "react"
import { ArrowLeft, CircleAlert, FileText, Folder, Loader2, Plus, Settings, Sparkles, Trash2, X } from "lucide-react"
import { CodeReportWorkbench } from "@/components/CodeReportWorkbench"
import { DocumentReportWorkbench } from "@/components/DocumentReportWorkbench"
import { ThemeToggle } from "@/components/ThemeToggle"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { api, type Job } from "@/services/api"

const STATUS_LABELS: Record<Job["status"], string> = {
  queued: "等待中",
  running: "分析中",
  interrupted: "已中断",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
}

function StatusBadge({ job }: { job: Job }) {
  const tone: Record<Job["status"], string> = {
    queued: "bg-muted text-muted-foreground",
    running: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    interrupted: "bg-muted text-muted-foreground",
    completed: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    failed: "bg-red-500/10 text-red-600 dark:text-red-400",
    cancelled: "bg-muted text-muted-foreground",
  }
  return (
    <Badge variant="outline" className={cn("border-transparent font-normal", tone[job.status])}>
      {job.status === "running" && <Loader2 className="size-3 animate-spin" />}
      {STATUS_LABELS[job.status]}
    </Badge>
  )
}

function Capability({ name, ready }: { name: string; ready: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <span className={cn("size-1.5 rounded-full", ready ? "bg-emerald-500" : "bg-border")} />
      {name}
    </span>
  )
}

function sourceName(job: Job) {
  return String(job.source.name ?? job.source.repo ?? job.source.repository_url ?? job.source_kind)
}

export default function App() {
  const client = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>()
  const [githubUrl, setGithubUrl] = useState("")
  const [folderPath, setFolderPath] = useState("")
  const [language, setLanguage] = useState("zh-CN")
  const [notice, setNotice] = useState("")
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [deletingJob, setDeletingJob] = useState<Job | null>(null)
  const [settingsDraft, setSettingsDraft] = useState<Record<string, string>>({})

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

  const deleteJob = useMutation({
    mutationFn: (id: string) => api.delete(id),
    onSuccess: ({ job_id }) => {
      if (selectedId === job_id) {
        setSelectedId(jobs.data?.find((job) => job.id !== job_id)?.id ?? null)
      }
      client.removeQueries({ queryKey: ["report", job_id] })
      client.invalidateQueries({ queryKey: ["jobs"] })
      setDeletingJob(null)
      setNotice("项目记录和临时文件已删除。")
    },
    onError: (error) => {
      setDeletingJob(null)
      setNotice(error.message)
    },
  })

  const submitFolder = () => {
    const path = folderPath.trim()
    if (!path) return
    createJob.mutate(() => api.localFolder(path, language))
  }

  const submitPdf = (file?: File) => {
    if (!file) return
    const data = new FormData()
    data.append("file", file)
    data.append("language", language)
    data.append("parser", "auto")
    createJob.mutate(() => api.upload("pdf", data))
  }

  const submitMarkdown = (file?: File) => {
    if (!file) return
    const data = new FormData()
    data.append("file", file)
    data.append("language", language)
    createJob.mutate(() => api.upload("markdown", data))
  }

  const saveSettings = async () => {
    await api.updateSettings(settingsDraft)
    setSettingsDraft({})
    setSettingsOpen(false)
    client.invalidateQueries({ queryKey: ["capabilities"] })
    setNotice("本机配置已更新。")
  }

  return (
    <main className="flex h-full flex-col">
      <header className="grid h-13 shrink-0 grid-cols-[1fr_auto_1fr] items-center gap-6 border-b bg-background px-4 sm:px-6">
        <div className="flex items-center gap-2.5 justify-self-start">
          <span className="grid size-7 place-items-center rounded-md bg-foreground text-background">
            <Sparkles className="size-3.5" />
          </span>
          <span className="font-heading text-[15px] font-medium tracking-tight">Repo2Career</span>
          <Badge variant="secondary" className="font-mono text-[10px] font-normal">v0.1</Badge>
        </div>
        <div className="hidden items-center gap-4 md:flex">
          <Capability name="CodeGraph" ready={capabilities.data?.codegraph.available ?? false} />
          <Capability name="PDF" ready={Boolean(capabilities.data?.pdf_parser)} />
          <Capability name="DeepSeek" ready={capabilities.data?.deepseek.configured ?? false} />
        </div>
        <div className="flex items-center gap-1 justify-self-end">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={() => setSettingsOpen(true)}>
            <Settings />
            <span className="hidden sm:inline">配置</span>
          </Button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="flex w-60 shrink-0 flex-col border-r bg-background">
          <div className="flex items-center justify-between px-3 py-3">
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-medium">项目</span>
              <span className="font-mono text-[10px] text-muted-foreground">{jobs.data?.length ?? 0}</span>
            </div>
            <Button variant="ghost" size="icon-sm" aria-label="新建分析" onClick={() => setSelectedId(null)}>
              <Plus />
            </Button>
          </div>
          <div className="flex-1 space-y-1 overflow-y-auto px-2 pb-2">
            {jobs.data?.map((job) => (
              <div key={job.id} className="group relative">
                <button
                  onClick={() => setSelectedId(job.id)}
                  className={cn(
                    "flex w-full flex-col gap-1 rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-muted",
                    job.id === selectedId && "bg-muted",
                  )}
                >
                  <div className="flex w-full items-center justify-between gap-2">
                    <span className="min-w-0 truncate text-sm">{sourceName(job)}</span>
                    <StatusBadge job={job} />
                  </div>
                  <span className="pr-7 font-mono text-[10px] text-muted-foreground">
                    {new Date(job.created_at).toLocaleDateString()} · {job.progress}%
                  </span>
                </button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="absolute right-1 bottom-1 text-muted-foreground opacity-60 hover:text-destructive focus-visible:opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                  aria-label={`删除项目 ${sourceName(job)}`}
                  title="删除项目"
                  onClick={() => setDeletingJob(job)}
                >
                  <Trash2 />
                </Button>
              </div>
            ))}
            {!jobs.data?.length && (
              <p className="px-2.5 py-6 text-center text-xs leading-relaxed text-muted-foreground">
                还没有项目。<br />从右侧开始第一次分析。
              </p>
            )}
          </div>
          <div className="border-t px-3 py-3 font-mono text-[10px] text-muted-foreground">
            所有分析记录保存在本机
          </div>
        </aside>

        <section className={cn(
          "min-w-0 flex-1 overflow-y-auto",
          (["pdf", "markdown", "github", "folder"].includes(selected?.source_kind ?? ""))
            && selected?.status === "completed" && "hide-scrollbar lg:overflow-hidden",
        )}>
          {!selected && (
            <div className="mx-auto w-full max-w-4xl px-6 py-10">
              <div className="mb-6 flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">新建分析</p>
                  <h1 className="font-heading mt-1 text-3xl font-semibold tracking-tight">选择一个项目来源</h1>
                  <p className="mt-2 text-sm text-muted-foreground">我们会整理其中的技术证据、项目亮点和面试材料。</p>
                </div>
                <div className="flex items-center gap-2">
                  <Label htmlFor="report-language" className="text-xs">报告语言</Label>
                  <select
                    id="report-language"
                    value={language}
                    onChange={(event) => setLanguage(event.target.value)}
                    className="h-8 rounded-lg border border-input bg-transparent px-2 pr-6 text-sm text-foreground outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
                  >
                    <option value="zh-CN">简体中文</option>
                    <option value="en">English</option>
                  </select>
                </div>
              </div>

              <Card>
                <Tabs.Root defaultValue="github" className="w-full">
                  <Tabs.List className="hide-scrollbar flex items-center gap-1 overflow-x-auto border-b px-3">
                    <Tabs.Trigger
                      value="github"
                      className="inline-flex items-center justify-center border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground outline-none transition-colors hover:text-foreground data-[state=active]:border-foreground data-[state=active]:text-foreground"
                    >
                      GitHub 仓库
                    </Tabs.Trigger>
                    <Tabs.Trigger
                      value="folder"
                      className="inline-flex items-center justify-center border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground outline-none transition-colors hover:text-foreground data-[state=active]:border-foreground data-[state=active]:text-foreground"
                    >
                      本地目录
                    </Tabs.Trigger>
                    <Tabs.Trigger
                      value="pdf"
                      className="inline-flex items-center justify-center border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground outline-none transition-colors hover:text-foreground data-[state=active]:border-foreground data-[state=active]:text-foreground"
                    >
                      PDF 文档
                    </Tabs.Trigger>
                    <Tabs.Trigger
                      value="markdown"
                      className="inline-flex items-center justify-center border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground outline-none transition-colors hover:text-foreground data-[state=active]:border-foreground data-[state=active]:text-foreground"
                    >
                      Markdown
                    </Tabs.Trigger>
                  </Tabs.List>

                  <Tabs.Content value="github" className="space-y-3 px-4 py-4">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">GitHub 仓库</p>
                      <p className="text-xs text-muted-foreground">输入公开仓库地址；私有仓库可在配置中添加访问令牌。</p>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="github-url">仓库地址</Label>
                      <Input
                        id="github-url"
                        placeholder="https://github.com/owner/repository"
                        value={githubUrl}
                        onChange={(event) => setGithubUrl(event.target.value)}
                      />
                    </div>
                    <Button disabled={!githubUrl || createJob.isPending} onClick={() => createJob.mutate(() => api.github(githubUrl, language))}>
                      {createJob.isPending ? "正在提交…" : "开始分析"}
                    </Button>
                  </Tabs.Content>

                  <Tabs.Content value="folder" className="space-y-3 px-4 py-4">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">本地目录</p>
                      <p className="text-xs text-muted-foreground">直接读取本机目录，不会上传或复制文件；依赖、二进制和敏感配置会被跳过。</p>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="local-folder-path">本地目录路径</Label>
                      <Input
                        id="local-folder-path"
                        placeholder="/Users/name/projects/my-project"
                        value={folderPath}
                        onChange={(event) => setFolderPath(event.target.value)}
                      />
                    </div>
                    <Button disabled={!folderPath.trim() || createJob.isPending} onClick={submitFolder}>
                      <Folder /> {createJob.isPending ? "正在提交…" : "开始分析"}
                    </Button>
                  </Tabs.Content>

                  <Tabs.Content value="pdf" className="space-y-3 px-4 py-4">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">PDF 文档</p>
                      <p className="text-xs text-muted-foreground">适用于项目说明书、技术方案、复盘材料与产品文档。</p>
                    </div>
                    <div className="rounded-lg border bg-muted/50 px-3 py-2 text-xs">
                      <span className="font-medium">当前解析器</span>{" "}
                      <span className="text-muted-foreground">
                        {capabilities.data?.mineru.configured ? "MinerU 云解析（失败自动回退 pypdf）" : "pypdf 本地解析，不支持 OCR"}
                      </span>
                    </div>
                    <label className="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-lg border border-input px-2.5 text-sm font-medium transition-colors hover:bg-muted">
                      <FileText className="size-3.5" /> 选择 PDF
                      <input type="file" accept="application/pdf" className="hidden" onChange={(event) => submitPdf(event.target.files?.[0])} />
                    </label>
                  </Tabs.Content>

                  <Tabs.Content value="markdown" className="space-y-3 px-4 py-4">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">Markdown 文档</p>
                      <p className="text-xs text-muted-foreground">直接读取 UTF-8 Markdown 并交给大模型生成报告，不经过 PDF 解析器。</p>
                    </div>
                    <label className="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-lg border border-input px-2.5 text-sm font-medium transition-colors hover:bg-muted">
                      <FileText className="size-3.5" /> 选择 Markdown
                      <input
                        type="file"
                        accept=".md,text/markdown,text/plain"
                        className="hidden"
                        onChange={(event) => submitMarkdown(event.target.files?.[0])}
                      />
                    </label>
                  </Tabs.Content>
                </Tabs.Root>
              </Card>

              <Card className="mt-4">
                <CardHeader>
                  <CardTitle>报告包含</CardTitle>
                  <CardDescription>仅静态读取，不执行代码</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="space-y-1 border-l-2 border-border pl-3">
                      <p className="text-sm font-medium">项目解读</p>
                      <p className="text-xs text-muted-foreground">业务流程、技术栈与关键调用链</p>
                    </div>
                    <div className="space-y-1 border-l-2 border-border pl-3">
                      <p className="text-sm font-medium">工程亮点</p>
                      <p className="text-xs text-muted-foreground">技术难点、关键决策与证据边界</p>
                    </div>
                    <div className="space-y-1 border-l-2 border-border pl-3">
                      <p className="text-sm font-medium">求职材料</p>
                      <p className="text-xs text-muted-foreground">简历要点、STAR 故事与面试问题</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {notice && (
                <div className="mt-4 flex items-center gap-2 rounded-lg border bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
                  <CircleAlert className="size-3.5" />
                  {notice}
                </div>
              )}
            </div>
          )}

          {selected && selected.status !== "completed" && (
            <div className="mx-auto flex w-full max-w-xl flex-col items-center px-6 py-16 text-center">
              <Button variant="ghost" size="sm" className="mb-8 self-start" onClick={() => setSelectedId(null)}>
                <ArrowLeft /> 返回新建分析
              </Button>
              <div className="mb-6 grid size-16 place-items-center rounded-full border">
                <Loader2 className="size-5 animate-spin text-muted-foreground" />
              </div>
              <p className="text-xs font-medium text-muted-foreground">正在分析</p>
              <h1 className="font-heading mt-2 text-3xl font-semibold tracking-tight break-words">{sourceName(selected)}</h1>
              <div className="mt-8 h-1 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full bg-foreground transition-[width] duration-300" style={{ width: `${selected.progress}%` }} />
              </div>
              <div className="mt-2 flex w-full justify-between font-mono text-[10px] text-muted-foreground uppercase">
                <span>{selected.stage}</span>
                <span>{selected.progress}%</span>
              </div>
              <p className="mt-6 text-sm text-muted-foreground">{selected.error || "正在建立证据链。大型仓库和复杂文档可能需要一些时间。"}</p>
              <div className="mt-6 flex gap-2">
                {["running", "queued"].includes(selected.status) && (
                  <Button variant="secondary" onClick={() => api.cancel(selected.id).then(() => client.invalidateQueries({ queryKey: ["jobs"] }))}>取消任务</Button>
                )}
                {["failed", "interrupted", "cancelled"].includes(selected.status) && (
                  <Button onClick={() => api.retry(selected.id).then(() => client.invalidateQueries({ queryKey: ["jobs"] }))}>重试任务</Button>
                )}
              </div>
            </div>
          )}

          {selected?.status === "completed" && report.data && (
            selected.source_kind === "pdf" || selected.source_kind === "markdown"
              ? <DocumentReportWorkbench report={report.data} jobId={selected.id} sourceKind={selected.source_kind} />
              : <CodeReportWorkbench report={report.data} jobId={selected.id} />
          )}
        </section>
      </div>

      {deletingJob && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 px-4" onMouseDown={() => !deleteJob.isPending && setDeletingJob(null)}>
          <section
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-project-title"
            aria-describedby="delete-project-description"
            className="w-full max-w-sm rounded-lg border bg-card p-5 shadow-xl"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="delete-project-title" className="text-lg font-semibold">删除项目？</h2>
                <p id="delete-project-description" className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  “{sourceName(deletingJob)}”的分析记录、报告和本应用创建的临时文件将从本机永久删除。原始本地目录不会被删除。
                </p>
              </div>
              <Button variant="ghost" size="icon-sm" aria-label="关闭删除确认" disabled={deleteJob.isPending} onClick={() => setDeletingJob(null)}>
                <X />
              </Button>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" disabled={deleteJob.isPending} onClick={() => setDeletingJob(null)}>取消</Button>
              <Button variant="destructive" disabled={deleteJob.isPending} onClick={() => deleteJob.mutate(deletingJob.id)}>
                {deleteJob.isPending ? <><Loader2 className="animate-spin" /> 正在删除</> : <><Trash2 /> 删除项目</>}
              </Button>
            </div>
          </section>
        </div>
      )}

      {settingsOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm" onMouseDown={() => setSettingsOpen(false)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
            className="flex h-full w-full max-w-md flex-col overflow-y-auto border-l bg-card p-6 shadow-xl"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground">本机配置</p>
                <h2 id="settings-title" className="font-heading mt-1 text-2xl font-semibold">模型与解析服务</h2>
              </div>
              <Button variant="ghost" size="icon-sm" aria-label="关闭配置" onClick={() => setSettingsOpen(false)}>
                <X />
              </Button>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">密钥只写入本机环境，不会显示在报告中。</p>
            <div className="mt-6 space-y-5">
              <div className="space-y-1.5">
                <Label>DeepSeek API Key</Label>
                <Input type="password" placeholder="仅保存到本机 .env" onChange={(event) => setSettingsDraft({ ...settingsDraft, DEEPSEEK_API_KEY: event.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label>DeepSeek 模型</Label>
                <Input placeholder={capabilities.data?.deepseek.model} onChange={(event) => setSettingsDraft({ ...settingsDraft, DEEPSEEK_MODEL: event.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label>MinerU API Key</Label>
                <Input type="password" placeholder="留空时使用 pypdf" onChange={(event) => setSettingsDraft({ ...settingsDraft, MINERU_API_KEY: event.target.value })} />
              </div>
            </div>
            <div className="mt-auto flex justify-end gap-2 pt-6">
              <Button variant="ghost" onClick={() => setSettingsOpen(false)}>取消</Button>
              <Button onClick={saveSettings}>保存配置</Button>
            </div>
          </section>
        </div>
      )}
    </main>
  )
}
