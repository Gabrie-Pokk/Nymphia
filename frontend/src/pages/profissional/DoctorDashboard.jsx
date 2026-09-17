import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Users, AlertTriangle, Calendar, Clock, ChevronRight, UserPlus, RefreshCw } from 'lucide-react';
import TriageDisclaimer from '../../components/TriageDisclaimer';

export default function DoctorDashboard({ onSelectPatient, onNavigateGenerateInvite }) {
  const { user, authHeaders } = useAuth();
  const [pacientes, setPacientes] = useState([]);
  const [carregando, setCarregando] = useState(true);

  const carregarPacientes = async () => {
    setCarregando(true);
    try {
      const res = await fetch('/vinculo/minhas-gestantes', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setPacientes(data);
      }
    } catch (err) {
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregarPacientes();
  }, []);

  const totalComAlerta = pacientes.filter((p) => p.total_alertas_30d > 0).length;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Painel Obstétrico
          </span>
          <h2 style={{ margin: 0 }}>Dr(a). {user?.nome}</h2>
        </div>
        <button
          className="btn btn-primary"
          onClick={onNavigateGenerateInvite}
          style={{ minHeight: '40px', padding: '8px 14px', fontSize: '0.85rem' }}
        >
          <UserPlus size={16} /> Gerar Convite
        </button>
      </div>

      {/* Resumo de Urgência no Topo */}
      <div
        className="card card-vinho"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 20px',
          marginBottom: '20px'
        }}
      >
        <div>
          <span style={{ fontSize: '0.82rem', color: 'var(--color-rosa-claro)', display: 'block' }}>
            Triagem Priorizada (Últimos 30 dias)
          </span>
          <h3 style={{ color: '#FFFFFF', fontSize: '1.4rem', margin: '4px 0 0 0' }}>
            {totalComAlerta} {totalComAlerta === 1 ? 'paciente com alerta' : 'pacientes com alertas'}
          </h3>
        </div>
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: totalComAlerta > 0 ? 'var(--color-rosa)' : 'rgba(255,255,255,0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF'
          }}
        >
          {totalComAlerta > 0 ? <AlertTriangle size={26} /> : <Users size={26} />}
        </div>
      </div>

      {/* Lista de Pacientes Ordenada por Urgência */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '1.05rem', margin: 0 }}>
          Suas Pacientes ({pacientes.length})
        </h3>
        <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
          Ordenado por gravidade de alertas
        </span>
      </div>

      {carregando ? (
        <p className="text-muted">Carregando lista priorizada...</p>
      ) : pacientes.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
          <Users size={36} color="var(--color-text-muted)" style={{ margin: '0 auto 12px auto' }} />
          <p style={{ fontWeight: 600, color: 'var(--color-vinho)' }}>Nenhuma gestante vinculada ainda</p>
          <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '16px' }}>
            Gere um código de convite de 8 dígitos para conectar suas pacientes ao seu painel.
          </p>
          <button className="btn btn-primary" onClick={onNavigateGenerateInvite}>
            <UserPlus size={18} /> Gerar Primeiro Convite
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {pacientes.map((p) => {
            const temAlerta = p.total_alertas_30d > 0;
            return (
              <div
                key={p.gestante_id}
                className="card"
                style={{
                  margin: 0,
                  padding: '14px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  borderLeft: temAlerta ? '5px solid var(--color-vermelho)' : '5px solid #27AE60',
                  backgroundColor: temAlerta ? '#FFF8F8' : 'var(--color-surface-card)'
                }}
                onClick={() => onSelectPatient(p.gestante_id)}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-vinho)' }}>
                      {p.nome}
                    </h4>
                    {p.semana_gestacional && (
                      <span className="badge-rosa" style={{ fontSize: '0.72rem' }}>
                        {p.semana_gestacional}ª sem
                      </span>
                    )}
                    {temAlerta && (
                      <span
                        style={{
                          backgroundColor: 'var(--color-vermelho)',
                          color: '#FFFFFF',
                          padding: '2px 8px',
                          borderRadius: 'var(--radius-full)',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '3px'
                        }}
                      >
                        <AlertTriangle size={12} /> {p.total_alertas_30d} {p.total_alertas_30d === 1 ? 'alerta' : 'alertas'}
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                    <span>Último check-in: <strong>{p.ultimo_checkin_relativo}</strong></span>
                    {p.proxima_consulta && (
                      <span>
                        Próx. Consulta: <strong>{new Date(p.proxima_consulta).toLocaleDateString('pt-BR')}</strong>
                      </span>
                    )}
                  </div>
                </div>

                <ChevronRight size={20} color="var(--color-text-muted)" />
              </div>
            );
          })}
        </div>
      )}

      <TriageDisclaimer />
    </div>
  );
}
