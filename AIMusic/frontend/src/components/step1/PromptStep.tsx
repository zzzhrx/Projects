import { useState } from 'react'
import { useMusicStore, type PromptVersion } from '../../store/musicStore'
import { api } from '../../services/api'
import PromptHistoryDrawer from '../common/PromptHistoryDrawer'

export default function PromptStep() {
  const {
    originalPrompt, optimizedPrompt, finalPrompt, sessionId, promptVersions,
    setOriginalPrompt, setOptimizedPrompt, setFinalPrompt, setSessionId, addPromptVersion,
    setStep, setLoading, setError, loading,
  } = useMusicStore()

  const [editedPrompt, setEditedPrompt] = useState('')
  const [showHistory, setShowHistory] = useState(false)
  const [showOptimized, setShowOptimized] = useState(false)

  const handleOptimize = async () => {
    if (!originalPrompt.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.optimizePrompt(originalPrompt, 'prompt', sessionId)
      const optimized = result.optimized_prompt || result.content || ''
      if (result.session_id) {
        setSessionId(result.session_id)
      }
      setOptimizedPrompt(optimized)
      setEditedPrompt(optimized)
      setShowOptimized(true)
      const version: PromptVersion = {
        id: crypto.randomUUID(),
        step: 'prompt',
        type: 'ai_optimized',
        content: optimized,
        timestamp: new Date().toISOString(),
        parentVersionId: null,
      }
      addPromptVersion(version)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI优化失败')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickSuggest = async () => {
    const text = showOptimized ? editedPrompt : originalPrompt
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.quickSuggest(text, '古风音乐提示词润色')
      const suggested = result.suggestion || result.content || ''
      setOptimizedPrompt(suggested)
      setEditedPrompt(suggested)
      setShowOptimized(true)
      const version: PromptVersion = {
        id: crypto.randomUUID(),
        step: 'prompt',
        type: 'ai_optimized',
        content: suggested,
        timestamp: new Date().toISOString(),
        parentVersionId: null,
        note: '快速润色',
      }
      addPromptVersion(version)
    } catch (err) {
      setError(err instanceof Error ? err.message : '快速润色失败')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    const content = showOptimized ? editedPrompt : originalPrompt
    if (!content.trim()) return
    setFinalPrompt(content)
    if (showOptimized && editedPrompt !== optimizedPrompt) {
      const version: PromptVersion = {
        id: crypto.randomUUID(),
        step: 'prompt',
        type: 'human_modified',
        content: editedPrompt,
        timestamp: new Date().toISOString(),
        parentVersionId: null,
      }
      addPromptVersion(version)
      try {
        await api.saveHumanModified('prompt', editedPrompt, sessionId)
      } catch {
        // Keep local history even if the backend history write fails.
      }
    }
    setStep(1)
  }

  const handleRestore = (version: PromptVersion) => {
    setEditedPrompt(version.content)
    setOptimizedPrompt(version.content)
    setShowOptimized(true)
    const restoredVersion: PromptVersion = {
      id: crypto.randomUUID(),
      step: 'prompt',
      type: 'restored',
      content: version.content,
      timestamp: new Date().toISOString(),
      parentVersionId: version.id,
      note: `回溯至 ${version.timestamp}`,
    }
    addPromptVersion(restoredVersion)
    setShowHistory(false)
  }

  return (
    <div className="flex flex-col gap-6 py-8">
      <div className="text-center mb-2">
        <h2 className="text-2xl text-gold font-bold mb-2">提示词创作</h2>
        <p className="text-rice-dark text-sm">描述你想要创作的古风音乐，AI将助你润色优化</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <label className="block text-gold text-sm font-medium mb-3">原始提示词</label>
            <textarea
              className="w-full h-40 bg-ink border border-gold/20 rounded-lg p-4 text-rice placeholder:text-rice-dark/50 focus:outline-none focus:border-gold/50 resize-none"
              placeholder="描述你想要创作的古风音乐..."
              value={originalPrompt}
              onChange={(e) => setOriginalPrompt(e.target.value)}
            />
            <div className="flex gap-3 mt-4">
              <button
                className="px-6 py-2.5 bg-gold hover:bg-gold-light text-ink rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleOptimize}
                disabled={!originalPrompt.trim() || loading}
              >
                {loading ? '优化中...' : 'AI优化'}
              </button>
              <button
                className="px-6 py-2.5 border border-gold/40 text-gold hover:bg-gold/10 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleQuickSuggest}
                disabled={!originalPrompt.trim() && !editedPrompt.trim() || loading}
              >
                快速润色
              </button>
            </div>
          </div>

          {showOptimized && (
            <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
              <label className="block text-gold text-sm font-medium mb-3">优化结果（可编辑）</label>
              <textarea
                className="w-full h-40 bg-ink border border-gold/20 rounded-lg p-4 text-rice placeholder:text-rice-dark/50 focus:outline-none focus:border-gold/50 resize-none"
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
              />
            </div>
          )}

          <div className="flex justify-end">
            <button
              className="px-8 py-3 bg-vermilion hover:bg-vermilion-light text-rice rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleConfirm}
              disabled={!originalPrompt.trim() || loading}
            >
              确认提示词
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <h3 className="text-gold text-sm font-medium mb-3">当前提示词</h3>
            <p className="text-rice text-sm leading-relaxed">
              {finalPrompt || originalPrompt || '尚未输入提示词'}
            </p>
          </div>

          <button
            className="w-full px-4 py-3 border border-gold/30 text-gold hover:bg-gold/10 rounded-lg transition-colors text-sm"
            onClick={() => setShowHistory(true)}
          >
            查看提示词历史 ({promptVersions.length})
          </button>

          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <h3 className="text-gold text-sm font-medium mb-3">创作提示</h3>
            <ul className="text-rice-dark text-xs space-y-2 leading-relaxed">
              <li>• 描述音乐意境，如"月下独酌、清风拂柳"</li>
              <li>• 指定情感基调，如"婉约、豪放、清幽"</li>
              <li>• 参考古诗词意象，如"大漠孤烟、小桥流水"</li>
              <li>• 说明乐器偏好，如"以古筝为主旋律"</li>
            </ul>
          </div>
        </div>
      </div>

      <PromptHistoryDrawer
        open={showHistory}
        onClose={() => setShowHistory(false)}
        versions={promptVersions}
        onRestore={handleRestore}
      />
    </div>
  )
}
