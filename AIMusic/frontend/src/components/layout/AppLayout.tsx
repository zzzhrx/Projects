import { useState } from 'react'
import type { ReactNode } from 'react'
import StepIndicator from './StepIndicator'
import SettingsModal from '../settings/SettingsModal'

interface AppLayoutProps {
  children: ReactNode
  currentStep: number
}

export default function AppLayout({ children, currentStep }: AppLayoutProps) {
  const [showSettings, setShowSettings] = useState(false)

  return (
    <div className="min-h-screen bg-ink text-rice flex flex-col">
      <header className="border-b border-gold/30 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gold tracking-wider">
            古韵AI — 古风音乐创作工坊
          </h1>
          <button
            className="w-9 h-9 flex items-center justify-center rounded-lg border border-gold/30 text-gold hover:bg-gold/10 transition-colors"
            onClick={() => setShowSettings(true)}
            title="设置"
          >
            ⚙
          </button>
        </div>
      </header>

      <nav className="border-b border-gold/20 px-6 py-3">
        <div className="max-w-5xl mx-auto">
          <StepIndicator currentStep={currentStep} />
        </div>
      </nav>

      <main className="flex-1 px-6 py-8">
        <div className="max-w-5xl mx-auto">
          {children}
        </div>
      </main>

      <footer className="border-t border-gold/20 px-6 py-3 text-center text-rice-dark text-xs">
        古韵AI © 2026 — 词曲创作辅助工具
      </footer>

      <SettingsModal
        open={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  )
}
