import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface PromptVersion {
  id: string
  step: 'prompt' | 'score'
  type: 'original' | 'ai_optimized' | 'human_modified' | 'restored'
  content: string
  timestamp: string
  parentVersionId: string | null
  note?: string
}

interface MusicState {
  currentStep: number
  sessionId: string

  originalPrompt: string
  optimizedPrompt: string
  finalPrompt: string
  promptVersions: PromptVersion[]

  generatedLyrics: string
  lrcContent: string
  finalLyrics: string

  scorePrompt: string
  optimizedScorePrompt: string
  selectedInstrument: '钢琴' | '古筝' | '小提琴'
  vocalAbc: string
  instrumentAbc: string
  combinedAbc: string
  scorePromptVersions: PromptVersion[]

  midiUrl: string

  loading: boolean
  error: string | null

  setStep: (step: number) => void
  setSessionId: (sessionId: string) => void
  setOriginalPrompt: (prompt: string) => void
  setOptimizedPrompt: (prompt: string) => void
  setFinalPrompt: (prompt: string) => void
  addPromptVersion: (version: PromptVersion) => void
  setGeneratedLyrics: (lyrics: string) => void
  setLrcContent: (content: string) => void
  setFinalLyrics: (lyrics: string) => void
  setScorePrompt: (prompt: string) => void
  setOptimizedScorePrompt: (prompt: string) => void
  setSelectedInstrument: (instrument: '钢琴' | '古筝' | '小提琴') => void
  setVocalAbc: (abc: string) => void
  setInstrumentAbc: (abc: string) => void
  setCombinedAbc: (abc: string) => void
  addScorePromptVersion: (version: PromptVersion) => void
  setMidiUrl: (url: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

function createSessionId() {
  return crypto.randomUUID()
}

const initialState = {
  currentStep: 0,
  sessionId: createSessionId(),
  originalPrompt: '',
  optimizedPrompt: '',
  finalPrompt: '',
  promptVersions: [] as PromptVersion[],
  generatedLyrics: '',
  lrcContent: '',
  finalLyrics: '',
  scorePrompt: '',
  optimizedScorePrompt: '',
  selectedInstrument: '钢琴' as const,
  vocalAbc: '',
  instrumentAbc: '',
  combinedAbc: '',
  scorePromptVersions: [] as PromptVersion[],
  midiUrl: '',
  loading: false,
  error: null as string | null,
}

export const useMusicStore = create<MusicState>()(
  persist(
    (set) => ({
      ...initialState,

      setStep: (step) => set({ currentStep: step }),
      setSessionId: (sessionId) => set({ sessionId }),
      setOriginalPrompt: (prompt) => set({ originalPrompt: prompt }),
      setOptimizedPrompt: (prompt) => set({ optimizedPrompt: prompt }),
      setFinalPrompt: (prompt) => set({ finalPrompt: prompt }),
      addPromptVersion: (version) =>
        set((state) => ({ promptVersions: [...state.promptVersions, version] })),
      setGeneratedLyrics: (lyrics) => set({ generatedLyrics: lyrics }),
      setLrcContent: (content) => set({ lrcContent: content }),
      setFinalLyrics: (lyrics) => set({ finalLyrics: lyrics }),
      setScorePrompt: (prompt) => set({ scorePrompt: prompt }),
      setOptimizedScorePrompt: (prompt) => set({ optimizedScorePrompt: prompt }),
      setSelectedInstrument: (instrument) => set({ selectedInstrument: instrument }),
      setVocalAbc: (abc) => set({ vocalAbc: abc }),
      setInstrumentAbc: (abc) => set({ instrumentAbc: abc }),
      setCombinedAbc: (abc) => set({ combinedAbc: abc }),
      addScorePromptVersion: (version) =>
        set((state) => ({ scorePromptVersions: [...state.scorePromptVersions, version] })),
      setMidiUrl: (url) => set({ midiUrl: url }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      reset: () => set({ ...initialState, sessionId: createSessionId() }),
    }),
    {
      name: 'guyun-music-store',
      onRehydrateStorage: () => (state) => {
        if (state && !state.sessionId) {
          state.setSessionId(createSessionId())
        }
      },
    }
  )
)
