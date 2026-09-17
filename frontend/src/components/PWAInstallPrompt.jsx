import React, { useState, useEffect } from 'react';
import { Download, Smartphone, X, CheckCircle2, Share } from 'lucide-react';

export default function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);
  const [showIOSGuide, setShowIOSGuide] = useState(false);

  useEffect(() => {
    // Verifica se já está rodando como app standalone (instalado)
    const standalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
    setIsStandalone(Boolean(standalone));

    // Detecta se é iOS (Safari)
    const userAgent = window.navigator.userAgent.toLowerCase();
    const iOS = /iphone|ipad|ipod/.test(userAgent);
    setIsIOS(iOS);

    // Evento padrão do navegador no Android / Chrome / Edge
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Exibe banner se não tiver sido dispensado nesta sessão
      if (!sessionStorage.getItem('nymphia_pwa_dismissed')) {
        setShowPrompt(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Se for iOS e não for standalone e não foi dispensado
    if (iOS && !standalone && !sessionStorage.getItem('nymphia_pwa_dismissed')) {
      setShowPrompt(true);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = async () => {
    if (isIOS) {
      setShowIOSGuide(true);
      return;
    }

    if (!deferredPrompt) {
      alert("Para instalar, use a opção 'Adicionar à tela inicial' ou 'Instalar aplicativo' no menu do seu navegador.");
      return;
    }

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setShowPrompt(false);
      setDeferredPrompt(null);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    setShowIOSGuide(false);
    sessionStorage.setItem('nymphia_pwa_dismissed', 'true');
  };

  // Se já estiver instalado ou não houver necessidade de exibir
  if (isStandalone || !showPrompt) {
    return null;
  }

  return (
    <>
      <div 
        id="pwa-install-banner"
        style={{
          background: 'linear-gradient(135deg, #5C1A2A 0%, #3D0F1B 100%)',
          color: '#FDF0F2',
          padding: '0.65rem 1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.85rem',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          position: 'sticky',
          top: 0,
          zIndex: 9998,
          borderBottom: '1px solid rgba(201, 168, 76, 0.4)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div 
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'rgba(255,255,255,0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#C9A84C'
            }}
          >
            <Smartphone size={18} />
          </div>
          <div>
            <strong style={{ display: 'block', color: '#FFF' }}>Instale a Nymphia no Celular</strong>
            <span style={{ fontSize: '0.75rem', opacity: 0.85 }}>Acesso rápido 1-toque e emergência offline</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            id="btn-instalar-pwa"
            onClick={handleInstallClick}
            style={{
              background: 'linear-gradient(135deg, #C9A84C 0%, #B38F3A 100%)',
              color: '#5C1A2A',
              border: 'none',
              borderRadius: 20,
              padding: '0.35rem 0.85rem',
              fontWeight: 700,
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              cursor: 'pointer',
              boxShadow: '0 2px 6px rgba(0,0,0,0.2)'
            }}
          >
            <Download size={14} />
            Instalar
          </button>
          <button
            onClick={handleDismiss}
            style={{
              background: 'none',
              border: 'none',
              color: '#FDF0F2',
              opacity: 0.6,
              cursor: 'pointer',
              padding: '0.2rem',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Dispensar"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Modal explicativo para iOS */}
      {showIOSGuide && (
        <div 
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            zIndex: 99999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem'
          }}
          onClick={() => setShowIOSGuide(false)}
        >
          <div 
            style={{
              background: '#FFF',
              borderRadius: 16,
              padding: '1.5rem',
              maxWidth: 360,
              width: '100%',
              boxShadow: '0 12px 30px rgba(0,0,0,0.3)',
              color: '#333',
              textAlign: 'center'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div 
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: '#FDF0F2',
                color: '#5C1A2A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem'
              }}
            >
              <Share size={24} />
            </div>
            <h3 style={{ margin: '0 0 0.5rem', color: '#5C1A2A' }}>Como instalar no iPhone / iPad</h3>
            <p style={{ fontSize: '0.9rem', color: '#666', lineHeight: 1.5, margin: '0 0 1.25rem' }}>
              No navegador Safari do seu iPhone:
            </p>
            <ol style={{ textAlign: 'left', fontSize: '0.85rem', color: '#444', paddingLeft: '1.25rem', lineHeight: 1.6, margin: '0 0 1.25rem' }}>
              <li>Toque no botão <strong>Compartilhar</strong> (ícone do quadrado com a seta para cima <Share size={12} style={{ display: 'inline' }} />) na barra inferior.</li>
              <li>Role para baixo e toque em <strong>"Adicionar à Tela de Início"</strong>.</li>
              <li>Toque em <strong>"Adicionar"</strong> no canto superior direito.</li>
            </ol>
            <button
              onClick={() => setShowIOSGuide(false)}
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.65rem' }}
            >
              Entendi
            </button>
          </div>
        </div>
      )}
    </>
  );
}
