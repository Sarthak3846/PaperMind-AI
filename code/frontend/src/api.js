// Thin client for the PaperMind backend. The execution log shown in the UI is built
// ONLY from events streamed by the server (Server-Sent Events); nothing is simulated.
export const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

async function jsonOrThrow(res) {
  if (res.ok) return res.json()
  let detail = `${res.status} ${res.statusText}`
  try {
    const body = await res.json()
    if (body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
  } catch { /* ignore */ }
  throw new Error(detail)
}

export const fetchHealth = () => fetch(`${API_BASE}/api/health`).then(jsonOrThrow)
export const fetchPapers = () => fetch(`${API_BASE}/api/papers`).then(jsonOrThrow)

/** POST the question and call onEvent(event) for every SSE event, in order. */
export async function streamResearch(body, onEvent, signal) {
  const res = await fetch(`${API_BASE}/api/research/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) await jsonOrThrow(res)
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const line = chunk.split('\n').find((l) => l.startsWith('data: '))
      if (line) {
        try { onEvent(JSON.parse(line.slice(6))) } catch { /* ignore malformed event */ }
      }
    }
  }
}
