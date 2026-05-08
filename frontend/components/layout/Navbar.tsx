'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BookOpen, Brain, Upload, BarChart2 } from 'lucide-react'

const links = [
  { href: '/prep', label: 'Prep', icon: Brain },
  { href: '/hub', label: 'Learn', icon: BookOpen },
  { href: '/ingest', label: 'Ingest', icon: Upload },
  { href: '/summary', label: 'Summary', icon: BarChart2 },
]

export default function Navbar() {
  const path = usePathname()
  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 max-w-7xl mx-auto gap-6">
        <Link href="/prep" className="font-bold text-lg tracking-tight text-primary">
          SnugPrism
        </Link>
        <nav className="flex gap-1">
          {links.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                path.startsWith(href)
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto text-xs text-muted-foreground hidden sm:block">
          DS Interview Prep
        </div>
      </div>
    </header>
  )
}
