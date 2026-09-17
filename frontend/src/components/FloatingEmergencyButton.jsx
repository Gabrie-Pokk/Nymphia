import React, { useState, useEffect } from 'react';
import { PhoneCall, AlertTriangle, X } from 'lucide-react';

export default function FloatingEmergencyButton({ currentPath, onNavigateEmergency }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [countdown, setCountdown] = useState(5);

  // Não exibe o botão na própria tela de emergência
  if (currentPath === '/emergencia') {
    return null;
  }

  useEffect(() => {
    let timer;
    if (isExpanded) {
      setCountdown(5);
      timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            setIsExpanded(false);
            return 5;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isExpanded]);

  const handleFirstTap = (e) => {
    e.stopPropagation();
    setIsExpanded(true);
  };

  const handleSecondTap = (e) => {
    e.stopPropagation();
    setIsExpanded(false);
    onNavigateEmergency();
  };

  const handleCancel = (e) => {
    e.stopPropagation();
    setIsExpanded(false);
  };

  return (
    <>
      {isExpanded ? (
        <div className="emergency-confirm-panel" role="alert" aria-live="assertive">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--color-vermelho)' }}>
              <AlertTriangle size={18} /> Acionar Emergência?
            </span>
            <button
              onClick={handleCancel}
              style={{ minHeight: '36px', minWidth: '36px', padding: '4px', background: 'transparent', color: 'var(--color-text-muted)' }}
              aria-label="Cancelar alerta de emergência"
            >
              <X size={18} />
            </button>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-main)' }}>
            Toque abaixo para abrir o canal direto com o <strong>SAMU 192</strong> e sua maternidade.
          </p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleSecondTap}
              style={{
                flex: 1,
                backgroundColor: 'var(--color-vermelho)',
                color: '#FFFFFF',
                fontWeight: 700,
                fontSize: '0.9rem',
                minHeight: '48px',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-emergency)'
              }}
              aria-label="Confirmar e abrir tela de emergência 192"
            >
              Confirmar ({countdown}s)
            </button>
            <button
              onClick={handleCancel}
              className="btn-outline"
              style={{ minHeight: '48px' }}
            >
              Voltar
            </button>
          </div>
        </div>
      ) : (
        <button
          className="floating-emergency-btn"
          onClick={handleFirstTap}
          aria-label="Botão de emergência médica SAMU 192. Toque duas vezes para confirmar."
          title="Emergência SAMU 192"
        >
          <PhoneCall size={26} strokeWidth={2.4} />
        </button>
      )}
    </>
  );
}
