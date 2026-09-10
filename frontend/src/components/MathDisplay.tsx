import katex from 'katex';
import 'katex/dist/katex.min.css';
import type { Beat } from '../types';

function Formula({ latex }: { latex: string }) {
  const html = katex.renderToString(latex, { throwOnError: false, displayMode: true });
  // eslint-disable-next-line react/no-danger
  return <div className="formula" dangerouslySetInnerHTML={{ __html: html }} />;
}

export function MathDisplay({ beat }: { beat: Beat }) {
  if (!beat.figura_png_base64 && !beat.passos_latex?.length) return null;
  return (
    <div className="math-display">
      {beat.figura_png_base64 && (
        <img className="figura" src={`data:image/png;base64,${beat.figura_png_base64}`} alt="figura da aula" />
      )}
      {beat.passos_latex?.map((latex, i) => <Formula key={i} latex={latex} />)}
    </div>
  );
}
