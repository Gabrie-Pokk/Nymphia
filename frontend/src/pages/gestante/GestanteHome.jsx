import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Calendar, MessageSquare, Users, CheckCircle, Activity, Heart, Shield, FileText, Camera, Bluetooth, ChevronRight, AlertCircle, Link } from 'lucide-react';
import TriageDisclaimer from '../../components/TriageDisclaimer';

export default function GestanteHome({ onNavigate }) {
  const { user, authHeaders } = useAuth();
  const [perfil, setPerfil] = useState(null);
  const [checkinHoje, setCheckinHoje] = useState(false);
  const [proximoEvento, setProximoEvento] = useState(null);
  const [semana, setSemana] = useState(24);
  const [diasSemana, setDiasSemana] = useState(3);

  useEffect(() => {
    // 1. Carrega perfil
    fetch('/perfil-clinico', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setPerfil(data);
          if (data.dum) {
            const dumDate = new Date(data.dum + 'T12:00:00');
            const hoje = new Date();
            const diffDias = Math.floor((hoje - dumDate) / (1000 * 60 * 60 * 24));
            if (diffDias > 0) {
              setSemana(Math.floor(diffDias / 7));
              setDiasSemana(diffDias % 7);
            }
          }
        }
      })
      .catch(() => {});

    // 2. Verifica se checkin de hoje foi feito
    fetch('/checkin/historico?limite=1', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (data && data.length > 0) {
          const ultimo = new Date(data[0].data_hora);
          const hoje = new Date();
          if (ultimo.toDateString() === hoje.toDateString()) {
            setCheckinHoje(true);
          }
        }
      })
      .catch(() => {});

    // 3. Próximo evento da agenda
    fetch('/agenda/eventos?apenas_futuros=true', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (data && data.length > 0) {
          setProximoEvento(data[0]);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div>
      {/* Saudação e Semana Gestacional */}
      <div className="card card-vinho" style={{ position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'relative', zIndex: 2 }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--color-rosa-claro)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Olá, {user?.nome?.split(' ')[0]}
          </span>
          <h2 style={{ fontSize: '1.6rem', marginTop: '4px', marginBottom: '8px' }}>
            {semana}ª Semana + {diasSemana} dias
          </h2>
          <p style={{ fontSize: '0.88rem', opacity: 0.9 }}>
            O bebê já responde a estímulos sonoros e os pulmões produzem surfactante.
          </p>

          <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
            <span className="badge-gold">
              DPP: {perfil?.dpp ? new Date(perfil.dpp + 'T12:00:00').toLocaleDateString('pt-BR') : 'A calcular'}
            </span>
          </div>
        </div>
      </div>

      {/* Cartão de Status do Check-in Diário */}
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          borderLeft: checkinHoje ? '5px solid #27AE60' : '5px solid var(--color-rosa)'
        }}
        onClick={() => onNavigate('/checkin')}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              backgroundColor: checkinHoje ? '#E8F8F0' : 'var(--color-rosa-claro)',
              color: checkinHoje ? '#27AE60' : 'var(--color-rosa)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {checkinHoje ? <CheckCircle size={24} /> : <Activity size={24} />}
          </div>
          <div>
            <h3 style={{ fontSize: '1rem', margin: 0 }}>
              {checkinHoje ? 'Check-in Diário Concluído' : 'Realizar Check-in de Hoje'}
            </h3>
            <p className="text-muted" style={{ fontSize: '0.82rem' }}>
              {checkinHoje ? 'IA analisou seu humor e sintomas' : 'Como você e seu bebê estão se sentindo?'}
            </p>
          </div>
        </div>
        <ChevronRight size={20} color="var(--color-text-muted)" />
      </div>

      {/* Próximo Evento da Agenda */}
      {proximoEvento && (
        <div
          className="card"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          onClick={() => onNavigate('/agenda')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-rosa-claro)',
                color: 'var(--color-vinho)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Calendar size={22} />
            </div>
            <div>
              <span className="badge-rosa" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                Próximo Compromisso
              </span>
              <h3 style={{ fontSize: '0.98rem', marginTop: '2px', marginBottom: 0 }}>
                {proximoEvento.titulo}
              </h3>
              <p className="text-muted" style={{ fontSize: '0.8rem' }}>
                {new Date(proximoEvento.data_hora).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}
              </p>
            </div>
          </div>
          <ChevronRight size={20} color="var(--color-text-muted)" />
        </div>
      )}

      {/* Ações e Módulos Rápidos */}
      <h3 style={{ marginTop: '24px', marginBottom: '12px', fontSize: '1.05rem' }}>
        Acompanhamento & Tecnologias
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/conversa')}
        >
          <MessageSquare size={26} color="var(--color-rosa)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Conversa com a IA</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/agenda')}
        >
          <Calendar size={26} color="var(--color-vinho)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Agenda & Alarmes</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/prenatal-card')}
        >
          <FileText size={26} color="var(--color-vinho)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Caderneta de Pré-Natal</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/exames')}
        >
          <Activity size={26} color="var(--color-rosa)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Laudos & Exames</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/dispositivos')}
        >
          <Bluetooth size={26} color="var(--color-vinho)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Pressão & Glicemia</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/diario-visual')}
        >
          <Camera size={26} color="var(--color-rosa)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Diário Visual Gestacional</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/vinculo-medico')}
        >
          <Link size={26} color="var(--color-vinho)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Vincular Médico</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center' }}
          onClick={() => onNavigate('/comunidade')}
        >
          <Users size={26} color="var(--color-rosa)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px' }}>Comunidade Segura</span>
        </button>
      </div>

      <TriageDisclaimer />
    </div>
  );
}
