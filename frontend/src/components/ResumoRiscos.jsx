import React from 'react';

// Estimativas dos modelos de risco (v3: fatores clínicos por simulação com efeitos publicados).
// Profissional: números, AUC e dados faltantes. Gestante: linguagem simples,
// sem porcentagem, e o que levar para a equipe.

const ROTULO_NIVEL = { alto: 'Alto', moderado: 'Aumentado', baixo: 'Habitual' };
const COR_NIVEL = { alto: 'var(--color-vermelho, #C0392B)', moderado: '#B45309', baixo: '#1E7A46' };

const pct = (v) => `${(v * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
const vezes = (v) => `${Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} vez${v >= 1.95 ? 'es' : ''} a média`;

function valorDoModelo(c) {
  if (c.tipo_saida === 'probabilidade' && typeof c.probabilidade === 'number') {
    return `${pct(c.probabilidade)} (média ${pct(c.media_populacional)})${c.simulado ? ' · simulação' : ''}`;
  }
  if (typeof c.risco_relativo === 'number') return vezes(c.risco_relativo);
  return '';
}

export default function ResumoRiscos({ riscos, modo = 'gestante' }) {
  if (!riscos?.condicoes) return null;
  const condicoes = Object.values(riscos.condicoes);
  const fatores = riscos.fatores_clinicos || [];
  const prevencao = riscos.prevencao_pre_eclampsia;
  const faltando = [...new Set(condicoes.flatMap((c) => c.dados_faltantes || []))];

  if (modo === 'profissional') {
    return (
      <div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
          {condicoes.map((c) => (
            <div key={c.condicao} style={{ backgroundColor: '#FFFFFF', padding: '10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
              <strong style={{ fontSize: '0.8rem', display: 'block' }}>{c.nome}</strong>
              {c.fonte === 'indisponivel' || c.fonte === 'nao_se_aplica' ? (
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                  {c.fonte === 'nao_se_aplica' ? 'Não se aplica.' : 'Indisponível.'} {c.motivo}
                </span>
              ) : (
                <>
                  <span style={{ fontSize: '0.74rem', fontWeight: 700, color: COR_NIVEL[c.nivel] }}>
                    {ROTULO_NIVEL[c.nivel]}{c.motivo_nivel === 'diretriz' ? ' (critério das diretrizes)' : ''}
                  </span>
                  <span style={{ fontSize: '0.74rem', display: 'block', color: 'var(--color-text)' }}>{valorDoModelo(c)}</span>
                  <span style={{ fontSize: '0.68rem', display: 'block', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                    AUC {typeof c.auc === 'number' ? c.auc.toFixed(2).replace('.', ',') : '-'}
                    {c.dados_faltantes?.length ? ` · sem: ${c.dados_faltantes.join(', ')}` : ''}
                  </span>
                </>
              )}
            </div>
          ))}
        </div>

        {fatores.length > 0 && (
          <div style={{ marginTop: '12px' }}>
            <strong style={{ fontSize: '0.8rem', color: 'var(--color-vinho)' }}>Fatores clínicos informados (efeito publicado; nos modelos v3 eles já entram na estimativa, por simulação)</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: '18px', fontSize: '0.76rem', lineHeight: 1.45 }}>
              {fatores.map((f, i) => (
                <li key={i}>
                  {f.fator}
                  {typeof f.risco_relativo_publicado === 'number'
                    ? `: risco de pré-eclâmpsia ${f.risco_relativo_publicado.toLocaleString('pt-BR')} vezes maior (${f.fonte})`
                    : typeof f.razao_de_chances_publicada === 'number'
                      ? `: razão de chances ${f.razao_de_chances_publicada.toLocaleString('pt-BR')} para diabetes gestacional (${f.fonte})`
                      : ` (${f.fonte})`}
                  {f.peso_diretriz ? ` · fator ${f.peso_diretriz}` : ''}
                </li>
              ))}
            </ul>
          </div>
        )}

        {prevencao && (
          <div style={{ marginTop: '10px', padding: '8px 10px', borderLeft: '3px solid #B45309', backgroundColor: '#FFFBEB', fontSize: '0.76rem' }}>
            Critério de risco para pré-eclâmpsia atingido ({prevencao.altos} fator(es) alto(s), {prevencao.moderados} moderado(s)):
            avaliar indicação de profilaxia conforme a diretriz.
          </div>
        )}
      </div>
    );
  }

  // Gestante
  const acima = condicoes.filter((c) => c.nivel === 'alto' || c.nivel === 'moderado');
  const fatoresGestante = fatores.filter((f) => f.condicao === 'pre_eclampsia' && f.peso_diretriz);
  return (
    <div style={{ fontSize: '0.84rem', lineHeight: 1.5 }}>
      {acima.length === 0 ? (
        <p style={{ margin: '0 0 8px' }}>Pelos dados do seu cadastro, as estimativas estão na média ou abaixo dela.</p>
      ) : (
        <>
          <p style={{ margin: '0 0 6px' }}>Pelos dados do seu cadastro, estas estimativas ficaram acima da média:</p>
          <ul style={{ margin: '0 0 8px', paddingLeft: '18px' }}>
            {acima.map((c) => (
              <li key={c.condicao}>
                <strong>{c.nome}</strong>
                {c.motivo_nivel === 'diretriz'
                  ? ' (fator de risco importante no seu cadastro)'
                  : c.nivel === 'alto' ? ' (bem acima da média)' : ''}
              </li>
            ))}
          </ul>
          <p style={{ margin: '0 0 8px', color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
            Isso não é diagnóstico: é uma estimativa feita com dados de muitas gestantes brasileiras e com o efeito
            de fatores de risco publicado em estudos. Vale conversar com sua equipe.
          </p>
        </>
      )}

      {fatoresGestante.length > 0 && (
        <div style={{ margin: '8px 0', padding: '8px 10px', borderLeft: '3px solid var(--color-rosa)', backgroundColor: '#FFF5F7' }}>
          <strong style={{ display: 'block', marginBottom: '4px' }}>Leve para a sua equipe de pré-natal</strong>
          <ul style={{ margin: 0, paddingLeft: '18px' }}>
            {fatoresGestante.map((f, i) => <li key={i}>{f.fator}</li>)}
          </ul>
          {prevencao && <p style={{ margin: '6px 0 0', fontSize: '0.8rem' }}>{prevencao.mensagem}</p>}
        </div>
      )}

      {faltando.length > 0 && (
        <p style={{ margin: '8px 0 0', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
          Para estimativas mais precisas, complete no cadastro clínico: {faltando.join(', ')}.
        </p>
      )}
    </div>
  );
}
