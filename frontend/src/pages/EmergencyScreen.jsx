import React, { useState, useEffect } from 'react';
import { Phone, Navigation, AlertCircle, ArrowLeft, ShieldCheck, MapPin } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function EmergencyScreen({ onExit }) {
  const { authHeaders, isAuthenticated } = useAuth();
  const [maternidade, setMaternidade] = useState(() => {
    const cached = localStorage.getItem('nymphia_maternidade_cache');
    try {
      const parsed = cached ? JSON.parse(cached) : null;
      // Rejeita dados fictícios de demonstração herdados do cache
      if (parsed && parsed.nome && !parsed.nome.includes("Maternidade de Referência Regional")) {
        return parsed;
      }
    } catch (e) {}
    return null;
  });

  const [notificacaoStatus, setNotificacaoStatus] = useState({
    enviado: false,
    profissionalNotificado: false,
    erro: false
  });

  useEffect(() => {
    // 1. Tenta carregar dados atualizados do perfil clínico (se conectado)
    if (isAuthenticated) {
      fetch('/perfil-clinico', { headers: authHeaders() })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data && data.maternidade_nome && !data.maternidade_nome.includes("Maternidade de Referência Regional")) {
            const matData = {
              nome: data.maternidade_nome,
              endereco: data.maternidade_endereco || "Endereço cadastrado no onboarding",
              telefone: data.maternidade_telefone || "192",
              latitude: data.maternidade_latitude,
              longitude: data.maternidade_longitude
            };
            setMaternidade(matData);
            localStorage.setItem('nymphia_maternidade_cache', JSON.stringify(matData));
          }
        })
        .catch(() => {
          // Modo offline gracioso
        });
    }

    // 2. Dispara notificação paralela e registro de emergência (NUNCA BLOQUEIA)
    fetch('/emergencia/notificar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ momento: new Date().toISOString() })
    })
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json().catch(() => ({}));
          setNotificacaoStatus({
            enviado: true,
            profissionalNotificado: Boolean(data.profissional_notificado),
            erro: false
          });
        } else {
          setNotificacaoStatus({ enviado: false, profissionalNotificado: false, erro: true });
        }
      })
      .catch(() => {
        setNotificacaoStatus({ enviado: false, profissionalNotificado: false, erro: true });
      });
  }, [isAuthenticated]);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#FFFFFF', padding: '24px', display: 'flex', flexDirection: 'column' }}>
      {/* Botão de saída discreto */}
      <div style={{ marginBottom: '16px' }}>
        <button
          onClick={onExit}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.88rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
          aria-label="Sair da tela de emergência"
        >
          <ArrowLeft size={18} /> Voltar ao aplicativo
        </button>
      </div>

      {/* Header de Alerta Máximo */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div
          style={{
            width: '72px',
            height: '72px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-vermelho)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto',
            boxShadow: 'var(--shadow-emergency)'
          }}
        >
          <Phone size={36} />
        </div>
        <h1 style={{ color: 'var(--color-vermelho)', fontSize: '1.6rem', marginBottom: '6px' }}>
          Canal de Emergência Obstétrica
        </h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.95rem' }}>
          Se você está em trabalho de parto, sangrando, com convulsão ou perda de líquido, ligue imediatamente para o socorro.
        </p>
      </div>

      {/* AÇÃO PRINCIPAL: DISCAR SAMU 192 (Dominante em tela cheia) */}
      <a
        href="tel:192"
        style={{
          backgroundColor: 'var(--color-vermelho)',
          color: '#FFFFFF',
          textDecoration: 'none',
          padding: '20px',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '14px',
          fontSize: '1.35rem',
          fontWeight: 800,
          boxShadow: 'var(--shadow-emergency)',
          marginBottom: '28px',
          textAlign: 'center',
          transition: 'var(--transition)'
        }}
        aria-label="Ligar para o SAMU no número 192 agora"
      >
        <Phone size={32} />
        LIGAR PARA O SAMU (192)
      </a>

      {/* Cartão da Maternidade de Referência ou Orientação Segura */}
      {maternidade ? (
        <div className="card" style={{ border: '2px solid var(--color-border)', backgroundColor: 'var(--color-rosa-claro)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <ShieldCheck size={22} color="var(--color-vinho)" />
            <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Sua Maternidade de Referência</h2>
          </div>
          <p style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--color-vinho)', marginBottom: '4px' }}>
            {maternidade.nome}
          </p>
          <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', marginBottom: '16px' }}>
            {maternidade.endereco}
          </p>

          <div style={{ display: 'flex', gap: '10px' }}>
            <a
              href={`tel:${maternidade.telefone}`}
              className="btn btn-vinho"
              style={{ flex: 1, textDecoration: 'none' }}
              aria-label={`Ligar para a maternidade: ${maternidade.telefone}`}
            >
              <Phone size={18} />
              Ligar ({maternidade.telefone || 'Maternidade'})
            </a>
            <a
              href={maternidade.latitude && maternidade.longitude ? `geo:${maternidade.latitude},${maternidade.longitude}?q=${encodeURIComponent(maternidade.nome)}` : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(maternidade.endereco || maternidade.nome)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline"
              style={{ flex: 1, textDecoration: 'none' }}
              aria-label="Abrir rota no mapa até a maternidade"
            >
              <Navigation size={18} />
              Ver Rota
            </a>
          </div>
        </div>
      ) : (
        <div className="card" style={{ border: '1.5px solid var(--color-border)', backgroundColor: '#FAFAFA' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <MapPin size={22} color="var(--color-vinho)" />
            <h2 style={{ fontSize: '1.05rem', margin: 0, color: 'var(--color-vinho)' }}>Maternidade mais Próxima</h2>
          </div>
          <p style={{ fontSize: '0.88rem', color: 'var(--color-text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
            Nenhuma maternidade personalizada cadastrada no seu perfil. Em caso de urgência, dirija-se à maternidade ou pronto-socorro obstétrico mais próximo da sua localização ou aguarde as instruções do SAMU 192.
          </p>
          <a
            href="https://www.google.com/maps/search/?api=1&query=maternidade+pronto+socorro+obstetrico"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-outline"
            style={{ width: '100%', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', minHeight: '44px' }}
            aria-label="Buscar maternidades e prontos-socorros próximos no mapa"
          >
            <Navigation size={18} />
            Buscar Maternidades Próximas no Mapa
          </a>
        </div>
      )}

      {/* Status da Notificação Paralela */}
      <div style={{ marginTop: 'auto', textAlign: 'center', paddingTop: '20px' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
          {notificacaoStatus.enviado && notificacaoStatus.profissionalNotificado ? (
            <span style={{ color: '#27AE60', fontWeight: 600 }}>
              ✓ Alerta transmitido em paralelo para sua equipe de saúde vinculada.
            </span>
          ) : notificacaoStatus.enviado && !notificacaoStatus.profissionalNotificado ? (
            <span style={{ color: 'var(--color-text-muted)', fontWeight: 500 }}>
              ℹ️ Chamada de emergência pública registrada. Sem equipe médica vinculada nesta sessão — o atendimento depende exclusivamente da discagem ao SAMU 192.
            </span>
          ) : notificacaoStatus.erro ? (
            <span style={{ color: 'var(--color-vermelho)', fontWeight: 600 }}>
              ⚠️ Não foi possível registrar o evento no servidor. Disque 192 (SAMU) imediatamente no seu telefone!
            </span>
          ) : (
            <span>Conectando aos serviços de apoio em paralelo...</span>
          )}
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '6px' }}>
          A Nymphia orienta e conecta você ao socorro. A discagem para o 192 é sempre confirmada diretamente por você no telefone.
        </p>
      </div>
    </div>
  );
}
