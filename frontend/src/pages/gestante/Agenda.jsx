import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { Calendar, Clock, CheckCircle2, Circle, Trash2, Plus, Bell, Syringe, Pill, Activity, Flag } from 'lucide-react';

const TIPOS_EVENTO = [
  { tipo: 'consulta', label: 'Consulta Pré-Natal', icon: Calendar },
  { tipo: 'medicacao', label: 'Medicação / Suplemento', icon: Pill },
  { tipo: 'vacina', label: 'Vacina', icon: Syringe },
  { tipo: 'exame', label: 'Exame de Laboratório/USG', icon: Activity },
  { tipo: 'marco', label: 'Marco Gestacional', icon: Flag }
];

export default function Agenda({ onBack }) {
  const { authHeaders } = useAuth();
  const [eventos, setEventos] = useState([]);
  const [apenasFuturos, setApenasFuturos] = useState(true);
  const [mostrarModalCriar, setMostrarModalCriar] = useState(false);

  const [tipo, setTipo] = useState('consulta');
  const [titulo, setTitulo] = useState('');
  const [dataHora, setDataHora] = useState('');
  const [notas, setNotas] = useState('');
  const [recorrencia, setRecorrencia] = useState('');
  const [carregando, setCarregando] = useState(false);

  const carregarEventos = async () => {
    try {
      const res = await fetch(`/agenda/eventos?apenas_futuros=${apenasFuturos}`, {
        headers: authHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setEventos(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    carregarEventos();
  }, [apenasFuturos]);

  const handleConcluir = async (id) => {
    // Atualização otimista
    setEventos((prev) =>
      prev.map((ev) => (ev.id === id ? { ...ev, concluido: !ev.concluido } : ev))
    );

    try {
      await fetch(`/agenda/eventos/${id}/concluir`, {
        method: 'PATCH',
        headers: authHeaders()
      });
    } catch (err) {
      carregarEventos(); // Reverte se falhar
    }
  };

  const handleExcluir = async (id) => {
    setEventos((prev) => prev.filter((ev) => ev.id !== id));
    try {
      await fetch(`/agenda/eventos/${id}`, {
        method: 'DELETE',
        headers: authHeaders()
      });
    } catch (err) {
      carregarEventos();
    }
  };

  const handleCriarEvento = async (e) => {
    e.preventDefault();
    if (!titulo || !dataHora) return;

    setCarregando(true);
    try {
      const res = await fetch('/agenda/eventos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          tipo,
          titulo,
          data_hora: new Date(dataHora).toISOString(),
          notas,
          recorrencia: recorrencia || null
        })
      });

      if (res.ok) {
        setTitulo('');
        setDataHora('');
        setNotas('');
        setRecorrencia('');
        setMostrarModalCriar(false);
        carregarEventos();
      }
    } catch (err) {
    } finally {
      setCarregando(false);
    }
  };

  // Tocar alarme sonoro de teste
  const testarAlarme = () => {
    try {
      // Audio synthesis beep
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    } catch (e) {}
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2>Agenda & Alarmes</h2>
        <button
          className="btn btn-primary"
          onClick={() => setMostrarModalCriar(true)}
          style={{ minHeight: '40px', padding: '8px 14px', fontSize: '0.85rem' }}
        >
          <Plus size={16} /> Novo Evento
        </button>
      </div>

      {/* Barra de Filtro e Teste de Alarme */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
          <input
            type="checkbox"
            checked={apenasFuturos}
            onChange={(e) => setApenasFuturos(e.target.checked)}
            style={{ width: '16px', height: '16px', accentColor: 'var(--color-rosa)' }}
          />
          <span>Exibir apenas eventos futuros</span>
        </label>

        <button
          onClick={testarAlarme}
          className="btn btn-outline"
          style={{ minHeight: '36px', padding: '4px 10px', fontSize: '0.75rem', color: 'var(--color-vinho)' }}
          title="Verificar se o alarme sonoro está funcionando"
        >
          <Bell size={14} /> Testar Alarme
        </button>
      </div>

      {/* Modal de Criação de Evento */}
      {mostrarModalCriar && (
        <div className="card" style={{ border: '2px solid var(--color-rosa)', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '1.05rem', marginBottom: '12px' }}>Adicionar à Agenda</h3>
          <form onSubmit={handleCriarEvento}>
            <div className="form-group">
              <label>Tipo de Evento</label>
              <select className="form-control" value={tipo} onChange={(e) => setTipo(e.target.value)}>
                {TIPOS_EVENTO.map((t) => (
                  <option key={t.tipo} value={t.tipo}>{t.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Título do Evento</label>
              <input
                type="text"
                className="form-control"
                placeholder="Ex: Consulta Pré-Natal 24 semanas"
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Data e Horário</label>
              <input
                type="datetime-local"
                className="form-control"
                value={dataHora}
                onChange={(e) => setDataHora(e.target.value)}
                required
              />
            </div>

            {tipo === 'medicacao' && (
              <div className="form-group">
                <label>Recorrência (Opcional)</label>
                <select className="form-control" value={recorrencia} onChange={(e) => setRecorrencia(e.target.value)}>
                  <option value="">Apenas uma vez</option>
                  <option value="diaria">Diária</option>
                  <option value="8_8h">A cada 8 horas</option>
                  <option value="12_12h">A cada 12 horas</option>
                </select>
              </div>
            )}

            <div className="form-group">
              <label>Observações</label>
              <input
                type="text"
                className="form-control"
                placeholder="Ex: Levar resultados de exames de sangue"
                value={notas}
                onChange={(e) => setNotas(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button
                type="button"
                className="btn btn-outline"
                style={{ flex: 1 }}
                onClick={() => setMostrarModalCriar(false)}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ flex: 1 }}
                disabled={carregando}
              >
                {carregando ? 'Salvando...' : 'Salvar Evento'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Lista de Eventos */}
      {eventos.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
          <Calendar size={36} color="var(--color-text-muted)" style={{ margin: '0 auto 10px auto' }} />
          <p className="text-muted">
            {apenasFuturos
              ? "Nenhum compromisso futuro agendado. Desmarque o filtro acima para ver eventos passados ou adicione um novo."
              : "Nenhum evento registrado na agenda."}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {eventos.map((ev) => {
            const tipoMeta = TIPOS_EVENTO.find((t) => t.tipo === ev.tipo) || TIPOS_EVENTO[0];
            const Icon = tipoMeta.icon;
            const dataFmt = new Date(ev.data_hora).toLocaleString('pt-BR', {
              dateStyle: 'short',
              timeStyle: 'short'
            });

            return (
              <div
                key={ev.id}
                className="card"
                style={{
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  opacity: ev.concluido ? 0.6 : 1,
                  backgroundColor: ev.concluido ? '#F8F8F8' : 'var(--color-surface-card)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <button
                    onClick={() => handleConcluir(ev.id)}
                    style={{ background: 'transparent', border: 'none', padding: 0, cursor: 'pointer', color: ev.concluido ? '#27AE60' : 'var(--color-text-muted)' }}
                    aria-label={ev.concluido ? "Marcar como pendente" : "Concluir evento"}
                  >
                    {ev.concluido ? <CheckCircle2 size={24} /> : <Circle size={24} />}
                  </button>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Icon size={14} color="var(--color-vinho)" />
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-rosa)', textTransform: 'capitalize' }}>
                        {tipoMeta.label}
                      </span>
                    </div>
                    <h4 style={{ fontSize: '0.95rem', margin: '2px 0', textDecoration: ev.concluido ? 'line-through' : 'none' }}>
                      {ev.titulo}
                    </h4>
                    <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> {dataFmt} {ev.recorrencia ? `• Recorrência: ${ev.recorrencia}` : ''}
                    </p>
                    {ev.notas && (
                      <p style={{ fontSize: '0.78rem', color: 'var(--color-text-main)', marginTop: '2px' }}>
                        {ev.notas}
                      </p>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handleExcluir(ev.id)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', padding: '6px', cursor: 'pointer' }}
                  aria-label="Excluir evento"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
