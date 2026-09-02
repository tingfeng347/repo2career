import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"

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
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      aria-label={`切换为${next === "dark" ? "暗色" : "亮色"}主题`}
      onClick={() => setTheme(next)}
    >
      {theme === "light" ? <Moon /> : <Sun />}
    </Button>
  )
}
