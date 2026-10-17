"use client"

import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react"
import * as React from "react"
import { Toaster as Sonner, type ToasterProps } from "sonner"

const Toaster = ({ ...props }: ToasterProps) => {
  const readTheme = () => document.documentElement.dataset.theme === "dark" ? "dark" : "light"
  const [theme, setTheme] = React.useState<"light" | "dark">(readTheme)
  React.useEffect(() => {
    const update = () => setTheme(readTheme())
    window.addEventListener("dashboard:theme", update)
    update()
    return () => window.removeEventListener("dashboard:theme", update)
  }, [])

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      style={
        {
          "--normal-bg": "var(--ui-background)",
          "--normal-text": "var(--ui-foreground)",
          "--normal-border": "var(--ui-border)",
          "--border-radius": "var(--radius-lg)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

export { Toaster }
