import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { formatDateTime, formatTime } from '../../utils/dateUtils';
import {
  Heart, AlertTriangle, Calendar, Phone, ShieldCheck, CheckCircle2,
  Info, ArrowRight, Plus, CheckCircle, Trash2, Activity, Clock, Smile,
  ChevronDown, ChevronUp, UserCheck, Sparkles
} from 'lucide-react';

const SINTOMAS_RAPIDOS = [
  'Náusea / Enjoo',
  'Azia / Queimação',
  'Dor de cabeça',
  'Inchaço nas pernas',
  'Dor nas costas',
  'Cansaço excessivo',
  'Cólicas leves'
];

export default function PartnerDashboard({ onNavigateEmergency, onNavigateQuiz, onNavigateCheckin, onNavigateAgenda }) {
  const { user, authHeaders, login } = useAuth();
  const [emergenciaAtiva, setEmergenciaAtiva] = useState(null);
  const [marcos, setMarcos] = useState(null);
  const [agenda, setAgenda] = useState([]);
  const [gestanteConectada, setGestanteConectada] = useState(null);
  const [checkinsHoje, setCheckinsHoje] = useState([]);
  const [codigoConvite, setCodigoConvite] = useState('');
  const [conectado, setConectado] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState('');

  // Formulário Rápido de Check-in pelo Parceiro
  const [mostrarFormCheckin, setMostrarFormCheckin] = useState(false);
  const [humorCheckin, setHumorCheckin] = useState(4);
  const [descricaoCheckin, setDescricaoCheckin] = useState('');
  const [sintomasCheckin, setSintomasCheckin] = useState([]);
  const [movimentosBebeCheckin, setMovimentosBebeCheckin] = useState(6);
  const [salvandoCheckin, setSalvandoCheckin] = useState(false);
  const [resultadoCheckin, setResultadoCheckin] = useState(null);

  // Formulário Rápido de Adição de Evento na Agenda
  const [mostrarFormAgenda, setMostrarFormAgenda] = useState(false);
  const [tipoAgenda, setTipoAgenda] = useState('consulta');
  const [tituloAgenda, setTituloAgenda] = useState('');
  const [dataHoraAgenda, setDataHoraAgenda] = useState('');
  const [notasAgenda, setNotasAgenda] = useState('');
  const [salvandoAgenda, setSalvandoAgenda] = useState(false);

  const carregarDadosParceiro = async () => {
    try {
      // 1. Verifica dados da gestante conectada
      const resG = await fetch('/parceiro/gestante-conectada', { headers: authHeaders() });
      if (resG.ok) {
        const dG = await resG.json();
        if (dG.conectado) {
          setGestanteConectada(dG);
          setConectado(true);
        }
      }

      // 2. Verifica alertas de emergência em tempo real (Gratuito, todos os planos)
      const resEmerg = await fetch('/parceiro/emergencias-ativas', { headers: authHeaders() });
      if (resEmerg.ok) {
        const dEmerg = await resEmerg.json();
        setEmergenciaAtiva(dEmerg.alerta_ativo ? dEmerg : null);
      }

      // 3. Carrega marcos
      const resMarcos = await fetch('/parceiro/marcos', { headers: authHeaders() });
      if (resMarcos.ok) {
        const dMarcos = await resMarcos.json();
        setMarcos(dMarcos);
        setConectado(true);
      }

      // 4. Carrega agenda de apoio logístico (todos os eventos)
      const resAgenda = await fetch('/parceiro/agenda', { headers: authHeaders() });
      if (resAgenda.ok) {
        const dAgenda = await resAgenda.json();
        setAgenda(dAgenda);
      }

      // 5. Carrega histórico de check-ins recentes
      const resCheck = await fetch('/parceiro/checkin/historico?limite=3', { headers: authHeaders() });
      if (resCheck.ok) {
        const dCheck = await resCheck.json();
        setCheckinsHoje(dCheck);
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
    if (e) e.preventDefault();
    setErro('');
    setSucesso('');

    const codLimpo = (codigoConvite || 'PARC-MARIANA').trim().toUpperCase();
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
      await carregarDadosParceiro();
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  const handleSalvarCheckinRapido = async (e) => {
    e.preventDefault();
    setSalvandoCheckin(true);
    setErro('');
    try {
      const res = await fetch('/parceiro/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          humor: humorCheckin,
          descricao: descricaoCheckin,
          sintomas: sintomasCheckin,
          movimentos_bebe: movimentosBebeCheckin,
          semana_gestacional: gestanteConectada?.semana_atual || marcos?.semana_atual || 24
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao registrar check-in.');
      }

      setResultadoCheckin(data);
      setSucesso('Check-in diário registrado com sucesso no prontuário da gestante!');
      setDescricaoCheckin('');
      setSintomasCheckin([]);
      setMostrarFormCheckin(false);
      carregarDadosParceiro();
    } catch (err) {
      setErro(err.message);
    } finally {
      setSalvandoCheckin(false);
    }
  };

  const handleSalvarEventoAgenda = async (e) => {
    e.preventDefault();
    if (!tituloAgenda.trim() || !dataHoraAgenda) {
      setErro('Por favor, informe o título e a data/hora do compromisso.');
      return;
    }

    setSalvandoAgenda(true);
    setErro('');
    try {
      const res = await fetch('/parceiro/agenda/evento', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          tipo: tipoAgenda,
          titulo: tituloAgenda.trim(),
          data_hora: new Date(dataHoraAgenda).toISOString(),
          notas: notasAgenda.trim(),
          recorrencia: null
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao salvar evento na agenda.');
      }

      setSucesso(`Evento "${data.titulo}" adicionado com sucesso na agenda da parceira!`);
      setTituloAgenda('');
      setDataHoraAgenda('');
      setNotasAgenda('');
      setMostrarFormAgenda(false);
      carregarDadosParceiro();
    } catch (err) {
      setErro(err.message);
    } finally {
      setSalvandoAgenda(false);
    }
  };

  const handleToggleConcluirEvento = async (eventoId) => {
    try {
      const res = await fetch(`/parceiro/agenda/evento/${eventoId}/concluir`, {
        method: 'PATCH',
        headers: authHeaders()
      });
      if (res.ok) {
        carregarDadosParceiro();
      }
    } catch (err) {}
  };

  const handleExcluirEvento = async (eventoId) => {
    if (!window.confirm('Deseja realmente remover este compromisso da agenda?')) return;
    try {
      const res = await fetch(`/parceiro/agenda/evento/${eventoId}`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.ok || res.status === 204) {
        carregarDadosParceiro();
      }
    } catch (err) {}
  };

  const toggleSintomaRapido = (sintoma) => {
    if (sintomasCheckin.includes(sintoma)) {
      setSintomasCheckin(sintomasCheckin.filter((s) => s !== sintoma));
    } else {
      setSintomasCheckin([...sintomasCheckin, sintoma]);
    }
  };

  const alternarParaContaGestante = async () => {
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'gestante@nymphia.com.br', senha: 'senhaMaternidade123' })
      });
      const data = await res.json();
      if (data.token) {
        login(data.token, data);
        window.location.href = '/';
      }
    } catch (e) {}
  };

  return (
    <div style={{ paddingBottom: '70px' }}>
      {/* Cabeçalho do Parceiro */}
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: '0.8rem', color: '#1E7E34', fontWeight: 700, textTransform: 'uppercase' }}>
            🤝 Rede de Apoio & Parceiro
          </span>
          <h2 style={{ margin: '2px 0 0 0' }}>Olá, {user?.nome || 'Lucas'}</h2>
          <p className="text-muted" style={{ fontSize: '0.85rem', margin: '2px 0 0 0' }}>
            Apoio logístico, check-ins de bem-estar e canal de emergência
          </p>
        </div>

        <button
          onClick={alternarParaContaGestante}
          className="btn"
          style={{
            backgroundColor: '#FFF0F3',
            border: '1px solid var(--color-rosa)',
            color: 'var(--color-vinho)',
            fontSize: '0.75rem',
            padding: '6px 10px',
            borderRadius: 'var(--radius-sm)'
          }}
          title="Alternar para ver o aplicativo com a visão da Gestante (Mariana)"
        >
          🌸 Ver como Gestante
        </button>
      </div>

      {sucesso && (
        <div role="status" style={{ padding: '12px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-sm)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem' }}>
          <CheckCircle2 size={18} /> {sucesso}
        </div>
      )}

      {erro && (
        <div role="alert" style={{ padding: '12px', backgroundColor: '#FDEEE9', color: '#8A2B1A', borderRadius: 'var(--radius-sm)', marginBottom: '16px', fontSize: '0.88rem' }}>
          {erro}
        </div>
      )}

      {/* CARD DE VÍNCULO COM A GESTANTE */}
      <div
        className="card"
        style={{
          backgroundColor: conectado ? '#F4FBF7' : '#FFF9F5',
          border: conectado ? '1.5px solid #27AE60' : '1.5px solid #E67E22',
          padding: '16px',
          marginBottom: '18px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: conectado ? '#E8F8F0' : '#FDEBD0',
                color: conectado ? '#1E7E34' : '#D35400',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <UserCheck size={22} />
            </div>
            <div>
              <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', fontWeight: 700, color: conectado ? '#1E7E34' : '#D35400' }}>
                {conectado ? 'Parceira Conectada' : 'Vínculo Pendente'}
              </span>
              <h3 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-vinho)' }}>
                {gestanteConectada?.gestante_nome || 'Mariana Costa'}
              </h3>
            </div>
          </div>

          {conectado ? (
            <span className="badge-gold" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>
              Semana {gestanteConectada?.semana_atual || marcos?.semana_atual || 24}
            </span>
          ) : (
            <button
              onClick={() => handleConectarGestante(null)}
              className="btn btn-primary"
              style={{ fontSize: '0.78rem', padding: '6px 12px' }}
            >
              Conectar Demo
            </button>
          )}
        </div>

        {!conectado && (
          <form onSubmit={handleConectarGestante} style={{ marginTop: '12px' }}>
            <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
              Digite o código de parceiro gerado no perfil da gestante:
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                className="form-control"
                placeholder="Ex: PARC-XXXXX"
                value={codigoConvite}
                onChange={(e) => setCodigoConvite(e.target.value.toUpperCase())}
                style={{ flex: 1 }}
              />
              <button type="submit" className="btn btn-primary" disabled={carregando}>
                {carregando ? 'Ativando...' : 'Ativar'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* ALERTA DE EMERGÊNCIA EM TEMPO REAL */}
      {emergenciaAtiva ? (
        <div
          role="alert"
          style={{
            backgroundColor: '#FDEDEC',
            border: '2px solid var(--color-vermelho)',
            borderRadius: 'var(--radius-lg)',
            padding: '18px',
            marginBottom: '20px',
            boxShadow: 'var(--shadow-emergency)',
            animation: 'pulse 2s infinite'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-vermelho)', marginBottom: '8px' }}>
            <AlertTriangle size={28} />
            <h3 style={{ fontSize: '1.2rem', margin: 0, color: 'var(--color-vermelho)' }}>
              ALERTA DE EMERGÊNCIA ATIVO!
            </h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-main)', marginBottom: '12px' }}>
            {gestanteConectada?.gestante_nome || 'A gestante'} acionou o canal de emergência às {formatTime(emergenciaAtiva.data_hora)}.
          </p>

          <div style={{ backgroundColor: '#FFFFFF', padding: '12px', borderRadius: 'var(--radius-md)', marginBottom: '14px', border: '1px solid var(--color-border)', fontSize: '0.85rem' }}>
            <strong>Maternidade Destino:</strong> {emergenciaAtiva.maternidade || 'Maternidade de Referência'}
            <br />
            <strong>Telefone:</strong> {emergenciaAtiva.telefone_maternidade || '192'}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <a
              href="tel:192"
              className="btn"
              style={{ flex: 1, backgroundColor: 'var(--color-vermelho)', color: '#FFFFFF', textDecoration: 'none', justifyContent: 'center' }}
            >
              <Phone size={18} /> Ligar 192 (SAMU)
            </a>
            <button
              onClick={onNavigateEmergency}
              className="btn btn-outline"
              style={{ flex: 1, borderColor: 'var(--color-vermelho)', color: 'var(--color-vermelho)' }}
            >
              Ver Detalhes
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
            padding: '12px 14px',
            marginBottom: '18px'
          }}
        >
          <ShieldCheck size={24} color="#27AE60" />
          <div>
            <h4 style={{ margin: 0, color: '#1E7E34', fontSize: '0.92rem' }}>
              Alerta de Emergência SAMU Conectado
            </h4>
            <span style={{ fontSize: '0.78rem', color: '#27AE60' }}>
              Monitorando em tempo real. Nenhum chamado de socorro em aberto.
            </span>
          </div>
        </div>
      )}

      {/* ====================================================================== */}
      {/* 1. CHECK-IN DIÁRIO PELA GESTANTE (FEITO PELO PARCEIRO) */}
      {/* ====================================================================== */}
      <div
        className="card"
        style={{
          borderLeft: '5px solid var(--color-rosa)',
          backgroundColor: '#FFFDFD',
          marginBottom: '18px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-rosa-claro)',
                color: 'var(--color-rosa)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Activity size={22} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--color-vinho)' }}>
                Check-in Diário de Bem-Estar
              </h3>
              <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                Registre o estado diário de {gestanteConectada?.gestante_nome?.split(' ')[0] || 'Mariana'}
              </span>
            </div>
          </div>

          <button
            onClick={() => setMostrarFormCheckin(!mostrarFormCheckin)}
            className="btn btn-outline"
            style={{ fontSize: '0.8rem', padding: '6px 12px', borderColor: 'var(--color-rosa)', color: 'var(--color-vinho)' }}
          >
            {mostrarFormCheckin ? 'Fechar' : '🌸 Registrar Check-in'}
          </button>
        </div>

        {/* Resumo do último check-in se já existir hoje */}
        {checkinsHoje && checkinsHoje.length > 0 && !mostrarFormCheckin && (
          <div style={{ marginTop: '10px', padding: '10px 12px', backgroundColor: '#FDF7F8', borderRadius: 'var(--radius-sm)', border: '1px solid #F5D3D9' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--color-vinho)' }}>
                Último Registro: {formatDateTime(checkinsHoje[0].data_hora)}
              </span>
              <span style={{ fontSize: '0.78rem', color: 'var(--color-rosa)', fontWeight: 600 }}>
                Semana {checkinsHoje[0].semana_gestacional}
              </span>
            </div>
            <p style={{ margin: '4px 0', fontSize: '0.85rem', color: 'var(--color-text-main)' }}>
              {checkinsHoje[0].descricao || 'Sem anotações adicionais.'}
            </p>
            {checkinsHoje[0].recomendacao && (
              <div style={{ fontSize: '0.8rem', color: '#1E7E34', marginTop: '6px', fontWeight: 600 }}>
                💡 {checkinsHoje[0].recomendacao}
              </div>
            )}
          </div>
        )}

        {/* Formulário Interativo de Check-in pelo Parceiro */}
        {mostrarFormCheckin && (
          <form onSubmit={handleSalvarCheckinRapido} style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--color-border)' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
              Como ela está se sentindo hoje?
            </label>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '6px', marginBottom: '14px' }}>
              {[
                { n: 1, label: 'Muito Mal', emoji: '😫' },
                { n: 2, label: 'Indisposta', emoji: '🙁' },
                { n: 3, label: 'Regular', emoji: '😐' },
                { n: 4, label: 'Bem', emoji: '🙂' },
                { n: 5, label: 'Excelente', emoji: '🥰' }
              ].map((h) => (
                <button
                  type="button"
                  key={h.n}
                  onClick={() => setHumorCheckin(h.n)}
                  style={{
                    flex: 1,
                    padding: '8px 4px',
                    borderRadius: 'var(--radius-sm)',
                    border: humorCheckin === h.n ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                    backgroundColor: humorCheckin === h.n ? 'var(--color-rosa-claro)' : '#FFFFFF',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '2px'
                  }}
                >
                  <span style={{ fontSize: '1.4rem' }}>{h.emoji}</span>
                  <span style={{ fontSize: '0.68rem', color: 'var(--color-vinho)', fontWeight: 600 }}>{h.label}</span>
                </button>
              ))}
            </div>

            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
              Sintomas observados ou relatados por ela:
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
              {SINTOMAS_RAPIDOS.map((s) => {
                const ativo = sintomasCheckin.includes(s);
                return (
                  <button
                    type="button"
                    key={s}
                    onClick={() => toggleSintomaRapido(s)}
                    style={{
                      padding: '5px 10px',
                      borderRadius: 'var(--radius-full)',
                      border: ativo ? '1.5px solid var(--color-rosa)' : '1px solid var(--color-border)',
                      backgroundColor: ativo ? 'var(--color-rosa-claro)' : '#FFFFFF',
                      color: ativo ? 'var(--color-vinho)' : 'var(--color-text-muted)',
                      fontSize: '0.78rem',
                      fontWeight: ativo ? 600 : 400,
                      cursor: 'pointer'
                    }}
                  >
                    {s}
                  </button>
                );
              })}
            </div>

            <div className="form-group" style={{ marginBottom: '12px' }}>
              <label htmlFor="parc-checkin-desc" style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                Observações do Parceiro
              </label>
              <textarea
                id="parc-checkin-desc"
                className="form-control"
                rows={2}
                placeholder="Ex: Ela descansou à tarde, mas sentiu um leve enjoo após o almoço..."
                value={descricaoCheckin}
                onChange={(e) => setDescricaoCheckin(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ flex: 1, minHeight: '44px' }}
                disabled={salvandoCheckin}
              >
                {salvandoCheckin ? 'Registrando...' : 'Salvar Check-in por Ela'}
              </button>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setMostrarFormCheckin(false)}
                style={{ minHeight: '44px' }}
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </div>

      {/* ====================================================================== */}
      {/* 2. AGENDA COMPARTILHADA DA GESTANTE (GERENCIÁVEL PELO PARCEIRO) */}
      {/* ====================================================================== */}
      <div className="card" style={{ marginBottom: '18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={20} color="var(--color-rosa)" />
            <h3 style={{ fontSize: '1.05rem', margin: 0 }}>
              Agenda da Gestante (Apoio Logístico)
            </h3>
          </div>

          <button
            onClick={() => setMostrarFormAgenda(!mostrarFormAgenda)}
            className="btn btn-primary"
            style={{ fontSize: '0.78rem', padding: '6px 10px' }}
          >
            <Plus size={16} /> Novo Compromisso
          </button>
        </div>

        {/* Formulário de Novo Evento */}
        {mostrarFormAgenda && (
          <form
            onSubmit={handleSalvarEventoAgenda}
            style={{
              backgroundColor: '#F8F9FA',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              marginBottom: '14px'
            }}
          >
            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.95rem', color: 'var(--color-vinho)' }}>
              Adicionar Compromisso para a Gestante
            </h4>

            <div className="form-group" style={{ marginBottom: '8px' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Tipo de Compromisso</label>
              <select
                className="form-control"
                value={tipoAgenda}
                onChange={(e) => setTipoAgenda(e.target.value)}
                style={{ fontSize: '0.85rem' }}
              >
                <option value="consulta">Consulta de Pré-Natal</option>
                <option value="exame">Exame / Ultrassom</option>
                <option value="vacina">Vacina</option>
                <option value="medicacao">Medicação / Suplemento</option>
                <option value="alarme">Lembrete / Alarme</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: '8px' }}>
              <label htmlFor="agenda-titulo" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Título do Compromisso</label>
              <input
                id="agenda-titulo"
                type="text"
                className="form-control"
                placeholder="Ex: Ultrassom Morfológico 2º Trimestre"
                value={tituloAgenda}
                onChange={(e) => setTituloAgenda(e.target.value)}
                required
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '8px' }}>
              <label htmlFor="agenda-datahora" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Data e Horário</label>
              <input
                id="agenda-datahora"
                type="datetime-local"
                className="form-control"
                value={dataHoraAgenda}
                onChange={(e) => setDataHoraAgenda(e.target.value)}
                required
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '12px' }}>
              <label htmlFor="agenda-notas" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Notas de Apoio (opcional)</label>
              <input
                id="agenda-notas"
                type="text"
                className="form-control"
                placeholder="Ex: Levar carteirinha e exames anteriores de sangue"
                value={notasAgenda}
                onChange={(e) => setNotasAgenda(e.target.value)}
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ flex: 1 }}
                disabled={salvandoAgenda}
              >
                {salvandoAgenda ? 'Salvando...' : 'Salvar na Agenda dela'}
              </button>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setMostrarFormAgenda(false)}
              >
                Cancelar
              </button>
            </div>
          </form>
        )}

        {/* Lista de Eventos Gerenciáveis */}
        {agenda.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '16px', color: 'var(--color-text-muted)' }}>
            <Calendar size={28} style={{ opacity: 0.4, margin: '0 auto 6px auto' }} />
            <p style={{ margin: 0, fontSize: '0.85rem' }}>Nenhum compromisso cadastrado na agenda da gestante.</p>
            <button
              onClick={() => setMostrarFormAgenda(true)}
              className="btn btn-outline"
              style={{ marginTop: '8px', fontSize: '0.8rem' }}
            >
              + Adicionar Primeiro Compromisso
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {agenda.map((ev) => (
              <div
                key={ev.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  backgroundColor: ev.concluido ? '#F9FBF9' : '#FFFFFF',
                  borderRadius: 'var(--radius-sm)',
                  border: ev.concluido ? '1px solid #D5E8D4' : '1px solid var(--color-border)',
                  opacity: ev.concluido ? 0.75 : 1
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={() => handleToggleConcluirEvento(ev.id)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      padding: 0,
                      color: ev.concluido ? '#27AE60' : 'var(--color-text-muted)',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title={ev.concluido ? 'Marcar como pendente' : 'Marcar como concluído'}
                  >
                    {ev.concluido ? <CheckCircle size={22} color="#27AE60" /> : <Clock size={22} />}
                  </button>

                  <div>
                    <strong
                      style={{
                        color: ev.concluido ? 'var(--color-text-muted)' : 'var(--color-vinho)',
                        fontSize: '0.9rem',
                        textDecoration: ev.concluido ? 'line-through' : 'none',
                        display: 'block'
                      }}
                    >
                      {ev.titulo}
                    </strong>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.78rem' }}>
                      {formatDateTime(ev.data_hora)}
                    </span>
                    {ev.notas && (
                      <span style={{ display: 'block', fontSize: '0.74rem', color: '#666', fontStyle: 'italic', marginTop: '2px' }}>
                        {ev.notas}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handleExcluirEvento(ev.id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#C0392B',
                    cursor: 'pointer',
                    padding: '6px'
                  }}
                  title="Excluir compromisso"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}

            <button
              onClick={onNavigateAgenda}
              className="btn btn-outline"
              style={{ marginTop: '8px', width: '100%', fontSize: '0.82rem' }}
            >
              📅 Abrir Calendário Completo
            </button>
          </div>
        )}
      </div>

      {/* Marcos da Semana e Guia de Apoio */}
      {marcos && (
        <div className="card card-vinho" style={{ marginBottom: '18px' }}>
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

      {/* Quiz de Gostos & Mimos da Gestante */}
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          backgroundColor: '#FFF9FA',
          border: '1.5px solid var(--color-rosa)',
          marginBottom: '18px'
        }}
        onClick={onNavigateQuiz}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-rosa-claro)',
              color: 'var(--color-rosa)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Heart size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <h3 style={{ fontSize: '0.98rem', margin: 0, color: 'var(--color-vinho)' }}>
                Quiz dos Gostos da Gestante
              </h3>
              <span className="badge-gold" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>Mimos</span>
            </div>
            <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0 0' }}>
              Descubra os mimos, aromas e desejos favoritos dela para surpreendê-la!
            </p>
          </div>
        </div>
        <ArrowRight size={18} color="var(--color-vinho)" />
      </div>

      {/* Aviso de Privacidade e Governança LGPD */}
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
            <strong>Transparência & LGPD:</strong> Você tem autorização para auxiliar na logística, registrar o check-in diário e organizar consultas e exames da gestante. Suas ações são registradas com transparência para a equipe clínica.
          </div>
        </div>
      </div>
    </div>
  );
}
