import type { Beat, IniciarResposta } from './types';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

async function post<T>(caminho: string, corpo: unknown): Promise<T> {
  const r = await fetch(`${BASE}${caminho}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(corpo),
  });
  if (!r.ok) {
    const texto = await r.text().catch(() => '');
    throw new Error(`${r.status} ${r.statusText}${texto ? ` — ${texto}` : ''}`);
  }
  return r.json() as Promise<T>;
}

export function iniciarAula(problema: string): Promise<IniciarResposta> {
  return post<IniciarResposta>('/api/aulas', { problema });
}

export function proximoBeat(sessionId: string, resposta?: string): Promise<Beat> {
  return post<Beat>(`/api/aulas/${sessionId}/proximo`, { resposta: resposta ?? null });
}
