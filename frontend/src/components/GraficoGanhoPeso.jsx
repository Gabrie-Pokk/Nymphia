import React, { useState } from 'react';

// Gráfico de ganho de peso no estilo da Caderneta da Gestante: a faixa
// recomendada (FEBRASGO 2023, pelo IMC de antes da gravidez) e um ponto por
// pesagem, cada um na semana em que foi feito. Toque num ponto para ver o valor.

const LARGURA = 360;
const ALTURA = 230;
const MARGEM = { esquerda: 34, direita: 12, topo: 14, baixo: 30 };
const MARCOS = [0, 13, 27, 40];

const kg = (valor) =>
  Number(valor).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export default function GraficoGanhoPeso({ curva, pontos }) {
  const [selecionado, setSelecionado] = useState(null);
  if (!curva || curva.length === 0) return null;

  const valores = [
    ...curva.map((c) => c.min_kg),
    ...curva.map((c) => c.max_kg),
    ...pontos.map((p) => p.ganho_kg),
    0
  ];
  const yMin = Math.floor(Math.min(...valores) - 1);
  const yMax = Math.ceil(Math.max(...valores) + 1);
  const larguraUtil = LARGURA - MARGEM.esquerda - MARGEM.direita;
  const alturaUtil = ALTURA - MARGEM.topo - MARGEM.baixo;
  const x = (semana) => MARGEM.esquerda + (Math.min(42, Math.max(0, semana)) / 40) * larguraUtil;
  const y = (valor) => MARGEM.topo + ((yMax - valor) / (yMax - yMin)) * alturaUtil;

  const passo = yMax - yMin > 16 ? 4 : 2;
  const linhasGrade = [];
  for (let v = Math.ceil(yMin / passo) * passo; v <= yMax; v += passo) linhasGrade.push(v);

  const faixa = [
    ...curva.map((c) => `${x(c.semana)},${y(c.max_kg)}`),
    ...[...curva].reverse().map((c) => `${x(c.semana)},${y(c.min_kg)}`)
  ].join(' ');
  const ordenados = [...pontos].sort((a, b) => a.semana - b.semana || a.data.localeCompare(b.data));
  const trilha = ordenados.map((p) => `${x(p.semana)},${y(p.ganho_kg)}`).join(' ');
  const faixaDaSemana = (semana) => curva.find((c) => c.semana === Math.min(40, semana));
  const rotuloFaixa = faixaDaSemana(32);

  return (
    <div style={{ position: 'relative' }}>
      <svg
        viewBox={`0 0 ${LARGURA} ${ALTURA}`}
        style={{ width: '100%', height: 'auto', display: 'block' }}
        role="img"
        aria-label="Gráfico do ganho de peso por semana de gestação, com a faixa recomendada"
        onClick={() => setSelecionado(null)}
      >
        {linhasGrade.map((v) => (
          <g key={`g${v}`}>
            <line
              x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)}
              stroke={v === 0 ? '#C9BFC2' : '#EFE8EA'} strokeWidth="1"
            />
            <text x={MARGEM.esquerda - 6} y={y(v) + 3.5} textAnchor="end" fontSize="9.5" fill="#8A7F83">
              {v > 0 ? `+${v}` : v}
            </text>
          </g>
        ))}

        <polygon points={faixa} fill="rgba(39, 174, 96, 0.16)" stroke="none" />
        {rotuloFaixa && (
          <text
            x={x(32)} y={(y(rotuloFaixa.max_kg) + y(rotuloFaixa.min_kg)) / 2 + 3}
            textAnchor="middle" fontSize="9.5" fill="#3F6B4E" fontWeight="600"
          >
            faixa recomendada
          </text>
        )}

        {MARCOS.map((s) => (
          <text key={`m${s}`} x={x(s)} y={ALTURA - 12} textAnchor="middle" fontSize="9.5" fill="#8A7F83">
            {s === 0 ? '0' : `${s} sem`}
          </text>
        ))}
        <text x={LARGURA - MARGEM.direita} y={ALTURA - 1} textAnchor="end" fontSize="9" fill="#A39A9D">
          semanas de gestação
        </text>
        <text x={4} y={MARGEM.topo - 4} fontSize="9" fill="#A39A9D">kg ganhos</text>

        {ordenados.length > 1 && (
          <polyline points={trilha} fill="none" stroke="var(--color-vinho, #6B2737)" strokeWidth="2"
            strokeLinejoin="round" strokeLinecap="round" />
        )}
        {ordenados.map((p, i) => {
          const ultimo = i === ordenados.length - 1;
          return (
            <g key={`${p.data}-${i}`}>
              <circle
                cx={x(p.semana)} cy={y(p.ganho_kg)} r="4.5"
                fill={ultimo ? 'var(--color-vinho, #6B2737)' : '#FFFFFF'}
                stroke="var(--color-vinho, #6B2737)" strokeWidth="2"
              />
              <circle
                cx={x(p.semana)} cy={y(p.ganho_kg)} r="13" fill="transparent" style={{ cursor: 'pointer' }}
                onMouseEnter={() => setSelecionado(p)}
                onClick={(e) => { e.stopPropagation(); setSelecionado(p); }}
              >
                <title>{`Semana ${p.semana}: ${p.ganho_kg >= 0 ? '+' : ''}${kg(p.ganho_kg)} kg`}</title>
              </circle>
            </g>
          );
        })}
      </svg>

      {selecionado && (() => {
        const faixaSel = faixaDaSemana(selecionado.semana);
        return (
          <div
            style={{
              marginTop: '6px', padding: '8px 10px', borderRadius: '8px', backgroundColor: '#FAF6F7',
              border: '1px solid #F0E6E8', fontSize: '0.8rem', color: 'var(--color-text)'
            }}
          >
            <strong>Semana {selecionado.semana}</strong>
            {' · '}{new Date(`${selecionado.data}T12:00:00`).toLocaleDateString('pt-BR')}
            {' · '}{selecionado.ganho_kg >= 0 ? '+' : ''}{kg(selecionado.ganho_kg)} kg desde antes da gravidez
            {faixaSel && (
              <span style={{ display: 'block', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                Faixa recomendada nessa semana: {kg(faixaSel.min_kg)} a {kg(faixaSel.max_kg)} kg
              </span>
            )}
          </div>
        );
      })()}
    </div>
  );
}
