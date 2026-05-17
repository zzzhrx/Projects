import { useState, useRef, useEffect, useCallback } from 'react'
import { useMusicStore } from '../../store/musicStore'
import { api } from '../../services/api'
import { Midi } from '@tonejs/midi'

export default function MidiStep() {
  const {
    vocalAbc, instrumentAbc, selectedInstrument, midiUrl,
    sessionId, finalLyrics,
    setMidiUrl, setStep, setLoading, setError, loading, reset,
  } = useMusicStore()

  const [downloadType, setDownloadType] = useState<'vocal' | 'instrument' | 'full'>('full')
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentLyric, setCurrentLyric] = useState('')
  const [allLyrics, setAllLyrics] = useState<string[]>([])
  const [progress, setProgress] = useState(0)
  const [timeDisplay, setTimeDisplay] = useState('0:00 / 0:00')
  const playingRef = useRef(false)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const scheduledNodesRef = useRef<OscillatorNode[]>([])
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const totalDurationRef = useRef(0)
  const startTimeRef = useRef(0)
  const currentLyricRef = useRef('')

  const stopPlayback = useCallback(() => {
    playingRef.current = false
    setIsPlaying(false)
    for (const osc of scheduledNodesRef.current) {
      try { osc.stop() } catch { /* already stopped */ }
    }
    scheduledNodesRef.current = []
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }
    if (audioCtxRef.current?.state === 'running') {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
    setProgress(0)
    setCurrentLyric('')
    setTimeDisplay('0:00 / 0:00')
  }, [])

  useEffect(() => {
    return () => stopPlayback()
  }, [stopPlayback])

  const handleGenerateMidi = async () => {
    const abc = downloadType === 'vocal'
      ? vocalAbc
      : downloadType === 'instrument'
        ? instrumentAbc
        : `${vocalAbc}\n${instrumentAbc}`

    if (!abc.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.generateMidi(abc, sessionId, selectedInstrument, vocalAbc)
      setMidiUrl(result.midi_url || result.url || '')
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成MIDI失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePlayMidi = async () => {
    if (!midiUrl) return

    if (isPlaying) {
      stopPlayback()
      return
    }

    try {
      const response = await fetch(midiUrl)
      const arrayBuffer = await response.arrayBuffer()
      const midi = new Midi(arrayBuffer)

      // Extract all lyrics from MIDI tracks
      const allLyricEvents: Array<{ time: number; text: string }> = []
      for (const track of midi.tracks) {
        // @tonejs/midi stores lyrics in track meta or note-level
        for (const note of track.notes) {
          if (note.lyric) {
            allLyricEvents.push({ time: note.time, text: note.lyric })
          }
        }
      }
      setAllLyrics(allLyricEvents.map(l => l.text))

      if (!audioCtxRef.current || audioCtxRef.current.state === 'closed') {
        audioCtxRef.current = new AudioContext()
      }
      const ctx = audioCtxRef.current
      playingRef.current = true
      setIsPlaying(true)

      const now = ctx.currentTime
      startTimeRef.current = now
      const scheduled: OscillatorNode[] = []

      // Calculate total duration
      let maxEnd = 0
      for (const track of midi.tracks) {
        for (const note of track.notes) {
          maxEnd = Math.max(maxEnd, note.time + note.duration)
        }
      }
      totalDurationRef.current = maxEnd
      setTimeDisplay(`0:00 / ${formatTime(maxEnd)}`)

      // Determine which tracks are vocal (has lyrics or program 53/54)
      for (const track of midi.tracks) {
        const hasLyrics = track.notes.some(n => n.lyric)
        const isVocal = hasLyrics || track.instrument?.number === 53 || track.instrument?.number === 54

        for (const note of track.notes) {
          if (!playingRef.current) break

          const startTime = now + note.time
          const duration = note.duration
          const freq = midiToFrequency(note.midi)

          const osc = ctx.createOscillator()
          const gain = ctx.createGain()

          // Vocal: brighter sawtooth wave, louder. Instrument: softer sine
          if (isVocal) {
            osc.type = 'triangle'
            gain.gain.setValueAtTime(0, startTime)
            gain.gain.linearRampToValueAtTime(note.velocity * 0.3, startTime + 0.03)
            gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration * 0.9)
          } else {
            osc.type = 'sine'
            gain.gain.setValueAtTime(0, startTime)
            gain.gain.linearRampToValueAtTime(note.velocity * 0.15, startTime + 0.03)
            gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration * 0.9)
          }

          osc.frequency.value = freq
          osc.connect(gain)
          gain.connect(ctx.destination)
          osc.start(startTime)
          osc.stop(startTime + duration + 0.1)
          scheduled.push(osc)
        }
      }

      scheduledNodesRef.current = scheduled

      // Progress + lyric display timer (use ref to avoid stale closure)
      currentLyricRef.current = ''
      progressTimerRef.current = setInterval(() => {
        if (!playingRef.current) return
        const elapsed = ctx.currentTime - startTimeRef.current
        const total = totalDurationRef.current
        if (total > 0) {
          setProgress(Math.min(elapsed / total, 1))
          setTimeDisplay(`${formatTime(elapsed)} / ${formatTime(total)}`)
          const current = allLyricEvents.filter(l => l.time <= elapsed).pop()
          if (current && current.text !== currentLyricRef.current) {
            currentLyricRef.current = current.text
            setCurrentLyric(current.text)
          }
        }
        if (elapsed >= total) {
          stopPlayback()
        }
      }, 100)

      // Auto-stop when done
      setTimeout(() => {
        if (playingRef.current) stopPlayback()
      }, (maxEnd + 1) * 1000)

    } catch (err) {
      setError(err instanceof Error ? err.message : '播放MIDI失败')
      setIsPlaying(false)
    }
  }

  const handleDownload = () => {
    if (!midiUrl) return
    const a = document.createElement('a')
    a.href = midiUrl
    a.download = `guyun_${downloadType}.mid`
    a.click()
  }

  const downloadOptions: Array<{ value: 'vocal' | 'instrument' | 'full'; label: string }> = [
    { value: 'vocal', label: '仅人声' },
    { value: 'instrument', label: '仅乐器' },
    { value: 'full', label: '完整合并' },
  ]

  return (
    <div className="flex flex-col gap-6 py-8">
      <div className="text-center mb-2">
        <h2 className="text-2xl text-gold font-bold mb-2">MIDI导出</h2>
        <p className="text-rice-dark text-sm">将曲谱转换为MIDI文件，支持预览与下载</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="flex flex-col gap-6">
          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <h3 className="text-gold text-sm font-medium mb-4">曲谱摘要</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-rice-dark">乐器</span>
                <span className="text-rice">{selectedInstrument}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-rice-dark">人声音轨</span>
                <span className="text-rice">{vocalAbc ? '已生成' : '未生成'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-rice-dark">乐器音轨</span>
                <span className="text-rice">{instrumentAbc ? '已生成' : '未生成'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-rice-dark">歌词行数</span>
                <span className="text-rice">{finalLyrics.split('\n').filter((l) => l.trim()).length}行</span>
              </div>
            </div>
          </div>

          <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
            <h3 className="text-gold text-sm font-medium mb-4">下载选项</h3>
            <div className="flex gap-3 mb-4">
              {downloadOptions.map((opt) => (
                <button
                  key={opt.value}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    downloadType === opt.value
                      ? 'bg-gold text-ink shadow-lg shadow-gold/30'
                      : 'border border-gold/30 text-gold hover:bg-gold/10'
                  }`}
                  onClick={() => setDownloadType(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <button
              className="w-full px-6 py-2.5 bg-gold hover:bg-gold-light text-ink rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleGenerateMidi}
              disabled={loading}
            >
              {loading ? '生成中...' : '生成MIDI'}
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          {midiUrl && (
            <div className="bg-ink-light border border-gold/20 rounded-xl p-6">
              <h3 className="text-gold text-sm font-medium mb-4">MIDI预览</h3>

              <div className="flex items-center gap-4 mb-4">
                <button
                  className={`w-10 h-10 flex items-center justify-center rounded-full transition-colors ${
                    isPlaying
                      ? 'bg-vermilion/30 text-vermilion-light hover:bg-vermilion/40'
                      : 'bg-gold/20 text-gold hover:bg-gold/30'
                  }`}
                  onClick={handlePlayMidi}
                >
                  <span className="text-lg">{isPlaying ? '⏸' : '▶'}</span>
                </button>
                <div className="flex-1">
                  <div className="w-full h-1.5 bg-ink rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gold rounded-full transition-all duration-200"
                      style={{ width: `${progress * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-rice-dark text-xs min-w-[100px] text-right">
                  {timeDisplay}
                </span>
              </div>

              {/* Current lyric display */}
              {currentLyric && (
                <div className="mb-3 p-3 bg-gold/10 border border-gold/30 rounded-lg text-center">
                  <span className="text-gold text-lg font-serif">{currentLyric}</span>
                </div>
              )}

              {/* All lyrics overview */}
              {allLyrics.length > 0 && (
                <div className="max-h-32 overflow-y-auto space-y-1 text-center">
                  {allLyrics.map((lyric, i) => (
                    <p
                      key={i}
                      className={`text-sm transition-colors ${
                        lyric === currentLyric
                          ? 'text-gold font-medium'
                          : 'text-rice-dark'
                      }`}
                    >
                      {lyric}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {midiUrl && (
            <button
              className="w-full px-6 py-3 bg-vermilion hover:bg-vermilion-light text-rice rounded-lg font-medium transition-colors"
              onClick={handleDownload}
            >
              下载MIDI
            </button>
          )}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          className="px-6 py-3 border border-gold/30 text-gold hover:bg-gold/10 rounded-lg transition-colors"
          onClick={() => setStep(2)}
        >
          上一步
        </button>
        <button
          className="px-8 py-3 bg-gold text-ink rounded-lg font-medium hover:bg-gold-light transition-colors"
          onClick={reset}
        >
          重新创作
        </button>
      </div>
    </div>
  )
}

function midiToFrequency(midi: number): number {
  return 440 * Math.pow(2, (midi - 69) / 12)
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
