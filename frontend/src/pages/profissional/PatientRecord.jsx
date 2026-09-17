import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import { User, Activity, AlertTriangle, FileText, MessageSquare, Plus, CheckCircle2, ShieldCheck, Heart } from 'lucide-react';

export default function PatientRecord({ patientId, onBack }) {
  const { authHeaders } = useAuth();
  const [ficha, setFicha] = useState(null);
  const [novaObservacao, setNovaObservacao] = useState('');
  const [carregando, setCarregando] = useState(true);
  const [salvandoObs, setSalvandoObs] = useState(false);
  const [sucessoObs, setSucessoObs] = useState('');

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
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Rastreio Estatístico Populacional (SINASC/SIH)</h3>
        <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: '12px' }}>
          Triagem multivariada baseada no perfil e histórico familiar da paciente:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          {riscos_calculados?.condicoes && Object.entries(riscos_calculados.condicoes).map(([cond, val]) => (
            <div
              key={cond}
              style={{
                backgroundColor: '#FFFFFF',
                padding: '10px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong style={{ fontSize: '0.82rem', textTransform: 'capitalize' }}>
                  {cond.replace(/_/g, ' ')}
                </strong>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: val.nivel === 'alto' ? 'var(--color-vermelho)' : val.nivel === 'moderado' ? '#D97706' : '#27AE60'
                  }}
                >
                  {val.nivel.toUpperCase()} ({Math.round(val.probabilidade * 100)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

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
