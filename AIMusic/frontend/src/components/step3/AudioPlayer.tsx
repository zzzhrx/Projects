import { useState, useRef, useCallback } from 'react'
import * as Tone from 'tone'

interface AudioPlayerProps {
  vocalAbc: string
  instrumentAbc: string
  activeTrack: 'vocal' | 'instrument'
}

function parseAbcNotes(abc: string): Array<{ note: string; duration: number }> {
  const notes: Array<{ note: string; duration: number }> = []
  const lines = abc.split('\n')
  let inBody = false

  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('K:')) {
      inBody = true
      continue
    }
    if (!inBody || trimmed.startsWith('%') || trimmed.length === 0) continue

    const noteRegex = /(\^?_?=?)?([A-Ga-g])([,']*)(\d*\/?\d*)/g
    let match
    while ((match = noteRegex.exec(trimmed)) !== null) {
      const accidental = match[1] || ''
      const pitch = match[2]
      const octave = match[3] || ''
      const durStr = match[4] || ''

      let noteName = pitch.toUpperCase()
      if (pitch === pitch.toLowerCase()) {
        const hasOctaveUp = octave.replace(/'/g, '').length > 0
        noteName = hasOctaveUp
          ? pitch.toUpperCase() + '#'
          : pitch.toUpperCase()
      }

      const isUpper = pitch === pitch.toUpperCase()
      const octaveNum = isUpper ? 4 : 5
      const sharps = (octave.match(/'/g) || []).length
      const flats = (octave.match(/,/g) || []).length
      const finalOctave = octaveNum + sharps - flats

      let duration = 1
      if (durStr.includes('/')) {
        const parts = durStr.split('/')
        duration = Number(parts[0] || 1) / Number(parts[1] || 2)
      } else if (durStr) {
        duration = Number(durStr)
      }

      const sharp = accidental === '^' ? '#' : ''
      const flat = accidental === '_' ? 'b' : ''
      notes.push({
        note: `${noteName}${sharp || flat}${finalOctave}`,
        duration,
      })
    }
  }
  return notes
}

export default function AudioPlayer({ vocalAbc, instrumentAbc, activeTrack }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentTime, setCurrentTime] = useState('0:00')
  const [totalTime, setTotalTime] = useState('0:00')
  const synthRef = useRef<Tone.PolySynth | null>(null)
  const sequenceRef = useRef<Tone.Part | null>(null)
  const startTimeRef = useRef<number>(0)
  const durationRef = useRef<number>(0)
  const animFrameRef = useRef<number>(0)
  const playingRef = useRef(false)

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const stopPlayback = useCallback(() => {
    playingRef.current = false
    if (sequenceRef.current) {
      sequenceRef.current.dispose()
      sequenceRef.current = null
    }
    if (synthRef.current) {
      synthRef.current.releaseAll()
    }
    setIsPlaying(false)
    setProgress(0)
    setCurrentTime('0:00')
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
      animFrameRef.current = 0
    }
  }, [])

  const updateProgress = useCallback(() => {
    if (!playingRef.current) return
    const elapsed = Tone.getTransport().seconds
    const total = durationRef.current
    if (total > 0) {
      setProgress(Math.min(elapsed / total, 1))
      setCurrentTime(formatTime(elapsed))
    }
    if (elapsed < total) {
      animFrameRef.current = requestAnimationFrame(updateProgress)
    } else {
      stopPlayback()
    }
  }, [stopPlayback])

  const handlePlay = async () => {
    await Tone.start()

    const abc = activeTrack === 'vocal' ? vocalAbc : instrumentAbc
    if (!abc.trim()) return

    stopPlayback()

    if (!synthRef.current) {
      synthRef.current = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'triangle' },
        envelope: { attack: 0.02, decay: 0.1, sustain: 0.3, release: 0.5 },
      }).toDestination()
    }

    const parsedNotes = parseAbcNotes(abc)
    if (parsedNotes.length === 0) return

    const bpm = 120
    Tone.getTransport().bpm.value = bpm

    const noteEvents: Array<{ time: number; note: string; duration: number }> = []
    let timeOffset = 0
    const beatDuration = 60 / bpm

    for (const n of parsedNotes) {
      const dur = n.duration * beatDuration
      try {
        noteEvents.push({ time: timeOffset, note: n.note, duration: dur * 0.9 })
      } catch {
        // skip invalid notes
      }
      timeOffset += dur
    }

    durationRef.current = timeOffset
    setTotalTime(formatTime(timeOffset))

    const part = new Tone.Part((time, event) => {
      try {
        synthRef.current?.triggerAttackRelease(event.note, event.duration, time)
      } catch {
        // skip playback errors
      }
    }, noteEvents.map((e) => ({ time: e.time, note: e.note, duration: e.duration })))

    part.start(0)
    sequenceRef.current = part

    Tone.getTransport().start()
    playingRef.current = true
    setIsPlaying(true)
    startTimeRef.current = Date.now()
    animFrameRef.current = requestAnimationFrame(updateProgress)
  }

  const handlePause = () => {
    if (playingRef.current) {
      Tone.getTransport().pause()
      playingRef.current = false
      setIsPlaying(false)
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
        animFrameRef.current = 0
      }
    } else {
      Tone.getTransport().start()
      playingRef.current = true
      setIsPlaying(true)
      animFrameRef.current = requestAnimationFrame(updateProgress)
    }
  }

  const handleStop = () => {
    Tone.getTransport().stop()
    Tone.getTransport().position = 0
    stopPlayback()
  }

  return (
    <div className="bg-ink-light border border-gold/20 rounded-xl p-5">
      <div className="flex items-center gap-4 mb-3">
        <button
          className="w-10 h-10 flex items-center justify-center rounded-full bg-gold/20 text-gold hover:bg-gold/30 transition-colors"
          onClick={isPlaying ? handlePause : handlePlay}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>
        <button
          className="w-10 h-10 flex items-center justify-center rounded-full bg-gold/10 text-gold hover:bg-gold/20 transition-colors"
          onClick={handleStop}
        >
          ⏹
        </button>
        <div className="flex-1">
          <div className="w-full h-1.5 bg-ink rounded-full overflow-hidden">
            <div
              className="h-full bg-gold rounded-full transition-all duration-200"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
        </div>
        <span className="text-rice-dark text-xs min-w-[80px] text-right">
          {currentTime} / {totalTime}
        </span>
      </div>
      <p className="text-rice-dark text-xs text-center">
        当前播放：{activeTrack === 'vocal' ? '人声音轨' : '乐器音轨'}
      </p>
    </div>
  )
}
