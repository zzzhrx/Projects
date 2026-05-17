import { useState, useEffect } from 'react'

interface SettingsModalProps {
  open: boolean
  onClose: () => void
}

export default function SettingsModal({ open, onClose }: SettingsModalProps) {
  const [deepseekKey, setDeepseekKey] = useState('')
  const [qwenKey, setQwenKey] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setDeepseekKey(localStorage.getItem('deepseek_api_key') || '')
      setQwenKey(localStorage.getItem('qwen_api_key') || '')
      setSaved(false)
    }
  }, [open])

  const handleSave = async () => {
    localStorage.setItem('deepseek_api_key', deepseekKey)
    localStorage.setItem('qwen_api_key', qwenKey)
    try {
      const resp = await fetch('/api/settings/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deepseek_api_key: deepseekKey,
          qwen_api_key: qwenKey,
        }),
      })
      if (resp.ok) {
        setSaved(true)
      } else {
        setError('保存失败，请检查后端服务')
      }
    } catch {
      setError('无法连接后端，Key 仅保存在本地')
    }
    setTimeout(() => {
      setSaved(false)
      setError('')
    }, 3000)
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />
      <div className="relative bg-ink-light border border-gold/30 rounded-2xl w-full max-w-md p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-gold text-lg font-medium">设置</h3>
            <button
              className="text-rice-dark hover:text-rice text-lg transition-colors"
              onClick={onClose}
            >
              ✕
            </button>
          </div>

          <div className="space-y-5">
            <div>
              <label className="block text-rice text-sm mb-2">DeepSeek API Key</label>
              <input
                type="password"
                className="w-full bg-ink border border-gold/20 rounded-lg px-4 py-2.5 text-rice placeholder:text-rice-dark/50 focus:outline-none focus:border-gold/50 text-sm"
                placeholder="输入DeepSeek API Key"
                value={deepseekKey}
                onChange={(e) => setDeepseekKey(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-rice text-sm mb-2">千问 API Key</label>
              <input
                type="password"
                className="w-full bg-ink border border-gold/20 rounded-lg px-4 py-2.5 text-rice placeholder:text-rice-dark/50 focus:outline-none focus:border-gold/50 text-sm"
                placeholder="输入千问 API Key"
                value={qwenKey}
                onChange={(e) => setQwenKey(e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 mt-6">
            {saved && (
              <span className="text-green-400 text-sm">已保存</span>
            )}
            {error && (
              <span className="text-vermilion-light text-sm">{error}</span>
            )}
            <button
              className="px-5 py-2 border border-gold/30 text-gold hover:bg-gold/10 rounded-lg text-sm transition-colors"
              onClick={onClose}
            >
              取消
            </button>
            <button
              className="px-5 py-2 bg-gold hover:bg-gold-light text-ink rounded-lg text-sm font-medium transition-colors"
              onClick={handleSave}
            >
              保存
            </button>
          </div>
        </div>
      </div>
  )
}
