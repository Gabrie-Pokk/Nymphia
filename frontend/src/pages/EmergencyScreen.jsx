import React, { useState, useEffect } from 'react';
import { Phone, Navigation, AlertCircle, ArrowLeft, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function EmergencyScreen({ onExit }) {
  const { authHeaders } = useAuth();
  const [maternidade, setMaternidade] = useState(() => {
    const cached = localStorage.getItem('nymphia_maternidade_cache');
    return cached ? JSON.parse(cached) : {
      nome: "Maternidade de Referência Regional",
      endereco: "Av. Principal da Saúde, 1000 - Centro",
      telefone: "1133334444"
    };
  });
  const [notificado, setNotificado] = useState(false);

  useEffect(() => {
    // 1. Tenta carregar dados atualizados do perfil clínico (se conectado)
    fetch('/perfil-clinico', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.maternidade_nome) {
          const matData = {
            nome: data.maternidade_nome,
            endereco: data.maternidade_endereco || "Endereço cadastrado no onboarding",
            telefone: data.maternidade_telefone || "192"
          };
          setMaternidade(matData);
          localStorage.setItem('nymphia_maternidade_cache', JSON.stringify(matData));
        }
      })
      .catch(() => {
        // Modo offline gracioso
      });

    // 2. Dispara notificação paralela e registro de emergência (NUNCA BLOQUEIA)
    fetch('/emergencia/notificar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ momento: new Date().toISOString() })
    })
      .then(() => setNotificado(true))
      .catch(() => {
        // Falha de rede não impede a tela do SAMU
      });
  }, []);

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
          Se você está em trabalho de parto, sangrando ou com dores intensas, ligue imediatamente para o socorro.
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

      {/* Cartão da Maternidade de Referência */}
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

      {/* Status da Notificação Paralela */}
      <div style={{ marginTop: 'auto', textAlign: 'center', paddingTop: '20px' }}>
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
          {notificado ? (
            <span style={{ color: '#27AE60', fontWeight: 600 }}>
              ✓ Alerta transmitido em paralelo para sua equipe de saúde.
            </span>
          ) : (
            <span>Conectando aos serviços de apoio em paralelo...</span>
          )}
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
          A Nymphia orienta e conecta você ao socorro. A discagem é sempre confirmada por você.
        </p>
      </div>
    </div>
  );
}
