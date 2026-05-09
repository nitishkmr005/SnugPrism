import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/layout/Navbar'
import ChatWidget from '@/components/chat/ChatWidget'
import Providers from '@/components/Providers'

export const metadata: Metadata = {
  title: 'SnugPrism — DS Interview Prep',
  description: 'AI-powered data science interview preparation',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Navbar />
          <main className="min-h-[calc(100vh-56px)]">{children}</main>
          <ChatWidget />
        </Providers>
      </body>
    </html>
  )
}
