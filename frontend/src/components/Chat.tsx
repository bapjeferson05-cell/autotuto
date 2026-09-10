import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { Mensagem } from '../types';
import { MathDisplay } from './MathDisplay';

interface Props {
  mensagens: Mensagem[];
  iniciado: boolean;
  aguardandoPergunta: boolean;
  fim: boolean;
  carregando: boolean;
  erro: string | null;
  onEnviar: (texto: string) => void;
  onContinuar: () => void;
  onReiniciar: () => void;
}

export function Chat({
  mensagens, iniciado, aguardandoPergunta, fim, carregando, erro,
  onEnviar, onContinuar, onReiniciar,
}: Props) {
  const [texto, setTexto] = useState('');
  const fimDoChat = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fimDoChat.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [mensagens, carregando]);

  function enviar(e: FormEvent) {
    e.preventDefault();
    const t = texto.trim();
    if (!t || carregando) return;
    onEnviar(t);
    setTexto('');
  }

  return (
    <div className="chat">
      <div className="transcript">
        {mensagens.length === 0 && (
          <p className="vazio">
            Me conta o que você quer estudar — um exercício, um tópico, "quero entender trapézio"…
          </p>
        )}
        {mensagens.map((m, i) => (
          <div key={i} className={`msg ${m.autor}`}>
            {m.texto && <p>{m.texto}</p>}
            {m.beat && <MathDisplay beat={m.beat} />}
          </div>
        ))}
        {carregando && (
          <div className="msg professor pensando" aria-live="polite">
            <span className="ponto" /><span className="ponto" /><span className="ponto" />
          </div>
        )}
        {erro && <div className="erro" role="alert">{erro}</div>}
        {fim && (
          <div className="fim">
            <p>Fim da aula. Quer estudar outra coisa?</p>
            <button onClick={onReiniciar}>Nova pergunta</button>
          </div>
        )}
        <div ref={fimDoChat} />
      </div>
      {!fim && (
        <form className="entrada" onSubmit={enviar}>
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder={
              !iniciado
                ? 'O que você quer estudar?'
                : aguardandoPergunta
                  ? 'Responde aí…'
                  : 'Pergunta alguma coisa…'
            }
            disabled={carregando}
            aria-label="Sua mensagem"
          />
          <button type="submit" disabled={carregando || !texto.trim()}>Enviar</button>
          {iniciado && (
            <button type="button" className="secundario" onClick={onContinuar} disabled={carregando}>
              Continuar
            </button>
          )}
        </form>
      )}
    </div>
  );
}
