import React, { useState, useEffect } from 'react';
import { 
  Bot, ShieldCheck, AlertTriangle, FileText, X, Sparkles, 
  CheckCircle2, UserCheck, ExternalLink, Info, Activity
} from 'lucide-react';
import { apiFetch } from '../utils/api';

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
            <Activity size={16} /> Matriz de Métricas (6 Modelos)
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
            <AlertTriangle size={16} color="var(--color-dourado)" /> Alerta CDC / ITU (1%)
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

              {/* Aba 1: Matriz de Métricas */}
              {abaAtiva === 'metricas' && (
                <div>
                  <h4 style={{ color: 'var(--color-vinho)', marginTop: 0, marginBottom: '8px' }}>
                    Validação Estatística dos Modelos Preditivos Supervisionados
                  </h4>
                  <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '14px' }}>
                    Modelos ensemble de Machine Learning treinados sobre registros do SINASC e SIH/SUS (DATASUS),
                    calibrados com fatores de risco familiares e antecedentes clínicos:
                  </p>

                  <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                      <thead>
                        <tr style={{ backgroundColor: 'var(--color-creme)', textAlign: 'left', borderBottom: '2px solid var(--color-border)' }}>
                          <th style={{ padding: '8px 10px' }}>Condição Obstétrica</th>
                          <th style={{ padding: '8px 10px' }}>AUC-ROC</th>
                          <th style={{ padding: '8px 10px' }}>Sensibilidade</th>
                          <th style={{ padding: '8px 10px' }}>Especificidade</th>
                          <th style={{ padding: '8px 10px' }}>Precisão</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600 }}>Pré-eclâmpsia</td>
                          <td style={{ padding: '8px 10px', color: '#047857' }}>0.84</td>
                          <td style={{ padding: '8px 10px' }}>78%</td>
                          <td style={{ padding: '8px 10px' }}>76%</td>
                          <td style={{ padding: '8px 10px' }}>71%</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600 }}>Eclâmpsia</td>
                          <td style={{ padding: '8px 10px', color: '#047857' }}>0.82</td>
                          <td style={{ padding: '8px 10px' }}>75%</td>
                          <td style={{ padding: '8px 10px' }}>80%</td>
                          <td style={{ padding: '8px 10px' }}>68%</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600 }}>Diabetes Gestacional</td>
                          <td style={{ padding: '8px 10px', color: '#047857' }}>0.79</td>
                          <td style={{ padding: '8px 10px' }}>72%</td>
                          <td style={{ padding: '8px 10px' }}>74%</td>
                          <td style={{ padding: '8px 10px' }}>69%</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600 }}>Bem-Estar Fetal</td>
                          <td style={{ padding: '8px 10px', color: '#047857' }}>0.81</td>
                          <td style={{ padding: '8px 10px' }}>74%</td>
                          <td style={{ padding: '8px 10px' }}>77%</td>
                          <td style={{ padding: '8px 10px' }}>73%</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600 }}>Malformação Congênita</td>
                          <td style={{ padding: '8px 10px', color: '#047857' }}>0.76</td>
                          <td style={{ padding: '8px 10px' }}>70%</td>
                          <td style={{ padding: '8px 10px' }}>75%</td>
                          <td style={{ padding: '8px 10px' }}>64%</td>
                        </tr>
                        <tr style={{ backgroundColor: '#FEF2F2', borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '8px 10px', fontWeight: 600, color: 'var(--color-vermelho)' }}>
                            Infecção Urinária (ITU) ⚠️
                          </td>
                          <td style={{ padding: '8px 10px' }}>0.65</td>
                          <td style={{ padding: '8px 10px' }}>62%</td>
                          <td style={{ padding: '8px 10px' }}>68%</td>
                          <td style={{ padding: '8px 10px', fontWeight: 700, color: 'var(--color-vermelho)' }}>1% (0.01)</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div style={{ backgroundColor: 'var(--color-creme)', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
                    <div style={{ fontWeight: 700, color: 'var(--color-vinho)', marginBottom: '4px' }}>
                      Detector de Padrões Atípicos (Isolation Forest)
                    </div>
                    <div>
                      Algoritmo de aprendizado não supervisionado treinado para sinalizar perfis que se desviam da distribuição
                      populacional usual (ex: extremos de idade combinados com multiparidade e histórico de cesáreas prévias).
                    </div>
                  </div>
                </div>
              )}

              {/* Aba 2: Alerta CDC / ITU */}
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
                      Dever de Transparência e Boa-Fé Objetiva (CDC Arts. 12-14)
                    </div>
                    <p style={{ margin: 0, fontSize: '0.84rem', color: '#7F1D1D', lineHeight: 1.5 }}>
                      Em conformidade com o Código de Defesa do Consumidor e a Resolução CFM nº 2.454/2026, declaramos
                      expressamente que o modelo preditivo de Infecção do Trato Urinário (ITU) possui <strong>precisão de 0,01 (1%)</strong>.
                    </p>
                  </div>

                  <h5 style={{ color: 'var(--color-vinho)', marginBottom: '6px' }}>Por que a precisão é de 1%?</h5>
                  <p style={{ fontSize: '0.83rem', color: 'var(--color-text-main)', marginBottom: '12px' }}>
                    O treinamento foi baseado no banco de dados hospitalares do SIH/SUS (DATASUS), onde quase a totalidade absoluta
                    dos registros correspondia a partos a termo normais. Apenas internações obstétricas de alta complexidade com
                    sepse ou pielonefrite aguda continham a codificação de ITU como diagnóstico primário gerador da AIH.
                  </p>

                  <h5 style={{ color: 'var(--color-vinho)', marginBottom: '6px' }}>Como este resultado deve ser utilizado?</h5>
                  <ul style={{ fontSize: '0.83rem', paddingLeft: '20px', color: 'var(--color-text-main)', margin: '0 0 16px' }}>
                    <li>
                      <strong>Gatilho de rotina preventiva:</strong> Um score elevado serve apenas como lembrete educativo para que o obstetra
                      ou a gestante verifiquem se a urocultura de rotina do trimestre foi solicitada e realizada.
                    </li>
                    <li>
                      <strong>Proibição de presunção diagnóstica:</strong> Jamais interprete o score como comprovação de bacteriúria ativa,
                      e nunca inicie ou interrompa antibióticos sem o laudo de urocultura com antibiograma.
                    </li>
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
