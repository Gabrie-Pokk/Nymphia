import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import AiTransparencyModal from '../../components/AiTransparencyModal';
import ResumoRiscos from '../../components/ResumoRiscos';
import { User, Activity, AlertTriangle, FileText, MessageSquare, Plus, CheckCircle2, ShieldCheck, Heart, Info, Bot } from 'lucide-react';

export default function PatientRecord({ patientId, onBack }) {
  const { authHeaders } = useAuth();
  const [ficha, setFicha] = useState(null);
  const [novaObservacao, setNovaObservacao] = useState('');
  const [carregando, setCarregando] = useState(true);
  const [salvandoObs, setSalvandoObs] = useState(false);
  const [sucessoObs, setSucessoObs] = useState('');
  const [modalIaAberto, setModalIaAberto] = useState(false);

  const carregarFicha = async () => {
    setCarregando(true);
    try {
      const res = await fetch(`/vinculo/paciente/${patientId}/ficha`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setFicha(data);
      }
    } catch (err) {
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregarFicha();
  }, [patientId]);

  const handleSalvarObservacao = async (e) => {
    e.preventDefault();
    if (!novaObservacao.trim()) return;

    setSalvandoObs(true);
    try {
      const res = await fetch(`/vinculo/paciente/${patientId}/observacao`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ observacao: novaObservacao.trim() })
      });
      if (res.ok) {
        setNovaObservacao('');
        setSucessoObs('Observação médica registrada com sucesso.');
        carregarFicha();
      }
    } catch (err) {
    } finally {
      setSalvandoObs(false);
    }
  };

  if (carregando) {
    return <div style={{ padding: '24px' }}>Carregando prontuário da paciente...</div>;
  }

  if (!ficha) {
    return (
      <div style={{ padding: '24px' }}>
        <BackButton onClick={onBack} label="Voltar ao Painel" />
        <p>Prontuário não disponível ou vínculo não autorizado.</p>
      </div>
    );
  }

  const { identificacao, perfil_clinico, historico_familiar, riscos_calculados, checkins, exames, mensagens_autorizadas, observacoes_medicas } = ficha;
  const triagensEpds = ficha.triagens_epds || [];
  const NIVEL_EPDS = {
    urgente: { rotulo: 'Pergunta 10 positiva', cor: 'var(--color-vermelho, #C0392B)' },
    atencao: { rotulo: 'Triagem positiva (10 ou mais)', cor: '#B45309' },
    sem_sinais: { rotulo: 'Abaixo do corte', cor: '#1E7A46' }
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar ao Painel de Pacientes" />

      {/* Header da Paciente */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-rosa)', fontWeight: 700, textTransform: 'uppercase' }}>
            Prontuário Médico (Somente Leitura)
          </span>
          <h2 style={{ margin: '4px 0 0 0' }}>{identificacao?.nome}</h2>
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>{identificacao?.email}</p>
        </div>
        <span className="badge-gold">Auditoria LGPD Ativa</span>
      </div>

      <TriageDisclaimer />

      {/* Dados Clínicos do Onboarding */}
      <div className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '10px' }}>Histórico Obstétrico & Pessoal</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.85rem' }}>
          <div><strong>Idade:</strong> {perfil_clinico?.idade} anos</div>
          <div><strong>Estado Civil:</strong> {perfil_clinico?.estado_civil || 'Não informado'}</div>
          <div><strong>DUM:</strong> {perfil_clinico?.dum ? new Date(perfil_clinico.dum + 'T12:00:00').toLocaleDateString('pt-BR') : 'N/A'}</div>
          <div>
            <strong>DPP:</strong>{' '}
            <span style={{ color: 'var(--color-rosa)', fontWeight: 700 }}>
              {perfil_clinico?.dpp ? new Date(perfil_clinico.dpp + 'T12:00:00').toLocaleDateString('pt-BR') : 'N/A'}
            </span>
          </div>
          <div><strong>Gestações Anteriores:</strong> {perfil_clinico?.gestacoes_anteriores}</div>
          <div><strong>Perdas:</strong> {perfil_clinico?.perdas_gestacionais}</div>
          <div><strong>Cesáreas:</strong> {perfil_clinico?.partos_cesareos}</div>
          <div><strong>Partos Normais:</strong> {perfil_clinico?.partos_normais}</div>
        </div>
      </div>

      {/* Riscos Obstétricos Calculados (6 Condições CFM 2.454) */}
      <div className="card" style={{ borderLeft: '5px solid var(--color-dourado)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Rastreio Estatístico Populacional (SINASC/SIH)</h3>
            <span style={{ fontSize: '0.72rem', color: 'var(--color-vinho)', fontWeight: 600 }}>
              🛡️ SaMD Classe II • Resolução CFM nº 2.454/2026 (Art. 4º, V)
            </span>
          </div>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => setModalIaAberto(true)}
            style={{ fontSize: '0.75rem', padding: '4px 8px', minHeight: '28px', borderColor: 'var(--color-dourado)' }}
          >
            <Bot size={14} color="var(--color-dourado)" /> Governança & Métricas de IA
          </button>
        </div>

        <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: '12px' }}>
          Estimativas com dados do DATASUS e, na versão 3, fatores clínicos simulados a partir de estudos publicados,
          calculadas com o cadastro da paciente:
        </p>

        <ResumoRiscos riscos={riscos_calculados} modo="profissional" />

        {/* Carimbo de Prontuário CFM 2.454/2026 */}
        <div style={{ marginTop: '12px', padding: '10px 12px', backgroundColor: 'var(--color-creme)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: '0.74rem', color: 'var(--color-vinho)', lineHeight: '1.4' }}>
          <strong>Carimbo Auditável de Prontuário (CFM 2.454/2026):</strong>{' '}
          {riscos_calculados?.carimbo_samd_cfm || 'Triagem com suporte de IA supervisionada (SaMD Classe II / CFM nº 2.454/2026). Decisão diagnóstica privativa do médico obstetra assistente.'}
        </div>
      </div>

      <AiTransparencyModal isOpen={modalIaAberto} onClose={() => setModalIaAberto(false)} />

      {/* Histórico Recente de Check-ins */}
      <div className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '10px' }}>Linha do Tempo de Check-ins Diários</h3>
        {checkins && checkins.length === 0 ? (
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>Nenhum check-in realizado pela paciente.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '220px', overflowY: 'auto' }}>
            {checkins.map((c) => (
              <div key={c.id} style={{ padding: '8px 10px', backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <strong>{new Date(c.data_hora).toLocaleString('pt-BR')}</strong>
                  <span className="badge-gold" style={{ fontSize: '0.68rem' }}>Humor {c.humor}/5</span>
                </div>
                {c.descricao && <p style={{ margin: '2px 0', color: 'var(--color-text-main)' }}>"{c.descricao}"</p>}
                {c.alerta_sintoma_fisico && c.alerta_sintoma_fisico.length > 0 && (
                  <span style={{ color: 'var(--color-vermelho)', fontWeight: 700, fontSize: '0.75rem' }}>
                    ⚠️ Alertas: {c.alerta_sintoma_fisico.join(', ')}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Triagem emocional (EPDS) */}
      <div className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Triagem Emocional (EPDS)</h3>
        {triagensEpds.length === 0 ? (
          <p className="text-muted" style={{ fontSize: '0.85rem', margin: 0 }}>A paciente ainda não respondeu à escala.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--color-text-muted)' }}>
                <th style={{ padding: '4px 6px' }}>Data</th>
                <th style={{ padding: '4px 6px' }}>Semana</th>
                <th style={{ padding: '4px 6px' }}>Pontos</th>
                <th style={{ padding: '4px 6px' }}>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {triagensEpds.map((t) => (
                <tr key={t.id} style={{ borderTop: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '4px 6px' }}>{new Date(t.data_hora).toLocaleString('pt-BR')}</td>
                  <td style={{ padding: '4px 6px' }}>{t.semana_gestacional ?? '-'}</td>
                  <td style={{ padding: '4px 6px' }}>{t.pontuacao}/30</td>
                  <td style={{ padding: '4px 6px', color: NIVEL_EPDS[t.nivel]?.cor, fontWeight: 700 }}>
                    {NIVEL_EPDS[t.nivel]?.rotulo || t.nivel}
                    {t.pensamento_de_se_machucar ? ' · pensamento de se machucar' : ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="text-muted" style={{ fontSize: '0.72rem', margin: '8px 0 0' }}>
          Escala de Edimburgo. Corte de triagem: 10 ou mais (validação brasileira, Santos et al., 2007).
          Qualquer resposta positiva na pergunta 10 pede avaliação do risco de suicídio. Triagem não é diagnóstico.
        </p>
      </div>

      {/* Trechos de Conversa Autorizados */}
      <div className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Conversas Autorizadas pela Gestante</h3>
        <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: '10px' }}>
          Apenas mensagens que a paciente autorizou explicitamente compartilhar aparecem aqui:
        </p>

        {mensagens_autorizadas && mensagens_autorizadas.length === 0 ? (
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>Nenhum trecho de conversa compartilhado ainda.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {mensagens_autorizadas.map((m) => (
              <div key={m.id} style={{ padding: '8px 12px', backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--color-rosa)' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                  {new Date(m.data_hora).toLocaleString('pt-BR')}
                </span>
                <p style={{ fontSize: '0.85rem', margin: '4px 0 0 0' }}>"{m.conteudo}"</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Campo Próprio para Observações Médicas (REGRA SEÇÃO 7.2) */}
      <div className="card" style={{ border: '2px solid var(--color-vinho)' }}>
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Suas Observações Médicas (Campo Exclusivo)</h3>
        <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '12px' }}>
          O profissional nunca edita o registro da gestante. Suas anotações clínicas são salvas em campo próprio auditado:
        </p>

        {sucessoObs && (
          <div style={{ padding: '8px 12px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-sm)', marginBottom: '12px', fontSize: '0.82rem' }}>
            {sucessoObs}
          </div>
        )}

        <form onSubmit={handleSalvarObservacao}>
          <div className="form-group" style={{ marginBottom: '10px' }}>
            <textarea
              className="form-control"
              rows={3}
              placeholder="Digite suas observações de conduta, orientações da consulta ou prescrições..."
              value={novaObservacao}
              onChange={(e) => setNovaObservacao(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-vinho"
            style={{ width: '100%' }}
            disabled={salvandoObs}
          >
            {salvandoObs ? 'Salvando...' : 'Adicionar Observação Clínica'}
          </button>
        </form>

        {observacoes_medicas && observacoes_medicas.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '8px' }}>Histórico de Anotações Salvas:</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {observacoes_medicas.map((obs) => (
                <div key={obs.id} style={{ padding: '8px 12px', backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: '0.85rem' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                    Registrado em: {new Date(obs.criado_em).toLocaleString('pt-BR')}
                  </span>
                  <p style={{ margin: '4px 0 0 0', color: 'var(--color-vinho)', fontWeight: 500 }}>
                    {obs.observacao}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
