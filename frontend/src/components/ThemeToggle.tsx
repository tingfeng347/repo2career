import { useEffect, useState } from "react"

type Theme = "light" | "dark"

function initialTheme(): Theme {
  try {
    const stored = window.localStorage.getItem("repo2career-theme")
    if (stored === "light" || stored === "dark") return stored
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  } catch {
    return "light"
  }
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(initialTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    try {
      window.localStorage.setItem("repo2career-theme", theme)
    } catch {
      // Storage can be unavailable in privacy-restricted browser contexts.
    }
  }, [theme])

  const next = theme === "light" ? "dark" : "light"
  return (
    <button
      type="button"
      className="theme-toggle"
      aria-label={`切换为${next === "dark" ? "暗色" : "亮色"}主题`}
      onClick={() => setTheme(next)}
    >
      <span className="theme-track" aria-hidden="true"><i /></span>
      <span>{theme === "light" ? "亮色" : "暗色"}</span>
    </button>
  )
}
