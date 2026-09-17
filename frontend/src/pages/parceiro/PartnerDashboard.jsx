import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Heart, AlertTriangle, Calendar, Phone, ShieldCheck, CheckCircle2, Info, ArrowRight } from 'lucide-react';

export default function PartnerDashboard({ onNavigateEmergency }) {
  const { user, authHeaders } = useAuth();
  const [emergenciaAtiva, setEmergenciaAtiva] = useState(null);
  const [marcos, setMarcos] = useState(null);
  const [agenda, setAgenda] = useState([]);
  const [codigoConvite, setCodigoConvite] = useState('');
  const [conectado, setConectado] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState('');

  const carregarDadosParceiro = async () => {
    try {
      // 1. Verifica alertas de emergência em tempo real (Gratuito, todos os planos)
      const resEmerg = await fetch('/parceiro/emergencias-ativas', { headers: authHeaders() });
      if (resEmerg.ok) {
        const dEmerg = await resEmerg.json();
        setEmergenciaAtiva(dEmerg.alerta_ativo ? dEmerg : null);
      }

      // 2. Carrega marcos (Premium+)
      const resMarcos = await fetch('/parceiro/marcos', { headers: authHeaders() });
      if (resMarcos.ok) {
        const dMarcos = await resMarcos.json();
        setMarcos(dMarcos);
        setConectado(true);
      }

      // 3. Carrega agenda de apoio logístico (Premium+)
      const resAgenda = await fetch('/parceiro/agenda', { headers: authHeaders() });
      if (resAgenda.ok) {
        const dAgenda = await resAgenda.json();
        setAgenda(dAgenda);
      }
    } catch (err) {}
  };

  useEffect(() => {
    carregarDadosParceiro();
    // Poll de emergência a cada 8 segundos para o parceiro
    const interval = setInterval(carregarDadosParceiro, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleConectarGestante = async (e) => {
    e.preventDefault();
    setErro('');
    setSucesso('');

    const codLimpo = codigoConvite.trim().toUpperCase();
    if (!codLimpo) return;

    setCarregando(true);
    try {
      const res = await fetch('/parceiro/convite/usar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ codigo: codLimpo })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Código de parceiro inválido.');
      }
      setSucesso('Conectado à sua parceira com sucesso!');
      setCodigoConvite('');
      carregarDadosParceiro();
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--color-rosa)', fontWeight: 700, textTransform: 'uppercase' }}>
          Modo Parceiro
        </span>
        <h2 style={{ margin: 0 }}>Olá, {user?.nome}</h2>
        <p className="text-muted" style={{ fontSize: '0.85rem' }}>
          Apoio logístico e canal de emergência em tempo real
        </p>
      </div>

      {sucesso && (
        <div role="status" style={{ padding: '12px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-sm)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} /> {sucesso}
        </div>
      )}

      {erro && (
        <div role="alert" style={{ padding: '12px', backgroundColor: '#FDEEE9', color: '#8A2B1A', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
          {erro}
        </div>
      )}

      {/* ALERTA DE EMERGÊNCIA EM TEMPO REAL (GRATUITO PARA TODOS OS PLANOS) */}
      {emergenciaAtiva ? (
        <div
          role="alert"
          style={{
            backgroundColor: '#FDEDEC',
            border: '2px solid var(--color-vermelho)',
            borderRadius: 'var(--radius-lg)',
            padding: '20px',
            marginBottom: '24px',
            boxShadow: 'var(--shadow-emergency)',
            animation: 'pulse 2s infinite'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-vermelho)', marginBottom: '8px' }}>
            <AlertTriangle size={28} />
            <h3 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--color-vermelho)' }}>
              ALERTA DE EMERGÊNCIA ATIVO!
            </h3>
          </div>
          <p style={{ fontSize: '0.92rem', color: 'var(--color-text-main)', marginBottom: '12px' }}>
            A gestante acionou o canal de emergência às {new Date(emergenciaAtiva.data_hora).toLocaleTimeString('pt-BR')}.
          </p>

          <div style={{ backgroundColor: '#FFFFFF', padding: '12px', borderRadius: 'var(--radius-md)', marginBottom: '14px', border: '1px solid var(--color-border)' }}>
            <strong>Maternidade Destino:</strong> {emergenciaAtiva.maternidade || 'Maternidade de Referência'}
            <br />
            <strong>Telefone:</strong> {emergenciaAtiva.telefone_maternidade || '192'}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <a
              href="tel:192"
              className="btn"
              style={{ flex: 1, backgroundColor: 'var(--color-vermelho)', color: '#FFFFFF', textDecoration: 'none' }}
            >
              <Phone size={18} /> Ligar 192 (SAMU)
            </a>
            <button
              onClick={onNavigateEmergency}
              className="btn btn-outline"
              style={{ flex: 1, borderColor: 'var(--color-vermelho)', color: 'var(--color-vermelho)' }}
            >
              Abrir Rota / Detalhes
            </button>
          </div>
        </div>
      ) : (
        <div
          className="card"
          style={{
            backgroundColor: '#EAF7EF',
            border: '1px solid #27AE60',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '14px'
          }}
        >
          <ShieldCheck size={26} color="#27AE60" />
          <div>
            <h4 style={{ margin: 0, color: '#1E7E34', fontSize: '0.95rem' }}>
              Alerta de Emergência Conectado (Gratuito)
            </h4>
            <span style={{ fontSize: '0.8rem', color: '#27AE60' }}>
              Nenhum chamado de socorro em aberto no momento.
            </span>
          </div>
        </div>
      )}

      {/* Se não conectado, exibir formulário de código */}
      {!conectado && (
        <form onSubmit={handleConectarGestante} className="card">
          <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Conectar à Gestante</h3>
          <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '14px' }}>
            Peça à gestante para gerar o código de parceiro no perfil dela e digite abaixo:
          </p>

          <div className="form-group">
            <input
              type="text"
              className="form-control"
              placeholder="Ex: PARC-XXXXX"
              value={codigoConvite}
              onChange={(e) => setCodigoConvite(e.target.value.toUpperCase())}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%' }}
            disabled={carregando}
          >
            {carregando ? 'Conectando...' : 'Ativar Vínculo de Parceiro'}
            <ArrowRight size={18} />
          </button>
        </form>
      )}

      {/* Marcos da Semana e Guia de Apoio (Premium+) */}
      {marcos && (
        <div className="card card-vinho">
          <span className="badge-gold" style={{ marginBottom: '8px' }}>
            Semana {marcos.semana_atual}
          </span>
          <h3 style={{ color: '#FFFFFF', fontSize: '1.15rem', margin: '4px 0 8px 0' }}>
            Desenvolvimento do Bebê
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--color-rosa-claro)', marginBottom: '16px' }}>
            {marcos.desenvolvimento_bebe}
          </p>

          <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.15)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
            <strong style={{ display: 'block', fontSize: '0.85rem', color: '#FFFFFF', marginBottom: '4px' }}>
              Como apoiar nesta fase:
            </strong>
            <p style={{ fontSize: '0.82rem', color: 'var(--color-rosa-claro)', margin: 0 }}>
              {marcos.dica_como_apoiar}
            </p>
          </div>
        </div>
      )}

      {/* Agenda Compartilhada de Consultas e Vacinas (Premium+) */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Calendar size={18} color="var(--color-rosa)" />
          <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Agenda Compartilhada (Apoio Logístico)</h3>
        </div>

        {agenda.length === 0 ? (
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>Nenhum compromisso futuro agendado.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {agenda.map((ev) => (
              <div
                key={ev.id}
                style={{
                  padding: '10px 12px',
                  backgroundColor: '#FFFFFF',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.85rem'
                }}
              >
                <strong style={{ color: 'var(--color-vinho)', display: 'block' }}>{ev.titulo}</strong>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '0.78rem' }}>
                  {new Date(ev.data_hora).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Aviso de Privacidade Rigorosa (Regra Seção 7.3 e 13.7) */}
      <div
        style={{
          backgroundColor: '#F8F9FA',
          padding: '12px 14px',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.78rem',
          color: 'var(--color-text-muted)',
          lineHeight: 1.4,
          border: '1px solid var(--color-border)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
          <Info size={16} style={{ flexShrink: 0, marginTop: '1px' }} />
          <div>
            <strong>Privacidade Clínica Blindada (LGPD):</strong> O modo parceiro foi desenvolvido para apoio logístico e emergências. Por sigilo médico e decisão de design, o parceiro <strong>nunca</strong> tem acesso a check-ins individuais, conversas com a IA, riscos clínicos calculados ou laudos de exames.
          </div>
        </div>
      </div>
    </div>
  );
}
