import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { FileText, CheckCircle, ShieldCheck, Heart, User, Calendar, Syringe } from 'lucide-react';

const VACINAS_PADRAO = [
  { nome: "dTpa (Difteria, Tétano e Coqueluche)", periodo: "A partir da 20ª semana", status: "Recomendada" },
  { nome: "Hepatite B (3 doses)", periodo: "Início do pré-natal", status: "Recomendada" },
  { nome: "Influenza (Gripe)", periodo: "Dose única em qualquer trimestre", status: "Recomendada" },
  { nome: "Covid-19 Bivalente", periodo: "Conforme calendário do PNI", status: "Recomendada" }
];

export default function PrenatalCard({ onBack }) {
  const { user, authHeaders } = useAuth();
  const [perfil, setPerfil] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [exames, setExames] = useState([]);
  const [riscos, setRiscos] = useState(null);

  useEffect(() => {
    fetch('/perfil-clinico', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setPerfil(data))
      .catch(() => {});

    fetch('/historico-familiar', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setHistorico(data))
      .catch(() => {});

    fetch('/exames', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setExames(data))
      .catch(() => {});

    fetch('/risco/meu-risco', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setRiscos(data))
      .catch(() => {});
  }, []);

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <h2>Caderneta Digital de Pré-Natal</h2>
          <p className="text-muted" style={{ fontSize: '0.82rem' }}>
            Padrão Ministério da Saúde / FEBRASGO para apresentação em consulta
          </p>
        </div>
        <span className="badge-gold">Oficial</span>
      </div>

      {/* Cartão de Identificação da Gestante */}
      <div className="card" style={{ backgroundColor: '#FFFFFF', border: '2px solid var(--color-vinho)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <User size={20} color="var(--color-vinho)" />
          <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Identificação da Gestante</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.85rem' }}>
          <div>
            <strong style={{ color: 'var(--color-text-muted)', display: 'block' }}>Nome:</strong>
            <span style={{ fontWeight: 600, color: 'var(--color-vinho)' }}>{user?.nome}</span>
          </div>
          <div>
            <strong style={{ color: 'var(--color-text-muted)', display: 'block' }}>Idade:</strong>
            <span>{perfil?.idade ? `${perfil.idade} anos` : 'Não informada'}</span>
          </div>
          <div>
            <strong style={{ color: 'var(--color-text-muted)', display: 'block' }}>DUM:</strong>
            <span>{perfil?.dum ? new Date(perfil.dum + 'T12:00:00').toLocaleDateString('pt-BR') : 'N/A'}</span>
          </div>
          <div>
            <strong style={{ color: 'var(--color-text-muted)', display: 'block' }}>DPP:</strong>
            <span style={{ fontWeight: 700, color: 'var(--color-rosa)' }}>
              {perfil?.dpp ? new Date(perfil.dpp + 'T12:00:00').toLocaleDateString('pt-BR') : 'N/A'}
            </span>
          </div>
          <div>
            <strong style={{ color: 'var(--color-text-muted)', display: 'block' }}>Gestações / Partos:</strong>
            <span>G{perfil ? perfil.gestacoes_anteriores + 1 : 1} P{perfil?.partos_normais + perfil?.partos_cesareos || 0} A{perfil?.perdas_gestacionais || 0}</span>
          </div>
          <div>
            <strong style={{ color: 'var(--color-text-muted)', display: 'block' }}>Maternidade Ref.:</strong>
            <span>{perfil?.maternidade_nome || 'A definir'}</span>
          </div>
        </div>
      </div>

      {/* Histórico Familiar Relevante */}
      <div className="card">
        <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Histórico Familiar de Saúde</h3>
        {historico.length === 0 ? (
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>Sem condições familiares específicas registradas.</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {historico.map((h) => (
              <span key={h.id} className="badge-rosa" style={{ fontSize: '0.78rem' }}>
                {h.parente}: {h.condicao}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Calendário Vacinal Obrigatório */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Syringe size={18} color="var(--color-rosa)" />
          <h3 style={{ fontSize: '1rem', margin: 0 }}>Vacinas do Pré-Natal (PNI)</h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {VACINAS_PADRAO.map((v, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                backgroundColor: '#FFFFFF',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div>
                <strong style={{ fontSize: '0.85rem', color: 'var(--color-vinho)', display: 'block' }}>{v.nome}</strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{v.periodo}</span>
              </div>
              <span className="badge-gold" style={{ fontSize: '0.7rem' }}>{v.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Registro de Exames Laboratoriais */}
      <div className="card">
        <h3 style={{ fontSize: '1rem', marginBottom: '10px' }}>Exames Laboratoriais Registrados</h3>
        {exames.length === 0 ? (
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>Nenhum laudo enviado até o momento.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {exames.map((ex) => (
              <div
                key={ex.id}
                style={{
                  padding: '10px 12px',
                  backgroundColor: '#FFFFFF',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.85rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <strong style={{ color: 'var(--color-vinho)' }}>{ex.tipo}</strong>
                  <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                    {new Date(ex.data_realizacao + 'T12:00:00').toLocaleDateString('pt-BR')}
                  </span>
                </div>
                {ex.valores_extraidos && (
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', margin: 0 }}>
                    Extração OCR: {JSON.stringify(ex.valores_extraidos).slice(0, 100)}...
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
