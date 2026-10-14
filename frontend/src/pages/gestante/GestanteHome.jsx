import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  Calendar, MessageSquare, Users, CheckCircle, Activity, Heart,
  Shield, FileText, Camera, Bluetooth, ChevronRight, AlertCircle,
  Link, Eye, Scale, Stethoscope, Copy, Check, Share2, X
} from 'lucide-react';
import TriageDisclaimer from '../../components/TriageDisclaimer';

export default function GestanteHome({ onNavigate }) {
  const { user, authHeaders } = useAuth();
  const [perfil, setPerfil] = useState(null);
  const [checkinHoje, setCheckinHoje] = useState(false);
  const [proximoEvento, setProximoEvento] = useState(null);
  const [semana, setSemana] = useState(24);
  const [diasSemana, setDiasSemana] = useState(3);

  // Vínculos com Médico Obstetra e Parceiro Real
  const [medicosConectados, setMedicosConectados] = useState([]);
  const [vinculoParceiro, setVinculoParceiro] = useState(null);
  const [modalCodigoParceiro, setModalCodigoParceiro] = useState(false);
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    // 1. Carrega perfil clínico
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

    // 2. Verifica se check-in de hoje foi realizado
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

    // 4. Médicos obstetras vinculados
    fetch('/vinculo/meus-profissionais', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setMedicosConectados(Array.isArray(data) ? data : []);
      })
      .catch(() => {});

    // 5. Parceiro vinculado e código de convite
    fetch('/parceiro/meu-vinculo', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setVinculoParceiro(data);
      })
      .catch(() => {});
  }, []);

  const copiarCodigo = () => {
    const cod = vinculoParceiro?.codigo || 'PARC-CONECTAR';
    navigator.clipboard.writeText(cod);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2500);
  };

  const medicoPrincipal = medicosConectados.length > 0 ? medicosConectados[0] : null;

  return (
    <div>
      {/* Saudação e Semana Gestacional */}
      <div className="card card-vinho" style={{ position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'relative', zIndex: 2 }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--color-rosa-claro)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Olá, {user?.nome?.split(' ')[0] || 'Gestante'}
          </span>
          <h2 style={{ fontSize: '1.6rem', marginTop: '4px', marginBottom: '8px' }}>
            {semana}ª Semana + {diasSemana} dias
          </h2>
          <p style={{ fontSize: '0.88rem', opacity: 0.9 }}>
            O bebê já responde a estímulos sonoros e os pulmões produzem surfactante.
          </p>

          <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
            <span className="badge-gold">
              DPP: {perfil?.dpp ? new Date(perfil.dpp + 'T12:00:00').toLocaleDateString('pt-BR') : 'A calcular'}
            </span>
            {medicoPrincipal && (
              <span style={{ fontSize: '0.74rem', padding: '3px 8px', backgroundColor: 'rgba(255,255,255,0.22)', color: '#FFFFFF', borderRadius: '4px', fontWeight: 600 }}>
                🩺 Dr(a). {medicoPrincipal.profissional_nome}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* CARD 1: VÍNCULO COM O MÉDICO OBSTETRA (Destaque Principal) */}
      {medicoPrincipal ? (
        <div
          className="card"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            backgroundColor: '#F7F4F9',
            border: '1.5px solid var(--color-vinho)',
            marginBottom: '14px',
            padding: '14px'
          }}
          onClick={() => onNavigate('/vinculo-medico')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-vinho)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 10px rgba(92, 26, 42, 0.2)'
              }}
            >
              <Stethoscope size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <h3 style={{ fontSize: '0.98rem', margin: 0, color: 'var(--color-vinho)' }}>
                  Dr(a). {medicoPrincipal.profissional_nome}
                </h3>
                <span className="badge-gold" style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
                  Obstetra Conectado
                </span>
              </div>
              <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0 0' }}>
                {medicoPrincipal.profissional_crm ? `${medicoPrincipal.profissional_crm}/${medicoPrincipal.profissional_uf || 'SP'}` : 'CRM Ativo'} • Pré-natal compartilhado
              </p>
            </div>
          </div>
          <ChevronRight size={20} color="var(--color-vinho)" />
        </div>
      ) : (
        <div
          className="card"
          style={{
            backgroundColor: '#FFF9FB',
            border: '1.5px dashed var(--color-rosa)',
            marginBottom: '14px',
            padding: '14px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--color-rosa-claro)',
                  color: 'var(--color-vinho)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Stethoscope size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0, color: 'var(--color-vinho)' }}>
                  Conectar com seu Médico Obstetra
                </h3>
                <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0 0' }}>
                  Compartilhe seus exames, curvas de peso e receba condutas no pré-natal.
                </p>
              </div>
            </div>

            <button
              onClick={() => onNavigate('/vinculo-medico')}
              className="btn btn-primary"
              style={{ fontSize: '0.8rem', padding: '8px 14px', whiteSpace: 'nowrap' }}
            >
              Vincular Obstetra
            </button>
          </div>
        </div>
      )}

      {/* CARD 2: MODO PARCEIRO (Rede de Apoio Real) */}
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: vinculoParceiro?.conectado ? '#F4FBF7' : '#FCFBF8',
          border: vinculoParceiro?.conectado ? '1.5px solid #27AE60' : '1.5px solid #E5D5C5',
          marginBottom: '14px',
          padding: '14px',
          flexWrap: 'wrap',
          gap: '10px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              backgroundColor: vinculoParceiro?.conectado ? '#E8F8F0' : '#F7EFE7',
              color: vinculoParceiro?.conectado ? '#1E7E34' : '#8A5D3B',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Users size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <h3 style={{ fontSize: '0.98rem', margin: 0, color: vinculoParceiro?.conectado ? '#1E7E34' : 'var(--color-vinho)' }}>
                {vinculoParceiro?.conectado ? 'Modo Parceiro Conectado' : 'Conectar seu Parceiro(a)'}
              </h3>
              {vinculoParceiro?.conectado && (
                <span style={{ fontSize: '0.68rem', padding: '2px 6px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: '4px', fontWeight: 700 }}>
                  {vinculoParceiro?.parceiro?.nome || 'Conectado'}
                </span>
              )}
            </div>
            <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0 0' }}>
              {vinculoParceiro?.conectado
                ? 'Ele(a) pode fazer check-ins por você e acompanhar suas consultas.'
                : 'Compartilhe seu código exclusivo para acompanharem a gestação juntos.'}
            </p>
          </div>
        </div>

        <button
          onClick={() => setModalCodigoParceiro(true)}
          className="btn"
          style={{
            backgroundColor: vinculoParceiro?.conectado ? '#E8F8F0' : 'var(--color-vinho)',
            color: vinculoParceiro?.conectado ? '#1E7E34' : '#FFFFFF',
            fontSize: '0.78rem',
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 600,
            whiteSpace: 'nowrap'
          }}
        >
          {vinculoParceiro?.conectado ? 'Ver Código' : '🔑 Gerar / Ver Código'}
        </button>
      </div>

      {/* Cartão de Status do Check-in Diário */}
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          borderLeft: checkinHoje ? '5px solid #27AE60' : '5px solid var(--color-rosa)',
          marginBottom: '14px'
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
            <p className="text-muted" style={{ fontSize: '0.82rem', margin: '2px 0 0 0' }}>
              {checkinHoje ? 'IA analisou seu humor e sintomas com sucesso' : 'Como você e seu bebê estão se sentindo hoje?'}
            </p>
          </div>
        </div>
        <ChevronRight size={20} color="var(--color-text-muted)" />
      </div>

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
          marginBottom: '14px'
        }}
        onClick={() => onNavigate('/quiz-gostos')}
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
                Quiz de Gostos & Mimos
              </h3>
              <span className="badge-gold" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>Opcional</span>
            </div>
            <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0 0' }}>
              Seus desejos, aromas e preferências (seu parceiro pode responder por você!)
            </p>
          </div>
        </div>
        <ChevronRight size={20} color="var(--color-text-muted)" />
      </div>

      {/* Próximo Evento da Agenda */}
      {proximoEvento && (
        <div
          className="card"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', marginBottom: '14px' }}
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
              <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0 0' }}>
                {new Date(proximoEvento.data_hora).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}
              </p>
            </div>
          </div>
          <ChevronRight size={20} color="var(--color-text-muted)" />
        </div>
      )}

      {/* Ações e Módulos Rápidos (Organizados de forma limpa e harmônica) */}
      <h3 style={{ marginTop: '20px', marginBottom: '12px', fontSize: '1.05rem', color: 'var(--color-vinho)' }}>
        Acompanhamento & Tecnologias
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center', border: '1.5px solid #F39C12', backgroundColor: '#FFFAF5' }}
          onClick={() => onNavigate('/antropometria')}
        >
          <Scale size={26} color="#D35400" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px', fontWeight: 600, color: '#873600' }}>Antropometria & Peso</span>
        </button>

        <button
          className="btn btn-outline"
          style={{ flexDirection: 'column', height: '96px', padding: '12px', textAlign: 'center', border: '1.5px solid var(--color-rosa)', backgroundColor: '#FFFDFD' }}
          onClick={() => onNavigate('/visao-corporal')}
        >
          <Eye size={26} color="var(--color-rosa)" />
          <span style={{ fontSize: '0.85rem', marginTop: '6px', fontWeight: 600, color: 'var(--color-vinho)' }}>Visão Corporal IA</span>
        </button>

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

      {/* MODAL DE CÓDIGO DO PARCEIRO */}
      {modalCodigoParceiro && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '16px'
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: '420px',
              width: '100%',
              backgroundColor: '#FFFFFF',
              boxShadow: 'var(--shadow-lg)',
              borderRadius: 'var(--radius-lg)',
              position: 'relative'
            }}
          >
            <button
              onClick={() => setModalCodigoParceiro(false)}
              style={{
                position: 'absolute',
                top: '14px',
                right: '14px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--color-text-muted)'
              }}
            >
              <X size={20} />
            </button>

            <div style={{ textAlign: 'center', marginBottom: '16px' }}>
              <div
                style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '50%',
                  backgroundColor: '#E8F8F0',
                  color: '#1E7E34',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '8px'
                }}
              >
                <Users size={28} />
              </div>
              <h3 style={{ margin: 0, color: 'var(--color-vinho)', fontSize: '1.2rem' }}>
                Código de Convite do Parceiro
              </h3>
              <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: '4px' }}>
                Envie este código para o seu parceiro inserir no aplicativo dele(a) ao fazer login ou cadastro.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#F7F9FB',
                border: '2px dashed #1E7E34',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                textAlign: 'center',
                marginBottom: '16px'
              }}
            >
              <span style={{ fontSize: '0.75rem', color: '#1E7E34', fontWeight: 700, textTransform: 'uppercase' }}>
                Seu Código Exclusivo
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, letterSpacing: '3px', color: '#1E7E34', margin: '6px 0' }}>
                {vinculoParceiro?.codigo || 'PARC-CARREGANDO'}
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                Válido por tempo indeterminado até a conexão ser concluída.
              </span>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <button
                onClick={copiarCodigo}
                className="btn btn-outline"
                style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                {copiado ? <Check size={18} color="#27AE60" /> : <Copy size={18} />}
                {copiado ? 'Copiado!' : 'Copiar Código'}
              </button>

              <a
                href={`https://api.whatsapp.com/send?text=${encodeURIComponent(
                  `Oi amor! Baixe o aplicativo Nymphia ou acesse a plataforma e use o meu código de parceiro: ${vinculoParceiro?.codigo || ''} para acompanhar a gestação comigo!`
                )}`}
                target="_blank"
                rel="noreferrer"
                className="btn"
                style={{
                  backgroundColor: '#25D366',
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  textDecoration: 'none',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: 600
                }}
              >
                <Share2 size={18} /> WhatsApp
              </a>
            </div>

            <button
              onClick={() => setModalCodigoParceiro(false)}
              className="btn"
              style={{ width: '100%', backgroundColor: '#F0F0F0', color: '#333333' }}
            >
              Fechar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
