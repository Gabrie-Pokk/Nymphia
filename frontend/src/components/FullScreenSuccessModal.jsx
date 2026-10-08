import React, { useEffect } from 'react';
import { CheckCircle2, Sparkles, AlertTriangle, ArrowRight, X } from 'lucide-react';

export default function FullScreenSuccessModal({
  isOpen,
  onClose,
  title = 'Enviado com Sucesso!',
  subtitle = 'Seu registro foi salvo e integrado com segurança ao seu histórico de cuidado.',
  highlightText,
  alertaUrgente = null,
  orientacao = null,
  confirmButtonText = 'Continuar',
  autoCloseSeconds = 4,
  onConfirm
}) {
  useEffect(() => {
    if (!isOpen) return;

    if (autoCloseSeconds && autoCloseSeconds > 0 && !alertaUrgente) {
      const timer = setTimeout(() => {
        if (onClose) onClose();
      }, autoCloseSeconds * 1000);
      return () => clearTimeout(timer);
    }
  }, [isOpen, autoCloseSeconds, alertaUrgente, onClose]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (onConfirm) onConfirm();
    if (onClose) onClose();
  };

  const temAlerta = Boolean(alertaUrgente);

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 99999,
        backgroundColor: 'rgba(34, 10, 16, 0.78)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        animation: 'fadeInOverlay 0.25s ease-out'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !temAlerta) {
          onClose && onClose();
        }
      }}
    >
      <style>{`
        @keyframes fadeInOverlay {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleUpModal {
          from { opacity: 0; transform: scale(0.88) translateY(12px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes pulseSuccessIcon {
          0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(194, 24, 91, 0.4); }
          70% { transform: scale(1.05); box-shadow: 0 0 0 16px rgba(194, 24, 91, 0); }
          100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(194, 24, 91, 0); }
        }
      `}</style>

      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '460px',
          backgroundColor: '#FFFFFF',
          borderRadius: '24px',
          boxShadow: '0 24px 48px rgba(34, 10, 16, 0.35)',
          padding: '32px 24px',
          textAlign: 'center',
          position: 'relative',
          animation: 'scaleUpModal 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          border: temAlerta ? '2px solid var(--color-vermelho)' : '2px solid var(--color-rosa)'
        }}
      >
        {/* Botão de Fechar discreto */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: '50%'
          }}
          aria-label="Fechar"
        >
          <X size={20} />
        </button>

        {/* Ícone Celebratório */}
        <div
          style={{
            width: '84px',
            height: '84px',
            borderRadius: '50%',
            backgroundColor: temAlerta ? '#FDEDEC' : 'var(--color-rosa-claro)',
            color: temAlerta ? 'var(--color-vermelho)' : 'var(--color-rosa)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px auto',
            animation: 'pulseSuccessIcon 1.4s ease-out'
          }}
        >
          {temAlerta ? (
            <AlertTriangle size={46} strokeWidth={2.3} />
          ) : (
            <CheckCircle2 size={48} strokeWidth={2.4} />
          )}
        </div>

        {/* Título Principal de Confirmação */}
        <h2
          style={{
            fontSize: '1.4rem',
            fontWeight: 800,
            color: temAlerta ? 'var(--color-vermelho)' : 'var(--color-vinho)',
            marginBottom: '10px',
            lineHeight: 1.25
          }}
        >
          {title}
        </h2>

        {/* Subtítulo / Mensagem explicativa */}
        <p
          style={{
            fontSize: '0.94rem',
            color: 'var(--color-text-muted)',
            lineHeight: 1.45,
            marginBottom: highlightText || orientacao ? '16px' : '24px'
          }}
        >
          {subtitle}
        </p>

        {/* Destaque opcional */}
        {highlightText && (
          <div
            style={{
              backgroundColor: '#FAF4F5',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: '0.86rem',
              color: 'var(--color-vinho)',
              fontWeight: 600,
              marginBottom: '18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            <Sparkles size={16} color="var(--color-rosa)" style={{ flexShrink: 0 }} />
            <span>{highlightText}</span>
          </div>
        )}

        {/* Bloco de Alerta / Orientação Clínica se houver */}
        {orientacao && (
          <div
            style={{
              backgroundColor: temAlerta ? '#FDEEE9' : '#EAF7EF',
              border: temAlerta ? '1.5px solid var(--color-vermelho)' : '1px solid #27AE60',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              marginBottom: '22px',
              textAlign: 'left'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              {temAlerta ? (
                <AlertTriangle size={18} color="var(--color-vermelho)" />
              ) : (
                <CheckCircle2 size={18} color="#27AE60" />
              )}
              <strong style={{ fontSize: '0.9rem', color: temAlerta ? 'var(--color-vermelho)' : '#1E7E34' }}>
                {temAlerta ? 'Sinal de Atenção Obstétrica:' : 'Orientação Personalizada:'}
              </strong>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#2C181E', lineHeight: 1.4, margin: 0 }}>
              {orientacao}
            </p>
          </div>
        )}

        {/* Botão de Confirmação na Tela Inteira */}
        <button
          type="button"
          onClick={handleConfirm}
          className="btn btn-primary"
          style={{
            width: '100%',
            minHeight: '48px',
            fontSize: '1rem',
            fontWeight: 700,
            borderRadius: 'var(--radius-full)',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: 'var(--shadow-md)'
          }}
        >
          {confirmButtonText}
          <ArrowRight size={18} />
        </button>

        {!temAlerta && autoCloseSeconds > 0 && (
          <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '12px', marginBottom: 0 }}>
            Fechando automaticamente em alguns instantes...
          </p>
        )}
      </div>
    </div>
  );
}
