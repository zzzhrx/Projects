import { useState } from 'react'
import { useMusicStore } from '../../store/musicStore'
import { api } from '../../services/api'

const TIMESTAMP_PATTERN = /^\[(\d{2}:\d{2}\.\d{2,3})\](.*)$/
const SECTION_PATTERN = /^\[[^\d\]]+[^\]]*\]$/

function buildAutoTimestamp(index: number) {
  const mm = String(Math.floor(index * 8 / 60)).padStart(2, '0')
  const ss = String((index * 8) % 60).padStart(2, '0')
  return `${mm}:${ss}.000`
}

function normalizeLyricsToLrc(lyrics: string) {
  const lines = lyrics.split('\n')
  const normalizedLines: string[] = []
  let autoTimedIndex = 0

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) {
      continue
    }

    const timestampMatch = line.match(TIMESTAMP_PATTERN)
    if (timestampMatch) {
      normalizedLines.push(`[${timestampMatch[1]}]${timestampMatch[2]}`)
      autoTimedIndex += 1
      continue
    }

    if (SECTION_PATTERN.test(line)) {
      normalizedLines.push(line)
      continue
    }

    normalizedLines.push(`[${buildAutoTimestamp(autoTimedIndex)}]${line}`)
    autoTimedIndex += 1
  }

  return normalizedLines.join('\n')
}

export default function LyricStep() {
  const {
    finalPrompt, generatedLyrics, lrcContent, sessionId,
    setGeneratedLyrics, setLrcContent, setFinalLyrics, setSessionId,
    setStep, setLoading, setError, loading,
  } = useMusicStore()

  const [paragraphCount, setParagraphCount] = useState(2)
  const [rhymePreference, setRhymePreference] = useState('auto')
  const [editingLyrics, setEditingLyrics] = useState('')
  const [showEditor, setShowEditor] = useState(false)
  const [suggestion, setSuggestion] = useState('')
  const [showSuggestion, setShowSuggestion] = useState(false)

  const handleGenerate = async () => {
    if (!finalPrompt.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.generateLyrics(finalPrompt, '古风', sessionId, paragraphCount, rhymePreference)
      const lyrics = result.lyrics || result.content || ''
      if (result.session_id) {
        setSessionId(result.session_id)
      }
      setGeneratedLyrics(lyrics)
      setEditingLyrics(lyrics)
      setShowEditor(true)
      setLrcContent(result.lrc_content || normalizeLyricsToLrc(lyrics))
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成歌词失败')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickSuggest = async () => {
    const text = showEditor ? editingLyrics : generatedLyrics
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.quickSuggest(text, '古风歌词改进建议')
      setSuggestion(result.suggestion || result.content || '')
      setShowSuggestion(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : '快速建议失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveLrc = () => {
    if (!lrcContent) return
    const blob = new Blob([lrcContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'lyrics.lrc'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleConfirm = () => {
    const lyrics = showEditor ? editingLyrics : generatedLyrics
    if (!lyrics.trim()) return
    setFinalLyrics(lyrics)
    setStep(2)
  }

  const handleLyricsEdit = (value: string) => {
    setEditingLyrics(value)
    setLrcContent(normalizeLyricsToLrc(value))
  }

  const handleTimeChange = (lineIndex: number, timeStr: string) => {
    const lines = lrcContent.split('\n')
    if (lineIndex < lines.length) {
      const content = lines[lineIndex].replace(/^\[\d{2}:\d{2}\.\d{2,3}\]/, '')
      lines[lineIndex] = `[${timeStr}]${content}`
      setLrcContent(lines.join('\n'))

      const lyricLines = editingLyrics.split('\n')
      if (lineIndex < lyricLines.length) {
        const lyricContent = lyricLines[lineIndex].replace(/^\[\d{2}:\d{2}\.\d{2,3}\]/, '')
        lyricLines[lineIndex] = `[${timeStr}]${lyricContent}`
        setEditingLyrics(lyricLines.join('\n'))
      }
    }
  }

  const lrcLines = lrcContent.split('\n').filter((l) => l.trim())

  return (
    <div className="flex flex-col gap-6 py-8">
      <div className="text-center mb-2">
        <h2 className="text-2xl text-gold font-bold mb-2">歌词生成</h2>
        <p className="text-rice-dark text-sm">基于提示词生成古风歌词，支持编辑与时间轴标注</p>
      </div>

      <div className="bg-ink-light border border-gold/20 rounded-xl p-5">
        <h3 className="text-gold text-sm font-medium mb-2">参考提示词</h3>
        <p className="text-rice-dark text-sm leading-relaxed">{finalPrompt || '尚未设置提示词'}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <div className="flex items-center gap-6 mb-4">
              <div className="flex items-center gap-2">
                <label className="text-rice text-sm">段落数</label>
                <select
                  className="bg-ink border border-gold/20 rounded-lg px-3 py-1.5 text-rice text-sm focus:outline-none focus:border-gold/50"
                  value={paragraphCount}
                  onChange={(e) => setParagraphCount(Number(e.target.value))}
                >
                  {[1, 2, 3, 4].map((n) => (
                    <option key={n} value={n}>{n}段</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-rice text-sm">押韵偏好</label>
                <select
                  className="bg-ink border border-gold/20 rounded-lg px-3 py-1.5 text-rice text-sm focus:outline-none focus:border-gold/50"
                  value={rhymePreference}
                  onChange={(e) => setRhymePreference(e.target.value)}
                >
                  <option value="auto">自动</option>
                  <option value="ang">ang韵</option>
                  <option value="an">an韵</option>
                  <option value="ing">ing韵</option>
                  <option value="ou">ou韵</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                className="px-6 py-2.5 bg-gold hover:bg-gold-light text-ink rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleGenerate}
                disabled={!finalPrompt.trim() || loading}
              >
                {loading ? '生成中...' : '生成歌词'}
              </button>
              {showEditor && (
                <button
                  className="px-6 py-2.5 border border-gold/40 text-gold hover:bg-gold/10 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={handleQuickSuggest}
                  disabled={loading}
                >
                  快速建议
                </button>
              )}
            </div>

            {showSuggestion && suggestion && (
              <div className="mt-4 p-4 bg-gold/5 border border-gold/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gold text-xs font-medium">AI 改进建议</span>
                  <button
                    className="text-rice-dark hover:text-rice text-xs transition-colors"
                    onClick={() => setShowSuggestion(false)}
                  >
                    ✕
                  </button>
                </div>
                <p className="text-rice-dark text-sm leading-relaxed">{suggestion}</p>
              </div>
            )}
          </div>

          {showEditor && (
            <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
              <label className="block text-gold text-sm font-medium mb-3">歌词编辑器</label>
              <div className="relative">
                <div className="absolute left-0 top-0 bottom-0 w-8 bg-ink-light border-r border-gold/10 flex flex-col items-center pt-4 text-rice-dark text-xs select-none overflow-hidden">
                  {editingLyrics.split('\n').map((_, i) => (
                    <div key={i} className="leading-6 h-6">{i + 1}</div>
                  ))}
                </div>
                <textarea
                  className="w-full h-64 bg-ink border border-gold/20 rounded-lg pl-10 pr-4 py-4 text-rice placeholder:text-rice-dark/50 focus:outline-none focus:border-gold/50 resize-none leading-6"
                  value={editingLyrics}
                  onChange={(e) => handleLyricsEdit(e.target.value)}
                />
              </div>
            </div>
          )}

          {showEditor && lrcLines.length > 0 && (
            <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
              <label className="block text-gold text-sm font-medium mb-3">时间轴编辑</label>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {lrcLines.map((line, i) => {
                  const match = line.match(/^\[(\d{2}:\d{2}\.\d{3})\](.*)/)
                  if (!match) return null
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <input
                        type="text"
                        className="w-24 bg-ink border border-gold/20 rounded px-2 py-1 text-rice text-xs text-center focus:outline-none focus:border-gold/50"
                        value={match[1]}
                        onChange={(e) => handleTimeChange(i, e.target.value)}
                        placeholder="MM:SS.mmm"
                      />
                      <span className="text-rice-dark text-xs flex-1 truncate">{match[2]}</span>
                    </div>
                  )
                })}
              </div>
              <div className="flex gap-3 mt-4">
                <button
                  className="px-5 py-2 border border-gold/40 text-gold hover:bg-gold/10 rounded-lg text-sm transition-colors"
                  onClick={handleSaveLrc}
                >
                  保存LRC
                </button>
              </div>
            </div>
          )}

          <div className="flex justify-between">
            <button
              className="px-6 py-3 border border-gold/30 text-gold hover:bg-gold/10 rounded-lg transition-colors"
              onClick={() => setStep(0)}
            >
              上一步
            </button>
            <button
              className="px-8 py-3 bg-vermilion hover:bg-vermilion-light text-rice rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleConfirm}
              disabled={!(showEditor ? editingLyrics.trim() : generatedLyrics.trim()) || loading}
            >
              确认歌词
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <h3 className="text-gold text-sm font-medium mb-3">歌词预览</h3>
            <pre className="whitespace-pre-wrap text-rice text-sm leading-relaxed font-serif">
              {generatedLyrics || '尚未生成歌词'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
