import { useState } from 'react'
import { useMusicStore, type PromptVersion } from '../../store/musicStore'
import { api } from '../../services/api'
import ScoreDisplay from './ScoreDisplay'
import AudioPlayer from './AudioPlayer'
import PromptHistoryDrawer from '../common/PromptHistoryDrawer'

export default function ScoreStep() {
  const {
    finalLyrics, scorePrompt, selectedInstrument,
    vocalAbc, instrumentAbc, sessionId,
    scorePromptVersions,
    setScorePrompt, setOptimizedScorePrompt, setSelectedInstrument,
    setVocalAbc, setInstrumentAbc, addScorePromptVersion,
    setStep, setLoading, setError, loading,
  } = useMusicStore()

  const [editedScorePrompt, setEditedScorePrompt] = useState('')
  const [showOptimized, setShowOptimized] = useState(false)
  const [activeTab, setActiveTab] = useState<'vocal' | 'instrument'>('vocal')
  const [showHistory, setShowHistory] = useState(false)

  const handleOptimizeScorePrompt = async () => {
    if (!scorePrompt.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.optimizeScorePrompt(scorePrompt, sessionId)
      const optimized = result.optimized_prompt || result.content || ''
      setOptimizedScorePrompt(optimized)
      setEditedScorePrompt(optimized)
      setShowOptimized(true)
      const version: PromptVersion = {
        id: crypto.randomUUID(),
        step: 'score',
        type: 'ai_optimized',
        content: optimized,
        timestamp: new Date().toISOString(),
        parentVersionId: null,
      }
      addScorePromptVersion(version)
    } catch (err) {
      setError(err instanceof Error ? err.message : '优化曲谱提示词失败')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateScore = async () => {
    if (!finalLyrics.trim()) return
    setLoading(true)
    setError(null)
    try {
      const prompt = showOptimized ? editedScorePrompt : scorePrompt
      const result = await api.generateScore(finalLyrics, prompt, sessionId)
      setVocalAbc(result.vocal_abc || result.abc_notation || '')
      setInstrumentAbc(result.instrument_abc || '')
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成曲谱失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRestoreScorePrompt = (version: PromptVersion) => {
    setEditedScorePrompt(version.content)
    setOptimizedScorePrompt(version.content)
    setShowOptimized(true)
    const restoredVersion: PromptVersion = {
      id: crypto.randomUUID(),
      step: 'score',
      type: 'restored',
      content: version.content,
      timestamp: new Date().toISOString(),
      parentVersionId: version.id,
      note: `回溯至 ${version.timestamp}`,
    }
    addScorePromptVersion(restoredVersion)
    setShowHistory(false)
  }

  const instruments: Array<'钢琴' | '古筝' | '小提琴'> = ['钢琴', '古筝', '小提琴']

  return (
    <div className="flex flex-col gap-6 py-8">
      <div className="text-center mb-2">
        <h2 className="text-2xl text-gold font-bold mb-2">曲谱生成</h2>
        <p className="text-rice-dark text-sm">基于歌词生成五线谱，支持人声与乐器双音轨</p>
      </div>

      <div className="bg-ink-light border border-gold/20 rounded-xl p-5">
        <h3 className="text-gold text-sm font-medium mb-2">参考歌词</h3>
        <pre className="whitespace-pre-wrap text-rice-dark text-sm leading-relaxed max-h-32 overflow-y-auto font-serif">
          {finalLyrics || '尚未确认歌词'}
        </pre>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="flex flex-col gap-6">
          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <label className="block text-gold text-sm font-medium mb-3">曲谱提示词</label>
            <textarea
              className="w-full h-28 bg-ink border border-gold/20 rounded-lg p-4 text-rice placeholder:text-rice-dark/50 focus:outline-none focus:border-gold/50 resize-none"
              placeholder="描述曲谱风格、节奏、调式..."
              value={scorePrompt}
              onChange={(e) => setScorePrompt(e.target.value)}
            />
            <button
              className="mt-3 px-5 py-2 bg-gold hover:bg-gold-light text-ink rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleOptimizeScorePrompt}
              disabled={!scorePrompt.trim() || loading}
            >
              {loading ? '优化中...' : 'AI优化曲谱提示词'}
            </button>
          </div>

          {showOptimized && (
            <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
              <label className="block text-gold text-sm font-medium mb-3">优化后提示词（可编辑）</label>
              <textarea
                className="w-full h-28 bg-ink border border-gold/20 rounded-lg p-4 text-rice placeholder:text-rice-dark/50 focus:outline-none focus:border-gold/50 resize-none"
                value={editedScorePrompt}
                onChange={(e) => setEditedScorePrompt(e.target.value)}
              />
            </div>
          )}

          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <label className="block text-gold text-sm font-medium mb-3">乐器选择</label>
            <div className="flex gap-3">
              {instruments.map((inst) => (
                <button
                  key={inst}
                  className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    selectedInstrument === inst
                      ? 'bg-gold text-ink shadow-lg shadow-gold/30'
                      : 'border border-gold/30 text-gold hover:bg-gold/10'
                  }`}
                  onClick={() => setSelectedInstrument(inst)}
                >
                  {inst}
                </button>
              ))}
            </div>
          </div>

          <button
            className="px-6 py-2.5 bg-gold hover:bg-gold-light text-ink rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleGenerateScore}
            disabled={!finalLyrics.trim() || loading}
          >
            {loading ? '生成中...' : '生成曲谱'}
          </button>
        </div>

        <div className="flex flex-col gap-6">
          {(vocalAbc || instrumentAbc) && (
            <>
              <div className="flex border-b border-gold/20">
                <button
                  className={`px-5 py-2.5 text-sm font-medium transition-colors ${
                    activeTab === 'vocal'
                      ? 'text-gold border-b-2 border-gold'
                      : 'text-rice-dark hover:text-rice'
                  }`}
                  onClick={() => setActiveTab('vocal')}
                >
                  人声音轨
                </button>
                <button
                  className={`px-5 py-2.5 text-sm font-medium transition-colors ${
                    activeTab === 'instrument'
                      ? 'text-gold border-b-2 border-gold'
                      : 'text-rice-dark hover:text-rice'
                  }`}
                  onClick={() => setActiveTab('instrument')}
                >
                  乐器音轨
                </button>
              </div>

              <ScoreDisplay
                abcNotation={activeTab === 'vocal' ? vocalAbc : instrumentAbc}
              />

              <AudioPlayer
                vocalAbc={vocalAbc}
                instrumentAbc={instrumentAbc}
                activeTrack={activeTab}
              />
            </>
          )}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          className="px-6 py-3 border border-gold/30 text-gold hover:bg-gold/10 rounded-lg transition-colors"
          onClick={() => setStep(1)}
        >
          上一步
        </button>
        <div className="flex gap-3">
          <button
            className="px-4 py-3 border border-gold/30 text-gold hover:bg-gold/10 rounded-lg transition-colors text-sm"
            onClick={() => setShowHistory(true)}
          >
            曲谱提示词历史 ({scorePromptVersions.length})
          </button>
          <button
            className="px-8 py-3 bg-vermilion hover:bg-vermilion-light text-rice rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={() => setStep(3)}
            disabled={!vocalAbc.trim() && !instrumentAbc.trim()}
          >
            确认曲谱
          </button>
        </div>
      </div>

      <PromptHistoryDrawer
        open={showHistory}
        onClose={() => setShowHistory(false)}
        versions={scorePromptVersions}
        onRestore={handleRestoreScorePrompt}
      />
    </div>
  )
}
