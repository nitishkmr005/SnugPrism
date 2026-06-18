'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { BookOpen, Brain, Upload, BarChart2, Moon, Sun, Sparkles } from 'lucide-react'

const links = [
  { href: '/prep', label: 'Prep', icon: Brain },
  { href: '/hub', label: 'Learn', icon: BookOpen },
  { href: '/ingest', label: 'Ingest', icon: Upload },
  { href: '/summary', label: 'Summary', icon: BarChart2 },
]

export default function Navbar() {
  const path = usePathname()
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const saved = window.localStorage.getItem('snugprism-theme')
    const initial =
      saved === 'dark' || saved === 'light'
        ? saved
        : window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
    setTheme(initial)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    window.localStorage.setItem('snugprism-theme', theme)
  }, [theme])

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/75">
      <div className="flex h-14 items-center px-4 max-w-7xl mx-auto gap-5">
        {/* Logo */}
        <Link
          href="/prep"
          className="flex items-center gap-2 font-bold text-base tracking-tight text-primary shrink-0 group"
        >
          <span className="flex items-center justify-center h-7 w-7 rounded-lg bg-primary text-primary-foreground group-hover:scale-105 transition-transform">
            <Sparkles className="h-3.5 w-3.5" />
          </span>
          SnugPrism
        </Link>

        {/* Nav links */}
        <nav className="flex gap-0.5">
          {links.map(({ href, label, icon: Icon }) => {
            const active = path.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'text-primary bg-primary/8'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
                {active && (
                  <span className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-primary" />
                )}
              </Link>
            )
          })}
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-muted-foreground hidden sm:block font-medium tracking-wide">
            DS Interview Prep
          </span>
          <button
            type="button"
            onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border/60 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            aria-label="Toggle theme"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </header>
  )
}
