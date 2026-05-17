const DEFAULT_BACKEND_ORIGIN = 'http://127.0.0.1:8000'

export function getApiBase() {
  if (typeof window === 'undefined') {
    return `${DEFAULT_BACKEND_ORIGIN}/api`
  }

  const isElectron = Boolean(window.electronAPI?.isElectron)
  return isElectron ? `${DEFAULT_BACKEND_ORIGIN}/api` : '/api'
}

export function buildApiUrl(endpoint: string) {
  return `${getApiBase()}${endpoint}`
}

async function request(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(buildApiUrl(endpoint), {
    headers: { 'Content-Type': 'application/json', ...options.headers as Record<string, string> },
    ...options,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `API Error: ${response.statusText}`)
  }
  return response.json()
}

export const api = {
  optimizePrompt: (prompt: string, step: string, sessionId?: string) =>
    request('/prompt/optimize', { method: 'POST', body: JSON.stringify({ prompt, step, session_id: sessionId }) }),

  quickSuggest: (text: string, context?: string) =>
    request('/prompt/quick-suggest', { method: 'POST', body: JSON.stringify({ text, context }) }),

  getPromptHistory: (sessionId: string, step?: string) =>
    request(`/prompt/history/${sessionId}${step ? `?step=${step}` : ''}`),

  saveHumanModified: (step: string, content: string, sessionId: string, note?: string) =>
    request('/prompt/history/save', { method: 'POST', body: JSON.stringify({ step, content, session_id: sessionId, note }) }),

  generateLyrics: (
    prompt: string,
    style = '古风',
    sessionId?: string,
    paragraphCount = 2,
    rhymePreference = 'auto'
  ) =>
    request('/lyric/generate', {
      method: 'POST',
      body: JSON.stringify({
        prompt,
        style,
        paragraph_count: paragraphCount,
        rhyme_preference: rhymePreference,
        session_id: sessionId,
      }),
    }),

  exportLrc: (lrcContent: string, filename?: string) =>
    request('/lyric/export', { method: 'POST', body: JSON.stringify({ lrc_content: lrcContent, filename: filename || 'lyrics.lrc' }) }),

  optimizeScorePrompt: (prompt: string, sessionId?: string) =>
    request('/score/optimize-prompt', { method: 'POST', body: JSON.stringify({ prompt, session_id: sessionId }) }),

  generateScore: (
    lyrics: string,
    scorePrompt?: string,
    instrument = '钢琴',
    sessionId?: string
  ) =>
    request('/score/generate', {
      method: 'POST',
      body: JSON.stringify({
        lyrics,
        score_prompt: scorePrompt,
        instrument,
        session_id: sessionId,
      }),
    }),

  getScorePromptHistory: (sessionId: string) =>
    request(`/score/prompt/history?session_id=${sessionId}`),

  renderAudio: (abcNotation: string) =>
    request('/score/render-audio', { method: 'POST', body: JSON.stringify({ abc_notation: abcNotation }) }),

  generateMidi: (abcNotation: string, sessionId?: string, instrument?: string, vocalAbc?: string) =>
    request('/midi/generate', { method: 'POST', body: JSON.stringify({ abc_notation: abcNotation, session_id: sessionId, instrument, vocal_abc: vocalAbc }) }),
}
