import { useState } from 'react'
import type { PromptVersion } from '../../store/musicStore'

interface PromptHistoryDrawerProps {
  open: boolean
  onClose: () => void
  versions: PromptVersion[]
  onRestore: (version: PromptVersion) => void
}

const typeConfig: Record<string, { label: string; color: string }> = {
  original: { label: '原始', color: 'bg-blue-500/20 text-blue-300' },
  ai_optimized: { label: 'AI优化', color: 'bg-purple-500/20 text-purple-300' },
  human_modified: { label: '人工修改', color: 'bg-green-500/20 text-green-300' },
  restored: { label: '回溯', color: 'bg-orange-500/20 text-orange-300' },
}

export default function PromptHistoryDrawer({ open, onClose, versions, onRestore }: PromptHistoryDrawerProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const handleExport = () => {
    const data = JSON.stringify(versions, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'prompt_history.json'
    a.click()
    // Delay revoke to let browser start the download
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const sorted = [...versions].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={onClose}
        />
      )}

      <div
        className={`fixed top-0 right-0 h-full w-96 bg-ink border-l border-gold/20 z-50 transform transition-transform duration-300 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-5 border-b border-gold/20">
          <h3 className="text-gold font-medium">提示词历史</h3>
          <div className="flex items-center gap-3">
            <button
              className="text-rice-dark hover:text-rice text-xs transition-colors"
              onClick={handleExport}
            >
              导出历史
            </button>
            <button
              className="text-rice-dark hover:text-rice text-lg transition-colors"
              onClick={onClose}
            >
              ✕
            </button>
          </div>
        </div>

        <div className="overflow-y-auto h-[calc(100%-68px)] p-4 space-y-3">
          {sorted.length === 0 ? (
            <p className="text-rice-dark text-sm text-center py-8">暂无历史记录</p>
          ) : (
            sorted.map((version) => {
              const config = typeConfig[version.type] || typeConfig.original
              const isExpanded = expandedId === version.id

              return (
                <div
                  key={version.id}
                  className="bg-ink-light border border-gold/10 rounded-lg overflow-hidden"
                >
                  <div
                    className="flex items-center justify-between p-3 cursor-pointer hover:bg-gold/5 transition-colors"
                    onClick={() => setExpandedId(isExpanded ? null : version.id)}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${config.color}`}>
                        [{config.label}]
                      </span>
                      <span className="text-rice-dark text-xs">
                        {new Date(version.timestamp).toLocaleString('zh-CN')}
                      </span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="px-3 pb-3">
                      <p className="text-rice text-sm leading-relaxed whitespace-pre-wrap mb-3">
                        {version.content}
                      </p>
                      {version.note && (
                        <p className="text-rice-dark text-xs mb-3">备注：{version.note}</p>
                      )}
                      <button
                        className="px-4 py-1.5 bg-gold/20 text-gold hover:bg-gold/30 rounded text-xs transition-colors"
                        onClick={() => onRestore(version)}
                      >
                        恢复此版本
                      </button>
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>
    </>
  )
}
