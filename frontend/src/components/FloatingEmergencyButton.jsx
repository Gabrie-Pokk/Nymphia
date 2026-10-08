import React, { useState, useEffect, useRef } from 'react';
import { PhoneCall, AlertTriangle, X } from 'lucide-react';

export default function FloatingEmergencyButton({ currentPath, onNavigateEmergency }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const isChat = currentPath === '/conversa';

  // Posição personalizada pelo usuário (se arrastado)
  const [customPos, setCustomPos] = useState(null);
  const draggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0, startPos: { x: 0, y: 0 } });
  const hasMovedRef = useRef(false);

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

  const handleTouchStart = (e) => {
    const touch = e.touches[0];
    const rect = e.currentTarget.getBoundingClientRect();
    draggingRef.current = true;
    hasMovedRef.current = false;
    dragStartRef.current = {
      touchX: touch.clientX,
      touchY: touch.clientY,
      posX: customPos ? customPos.x : rect.left,
      posY: customPos ? customPos.y : rect.top
    };
  };

  const handleTouchMove = (e) => {
    if (!draggingRef.current) return;
    const touch = e.touches[0];
    const dx = touch.clientX - dragStartRef.current.touchX;
    const dy = touch.clientY - dragStartRef.current.touchY;

    if (Math.hypot(dx, dy) > 8) {
      hasMovedRef.current = true;
      const newX = Math.max(10, Math.min(window.innerWidth - 68, dragStartRef.current.posX + dx));
      const newY = Math.max(10, Math.min(window.innerHeight - 74, dragStartRef.current.posY + dy));
      setCustomPos({ x: newX, y: newY });
    }
  };

  const handleTouchEnd = (e) => {
    draggingRef.current = false;
    if (!hasMovedRef.current) {
      // Foi apenas um clique/toque
      handleFirstTap(e);
    }
  };

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

  // Posição base padrão (acima da barra de navegação ou acima do input do chat)
  const defaultStyle = {
    bottom: isChat ? '142px' : '84px',
    right: '18px'
  };

  const positionStyle = customPos
    ? { left: `${customPos.x}px`, top: `${customPos.y}px`, right: 'auto', bottom: 'auto' }
    : defaultStyle;

  return (
    <>
      {isExpanded ? (
        <div
          className="emergency-confirm-panel"
          style={{
            ...positionStyle,
            // Se posicionado perto do rodapé, mantém visível
            maxWidth: '300px'
          }}
          role="alert"
          aria-live="assertive"
        >
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
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-main)', margin: '4px 0 10px 0' }}>
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
          style={{
            ...positionStyle,
            width: '58px',
            height: '58px',
            minWidth: '58px',
            minHeight: '58px',
            maxWidth: '58px',
            maxHeight: '58px',
            aspectRatio: '1 / 1',
            borderRadius: '50%',
            flexShrink: 0,
            touchAction: 'none'
          }}
          onClick={(e) => {
            if (!hasMovedRef.current) handleFirstTap(e);
          }}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          aria-label="Botão de emergência médica SAMU 192. Arraste para mover ou toque duas vezes para acionar."
          title="Emergência SAMU 192 (Toque para acionar / Arraste para mover)"
        >
          <PhoneCall size={26} strokeWidth={2.4} />
        </button>
      )}
    </>
  );
}

