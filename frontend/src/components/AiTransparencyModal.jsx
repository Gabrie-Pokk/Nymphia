import React, { useState, useEffect } from 'react';
import { 
  Bot, ShieldCheck, AlertTriangle, FileText, X, Sparkles, 
  CheckCircle2, UserCheck, ExternalLink, Info, Activity
} from 'lucide-react';
import { apiFetch } from '../utils/api';

const ROTULO_FATOR = {
  pre_eclampsia_previa: 'Pré-eclâmpsia anterior',
  hipertensao_cronica: 'Pressão alta antes da gravidez',
  diabetes_previo: 'Diabetes antes da gravidez',
  imc_baixo_peso: 'IMC abaixo de 18,5',
  imc_sobrepeso: 'IMC de 25 a 29,9',
  imc_obesidade: 'IMC de 30 ou mais',
  gemeos: 'Gêmeos',
  historico_familiar_pe: 'Mãe com pré-eclâmpsia',
  historico_familiar_dm: 'Diabetes na família'
};

export default function AiTransparencyModal({ isOpen, onClose }) {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [abaAtiva, setAbaAtiva] = useState('metricas'); // 'metricas' | 'regulatorio' | 'itu'

  useEffect(() => {
    if (!isOpen) return;
    setCarregando(true);
    apiFetch('/modelos/transparencia-clinica', { skipAuth: true })
      .then((res) => setDados(res))
      .catch(() => null)
      .finally(() => setCarregando(false));
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(44, 24, 30, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: 'var(--radius-lg)',
          width: '100%',
          maxWidth: '720px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
          overflow: 'hidden'
        }}
      >
        {/* Cabeçalho */}
        <div
          style={{
            padding: '16px 20px',
            backgroundColor: 'var(--color-vinho)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'rgba(255,255,255,0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Bot size={20} color="var(--color-dourado)" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.05rem', color: '#FFFFFF', fontWeight: 700 }}>
                Governança de IA & Transparência Clínica
              </h3>
              <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.85)' }}>
                Resolução CFM nº 2.454/2026 • Código de Defesa do Consumidor • RDC Anvisa 657/2022
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#FFFFFF',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        {/* Barra de Abas */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-creme)'
          }}
        >
          <button
            onClick={() => setAbaAtiva('metricas')}
            style={{
              flex: 1,
              padding: '10px 14px',
              border: 'none',
              background: abaAtiva === 'metricas' ? '#FFFFFF' : 'transparent',
              borderBottom: abaAtiva === 'metricas' ? '3px solid var(--color-rosa)' : '3px solid transparent',
              color: abaAtiva === 'metricas' ? 'var(--color-vinho)' : 'var(--color-text-muted)',
              fontWeight: abaAtiva === 'metricas' ? 700 : 500,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <Activity size={16} /> Métricas reais dos modelos
          </button>
          <button
            onClick={() => setAbaAtiva('itu')}
            style={{
              flex: 1,
              padding: '10px 14px',
              border: 'none',
              background: abaAtiva === 'itu' ? '#FFFFFF' : 'transparent',
              borderBottom: abaAtiva === 'itu' ? '3px solid var(--color-rosa)' : '3px solid transparent',
              color: abaAtiva === 'itu' ? 'var(--color-vinho)' : 'var(--color-text-muted)',
              fontWeight: abaAtiva === 'itu' ? 700 : 500,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <AlertTriangle size={16} color="var(--color-dourado)" /> Infecção urinária
          </button>
          <button
            onClick={() => setAbaAtiva('regulatorio')}
            style={{
              flex: 1,
              padding: '10px 14px',
              border: 'none',
              background: abaAtiva === 'regulatorio' ? '#FFFFFF' : 'transparent',
              borderBottom: abaAtiva === 'regulatorio' ? '3px solid var(--color-rosa)' : '3px solid transparent',
              color: abaAtiva === 'regulatorio' ? 'var(--color-vinho)' : 'var(--color-text-muted)',
              fontWeight: abaAtiva === 'regulatorio' ? 700 : 500,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <ShieldCheck size={16} /> Marco Regulatório SaMD
          </button>
        </div>

        {/* Conteúdo com Rolagem */}
        <div style={{ padding: '20px', overflowY: 'auto', flex: 1, fontSize: '0.88rem', lineHeight: 1.55 }}>
          {carregando ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>
              Carregando relatório oficial de governança...
            </div>
          ) : (
            <>
              {/* Alerta Institucional de Não Substituição Médica */}
              <div
                style={{
                  backgroundColor: '#FFFBEB',
                  border: '1.5px solid var(--color-dourado)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  marginBottom: '16px',
                  display: 'flex',
                  gap: '10px',
                  alignItems: 'flex-start'
                }}
              >
                <Info size={20} color="var(--color-dourado)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '0.82rem', color: '#78350F' }}>
                  <strong>Aviso Mandatório (Resolução CFM nº 2.454/2026, Art. 5º, §2º):</strong> A inteligência artificial
                  Nymphia opera estritamente como ferramenta de suporte e triagem preditiva populacional. É expressamente
                  vedado ao sistema emitir diagnósticos definitivos ou prescrever condutas de forma autônoma. Decisões clínicas
                  cabem exclusivamente ao médico obstetra assistente.
                </div>
              </div>

              {/* Aba 1: métricas reais do treino v2, lidas do servidor */}
              {abaAtiva === 'metricas' && (
                <div>
                  <h4 style={{ color: 'var(--color-vinho)', marginTop: 0, marginBottom: '8px' }}>
                    Como os modelos foram avaliados
                  </h4>
                  <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '10px' }}>
                    Números de teste em dados reais que o modelo nunca viu. Os modelos só usam o que se sabe durante a
                    gestação. {dados?.como_ler}
                  </p>

                  {!dados?.modelos ? (
                    <p className="text-muted" style={{ fontSize: '0.82rem' }}>Não foi possível carregar as métricas agora.</p>
                  ) : (
                    <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                        <thead>
                          <tr style={{ backgroundColor: 'var(--color-creme)', textAlign: 'left', borderBottom: '2px solid var(--color-border)' }}>
                            <th style={{ padding: '8px 10px' }}>Condição</th>
                            <th style={{ padding: '8px 10px' }}>AUC (dados reais)</th>
                            <th style={{ padding: '8px 10px' }}>Comparação</th>
                            <th style={{ padding: '8px 10px' }}>Sensibilidade</th>
                            <th style={{ padding: '8px 10px' }}>Especificidade</th>
                            <th style={{ padding: '8px 10px' }}>Gestantes sinalizadas</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(dados.modelos).map(([chave, m]) => {
                            const pct = (v) => (typeof v === 'number' ? `${Math.round(v * 100)}%` : '-');
                            const num = (v) => (typeof v === 'number' ? v.toFixed(2).replace('.', ',') : '-');
                            const indisponivel = chave === 'itu';
                            const versao = m.simulado ? 'v3, simulação' : m.versao === '3.0' ? 'v3' : 'v2';
                            const comparacao = m.versao === '3.0'
                              ? `v2 nos mesmos dados: ${num(m.auc_roc_v2_nos_mesmos_dados)}`
                              : `só com a idade: ${num(m.auc_roc_so_com_idade)}`;
                            return (
                              <tr key={chave} style={{ borderBottom: '1px solid var(--color-border)', backgroundColor: indisponivel ? '#FEF2F2' : 'transparent' }}>
                                <td style={{ padding: '8px 10px', fontWeight: 600 }}>
                                  {m.nome_clinico}{indisponivel ? ' (indisponível)' : ''}
                                  <span style={{ display: 'block', fontWeight: 400, fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{versao}</span>
                                </td>
                                <td style={{ padding: '8px 10px' }}>{num(m.auc_roc)}</td>
                                <td style={{ padding: '8px 10px', color: 'var(--color-text-muted)' }}>{comparacao}</td>
                                <td style={{ padding: '8px 10px' }}>{pct(m.sensibilidade)}</td>
                                <td style={{ padding: '8px 10px' }}>{pct(m.especificidade)}</td>
                                <td style={{ padding: '8px 10px' }}>{pct(m.fracao_sinalizada_no_ponto)}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}

                  <div style={{ backgroundColor: 'var(--color-creme)', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
                    <div style={{ fontWeight: 700, color: 'var(--color-vinho)', marginBottom: '4px' }}>
                      O que esses números querem dizer
                    </div>
                    <div>
                      As bases públicas do DATASUS não registram os fatores mais fortes (pré-eclâmpsia anterior, pressão alta
                      ou diabetes de antes da gravidez, IMC). Na versão 3 esses fatores entram por simulação: o efeito de
                      cada um vem de estudos publicados. Nos dados reais, com os fatores desconhecidos, o desempenho ficou
                      igual ao da versão 2. A simulação não faz o modelo acertar mais em dados reais: ela faz a estimativa
                      mudar quando a gestante informa um fator, na medida que os estudos mostram. Os alarmes do check-in não
                      dependem destes modelos: são regras clínicas feitas para não deixar passar sinais de urgência.
                    </div>
                  </div>

                  {dados?.simulacao && (
                    <div style={{ marginTop: '14px' }}>
                      <h4 style={{ color: 'var(--color-vinho)', margin: '0 0 6px' }}>Fatores simulados: efeito publicado e efeito no modelo</h4>
                      <p className="text-muted" style={{ fontSize: '0.78rem', margin: '0 0 8px' }}>{dados.simulacao.o_que_e}</p>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.76rem' }}>
                          <thead>
                            <tr style={{ backgroundColor: 'var(--color-creme)', textAlign: 'left' }}>
                              <th style={{ padding: '6px 8px' }}>Condição</th>
                              <th style={{ padding: '6px 8px' }}>Fator</th>
                              <th style={{ padding: '6px 8px' }}>Razão de chances publicada</th>
                              <th style={{ padding: '6px 8px' }}>No modelo</th>
                              <th style={{ padding: '6px 8px' }}>Fonte</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(dados.modelos).flatMap(([chave, m]) =>
                              Object.entries(m.efeitos_dos_fatores || {}).map(([fator, e]) => (
                                <tr key={`${chave}-${fator}`} style={{ borderTop: '1px solid var(--color-border)' }}>
                                  <td style={{ padding: '6px 8px' }}>{m.nome_clinico}</td>
                                  <td style={{ padding: '6px 8px' }}>{ROTULO_FATOR[fator] || fator.replace(/_/g, ' ')}</td>
                                  <td style={{ padding: '6px 8px' }}>{String(e.razao_de_chances_publicada ?? '-').replace('.', ',')}</td>
                                  <td style={{ padding: '6px 8px' }}>{String(e.razao_de_chances_no_modelo ?? '-').replace('.', ',')}</td>
                                  <td style={{ padding: '6px 8px', color: 'var(--color-text-muted)' }}>{dados.simulacao.fontes?.[e.fonte] || e.fonte}</td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                      {dados.simulacao.suposicoes?.length > 0 && (
                        <ul style={{ fontSize: '0.76rem', margin: '8px 0 0', paddingLeft: '18px', color: 'var(--color-text-muted)' }}>
                          {dados.simulacao.suposicoes.map((t, i) => <li key={i}>{t}</li>)}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Aba 2: infecção urinária */}
              {abaAtiva === 'itu' && (
                <div>
                  <div
                    style={{
                      borderLeft: '4px solid var(--color-vermelho)',
                      backgroundColor: '#FEF2F2',
                      padding: '16px',
                      borderRadius: 'var(--radius-sm)',
                      marginBottom: '16px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-vermelho)', fontWeight: 700, fontSize: '0.95rem', marginBottom: '8px' }}>
                      <AlertTriangle size={18} />
                      Infecção urinária: sem modelo por enquanto
                    </div>
                    <p style={{ margin: 0, fontSize: '0.84rem', color: '#7F1D1D', lineHeight: 1.5 }}>
                      {dados?.modelos?.itu?.aviso || 'A base de treino não tinha casos suficientes.'}
                    </p>
                  </div>
                  <h5 style={{ color: 'var(--color-vinho)', marginBottom: '6px' }}>O que vale enquanto isso</h5>
                  <ul style={{ fontSize: '0.83rem', paddingLeft: '20px', color: 'var(--color-text-main)', margin: '0 0 16px' }}>
                    <li>A urocultura de rotina do pré-natal é o caminho para encontrar infecção sem sintomas.</li>
                    <li>Ardor ao urinar, febre ou dor nas costas são avaliados pelas regras do check-in, que avisam na hora.</li>
                  </ul>
                </div>
              )}

              {/* Aba 3: Marco Regulatório & Direitos */}
              {abaAtiva === 'regulatorio' && (
                <div>
                  <h4 style={{ color: 'var(--color-vinho)', marginTop: 0, marginBottom: '10px' }}>
                    Enquadramento Regulatório & Proteção Jurídica
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                      <strong style={{ color: 'var(--color-vinho)' }}>Classificação SaMD (Anvisa / CFM):</strong>
                      <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: 'var(--color-text-main)' }}>
                        O sistema Nymphia enquadra-se como Software as a Medical Device (SaMD) de Risco Médio (Classe II),
                        segundo a RDC Anvisa nº 657/2022 e o Anexo II da Resolução CFM nº 2.454/2026.
                      </p>
                    </div>

                    <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                      <strong style={{ color: 'var(--color-vinho)' }}>Carimbo Auditável em Prontuário (Art. 4º, V):</strong>
                      <div style={{ fontStyle: 'italic', backgroundColor: 'var(--color-creme)', padding: '8px', borderRadius: '4px', marginTop: '6px', fontSize: '0.8rem' }}>
                        "{dados?.carimbo_prontuario || 'Informações apoiadas por algoritmos preditivos de Inteligência Artificial (SaMD - CFM nº 2.454/2026). Decisão diagnóstica privativa do médico assistente.'}"
                      </div>
                    </div>

                    <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-rosa-claro)' }}>
                      <strong style={{ color: 'var(--color-vinho)' }}>Direito à Revisão Humana (Art. 20 da LGPD):</strong>
                      <p style={{ margin: '4px 0 8px', fontSize: '0.82rem', color: 'var(--color-text-main)' }}>
                        Você tem o direito inalienável de solicitar a reavaliação de qualquer sinalização ou cálculo estatístico por um profissional médico qualificado.
                      </p>
                      <span style={{ fontSize: '0.78rem', color: 'var(--color-rosa)', fontWeight: 600 }}>
                        Acesse a aba "Meus Dados & LGPD" no menu principal para submeter sua solicitação formal de revisão.
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Rodapé */}
        <div
          style={{
            padding: '14px 20px',
            backgroundColor: 'var(--color-creme)',
            borderTop: '1px solid var(--color-border)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '10px'
          }}
        >
          <button className="btn btn-primary" onClick={onClose} style={{ minHeight: '36px', padding: '6px 16px', fontSize: '0.84rem' }}>
            Compreendido e Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
