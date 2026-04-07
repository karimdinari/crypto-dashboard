/** Relative URLs — Vite dev proxy forwards `/api` to the FastAPI backend. */

export async function fetchJson<T>(path: string): Promise<T> {
  const r = await fetch(path)
  if (!r.ok) {
    throw new Error(`${r.status} ${r.statusText}`)
  }
  return r.json() as Promise<T>
}
