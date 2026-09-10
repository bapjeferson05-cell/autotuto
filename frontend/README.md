# AutoTuto — frontend

Chat web do professor de matemática: React + TypeScript (Vite), fala com o
`backend/` (FastAPI) da raiz do repositório. Renderiza a fala do professor, as
figuras geométricas (PNG do `professor/figuras`) e os passos da conta em LaTeX
(via [KaTeX](https://katex.org)).

```bash
npm install
cp .env.example .env      # VITE_API_URL — default já aponta pro backend local
npm run dev                # http://localhost:5173, precisa do backend rodando (:8000)
```

| arquivo | o quê |
|---|---|
| `src/api.ts` | chama `POST /api/aulas` e `POST /api/aulas/{id}/proximo` |
| `src/App.tsx` | estado da conversa (sessão, transcript, se está esperando resposta) |
| `src/components/Chat.tsx` | a caixa de chat: transcript + campo de entrada |
| `src/components/MathDisplay.tsx` | figura (PNG base64) e passos da conta (KaTeX) de um beat |

```bash
npm run build   # tsc -b && vite build → dist/
npm run lint    # oxlint
```

Ver `README.md` e `PROJETO.md` na raiz do repo para a arquitetura completa
(o mesmo `professor/` também roda por voz/terminal, fora do navegador).
