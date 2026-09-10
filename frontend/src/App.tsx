import { useState } from 'react';
import { Chat } from './components/Chat';
import { iniciarAula, proximoBeat } from './api';
import type { Mensagem } from './types';
import './App.css';

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [aguardandoPergunta, setAguardandoPergunta] = useState(false);
  const [fim, setFim] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function comecar(problema: string) {
    setCarregando(true);
    setErro(null);
    try {
      const r = await iniciarAula(problema);
      setSessionId(r.session_id);
      setMensagens([
        { autor: 'aluno', texto: problema },
        { autor: 'professor', texto: r.diz, beat: r },
      ]);
      setAguardandoPergunta(!!r.tem_pergunta);
      setFim(!!r.fim);
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setCarregando(false);
    }
  }

  async function enviar(texto: string) {
    if (!sessionId) return comecar(texto);
    setMensagens((m) => [...m, { autor: 'aluno', texto }]);
    setCarregando(true);
    setErro(null);
    try {
      const r = await proximoBeat(sessionId, texto);
      setMensagens((m) => [...m, { autor: 'professor', texto: r.diz, beat: r }]);
      setAguardandoPergunta(!!r.tem_pergunta);
      setFim(!!r.fim);
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setCarregando(false);
    }
  }

  async function continuar() {
    if (!sessionId) return;
    setCarregando(true);
    setErro(null);
    try {
      const r = await proximoBeat(sessionId);
      if (r.diz) setMensagens((m) => [...m, { autor: 'professor', texto: r.diz, beat: r }]);
      setAguardandoPergunta(!!r.tem_pergunta);
      setFim(!!r.fim);
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setCarregando(false);
    }
  }

  function reiniciar() {
    setSessionId(null);
    setMensagens([]);
    setAguardandoPergunta(false);
    setFim(false);
    setErro(null);
  }

  return (
    <div className="app">
      <header className="cabecalho">
        <h1>AutoTuto</h1>
        <p>o professor de matemática que explica, desenha e conversa</p>
      </header>
      <Chat
        mensagens={mensagens}
        iniciado={!!sessionId}
        aguardandoPergunta={aguardandoPergunta}
        fim={fim}
        carregando={carregando}
        erro={erro}
        onEnviar={enviar}
        onContinuar={continuar}
        onReiniciar={reiniciar}
      />
    </div>
  );
}
