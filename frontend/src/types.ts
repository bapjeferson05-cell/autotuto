export interface Beat {
  fim: boolean;
  diz?: string;
  tem_pergunta?: boolean;
  figura_png_base64?: string;
  passos_latex?: string[];
  valor?: number | string;
  resumo?: string;
  titulo?: string;
  topico?: string;
  avisos_planejador?: string[];
}

export interface IniciarResposta extends Beat {
  session_id: string;
}

export interface Mensagem {
  autor: 'aluno' | 'professor';
  texto?: string;
  beat?: Beat;
}
