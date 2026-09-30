import React, { useState, useEffect } from 'react';
import {
  Volume2,
  X,
  Sparkles,
  Sliders,
  Play,
  Square,
  Check,
  Heart,
  Smile,
  Zap,
  Settings
} from 'lucide-react';
import {
  getVoicePreferences,
  saveVoicePreferences,
  getAvailablePortugueseVoices,
  PERSONAS_VOZ,
  speakNymphia,
  stopNymphiaVoice,
  isNymphiaSpeaking
} from '../utils/voiceService';

export default function VoiceSettingsModal({ isOpen, onClose, onSaved }) {
  const [prefs, setPrefs] = useState(getVoicePreferences());
  const [vozesDisponiveis, setVozesDisponiveis] = useState([]);
  const [tocandoPrevia, setTocandoPrevia] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    setPrefs(getVoicePreferences());

    const atualizarVozes = () => {
      const vozes = getAvailablePortugueseVoices();
      setVozesDisponiveis(vozes);
    };

    atualizarVozes();

    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = atualizarVozes;
    }

    return () => {
      stopNymphiaVoice();
      setTocandoPrevia(false);
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSelecionarPersona = (personaKey) => {
    const config = PERSONAS_VOZ[personaKey];
    if (config) {
      const novos = {
        ...prefs,
        persona: personaKey,
        pitch: config.pitch,
        rate: config.rate
      };
      setPrefs(novos);
      saveVoicePreferences(novos);
    }
  };

  const handleMudarSlider = (campo, valor) => {
    const novos = {
      ...prefs,
      persona: 'custom',
      [campo]: parseFloat(valor)
    };
    setPrefs(novos);
    saveVoicePreferences(novos);
  };

  const handleMudarVozURI = (uri) => {
    const novos = {
      ...prefs,
      voiceURI: uri
    };
    setPrefs(novos);
    saveVoicePreferences(novos);
  };

  const handleToggleAutoFalar = (checked) => {
    const novos = {
      ...prefs,
      autoFalarChat: checked
    };
    setPrefs(novos);
    saveVoicePreferences(novos);
  };

  const handleOuvirPrevia = () => {
    if (tocandoPrevia) {
      stopNymphiaVoice();
      setTocandoPrevia(false);
      return;
    }

    setTocandoPrevia(true);
    const fraseExemplo =
      'Olá, querida! Sou a Nymphia, sua assistente e companheira de gestação. ' +
      'Estou aqui com muito carinho para cuidar de você e do seu bebê a cada semana.';

    speakNymphia(fraseExemplo, {
      pitch: prefs.pitch,
      rate: prefs.rate,
      onStart: () => setTocandoPrevia(true),
      onEnd: () => setTocandoPrevia(false),
      onError: () => setTocandoPrevia(false)
    });
  };

  const handleSalvarEFechar = () => {
    stopNymphiaVoice();
    saveVoicePreferences(prefs);
    if (onSaved) onSaved(prefs);
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(34, 10, 16, 0.65)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: '16px'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) handleSalvarEFechar();
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '520px',
          maxHeight: '90vh',
          overflowY: 'auto',
          backgroundColor: '#FFFFFF',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: '24px',
          position: 'relative'
        }}
      >
        {/* Top Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-rosa-claro)',
                color: 'var(--color-rosa)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Volume2 size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', margin: 0, color: 'var(--color-vinho)' }}>
                Personalizar Voz da Nymphia
              </h3>
              <p className="text-muted" style={{ fontSize: '0.78rem', margin: '2px 0 0 0' }}>
                Português fluente, carinhoso e adaptado ao seu bem-estar
              </p>
            </div>
          </div>

          <button
            onClick={handleSalvarEFechar}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-text-muted)',
              padding: '6px'
            }}
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        {/* 1. Escolha da Persona da Voz */}
        <label style={{ display: 'block', fontSize: '0.86rem', fontWeight: 600, color: 'var(--color-vinho)', marginBottom: '8px' }}>
          Estilo & Personalidade da Voz:
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginBottom: '18px' }}>
          {Object.values(PERSONAS_VOZ).map((p) => {
            const isSelected = prefs.persona === p.id;
            return (
              <div
                key={p.id}
                onClick={() => handleSelecionarPersona(p.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: isSelected ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                  backgroundColor: isSelected ? 'var(--color-rosa-claro)' : '#FFFFFF',
                  cursor: 'pointer',
                  transition: 'var(--transition)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      color: isSelected ? 'var(--color-rosa)' : 'var(--color-text-muted)',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    {p.id === 'carinhosa' && <Heart size={18} />}
                    {p.id === 'calma' && <Smile size={18} />}
                    {p.id === 'encorajadora' && <Zap size={18} />}
                    {p.id === 'custom' && <Sliders size={18} />}
                  </div>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--color-vinho)' }}>{p.nome}</h4>
                    <p style={{ margin: '2px 0 0 0', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      {p.descricao}
                    </p>
                  </div>
                </div>
                {isSelected && <Check size={18} color="var(--color-rosa)" style={{ flexShrink: 0 }} />}
              </div>
            );
          })}
        </div>

        {/* 2. Seleção do Timbre / Voz em Português */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '0.86rem', fontWeight: 600, color: 'var(--color-vinho)', marginBottom: '6px' }}>
            Voz do Sistema (Português do Brasil):
          </label>
          <select
            className="form-control"
            value={prefs.voiceURI || ''}
            onChange={(e) => handleMudarVozURI(e.target.value)}
            style={{ fontSize: '0.85rem', padding: '10px 12px' }}
          >
            {vozesDisponiveis.length === 0 ? (
              <option value="">Voz Padrão Brasileira do Navegador</option>
            ) : (
              vozesDisponiveis.map((v) => (
                <option key={v.voiceURI} value={v.voiceURI}>
                  {v.name} {v.lang.includes('BR') ? '🇧🇷' : '🇵🇹'}
                </option>
              ))
            )}
          </select>
          <p className="text-muted" style={{ fontSize: '0.72rem', marginTop: '4px' }}>
            💡 Dica: Vozes rotuladas como "Google", "Natural" ou "Online" oferecem a melhor fluência e expressividade.
          </p>
        </div>

        {/* 3. Sliders de Ajuste Fino */}
        <div style={{ backgroundColor: '#FAF4F5', padding: '14px', borderRadius: 'var(--radius-md)', marginBottom: '18px' }}>
          {/* Pitch / Tom */}
          <div style={{ marginBottom: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
              <span style={{ fontWeight: 600, color: 'var(--color-vinho)' }}>Tom da Voz (Pitch):</span>
              <span style={{ color: 'var(--color-rosa)', fontWeight: 700 }}>
                {prefs.pitch <= 0.95 ? 'Grave / Suave' : prefs.pitch >= 1.15 ? 'Agudo / Doce' : 'Equilibrado'} ({prefs.pitch}x)
              </span>
            </div>
            <input
              type="range"
              min="0.80"
              max="1.30"
              step="0.05"
              value={prefs.pitch}
              onChange={(e) => handleMudarSlider('pitch', e.target.value)}
              style={{ width: '100%', accentColor: 'var(--color-rosa)' }}
            />
          </div>

          {/* Rate / Velocidade */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
              <span style={{ fontWeight: 600, color: 'var(--color-vinho)' }}>Velocidade de Fala:</span>
              <span style={{ color: 'var(--color-rosa)', fontWeight: 700 }}>
                {prefs.rate <= 0.9 ? 'Calma & Pausada' : prefs.rate >= 1.05 ? 'Rápida' : 'Natural'} ({prefs.rate}x)
              </span>
            </div>
            <input
              type="range"
              min="0.80"
              max="1.25"
              step="0.05"
              value={prefs.rate}
              onChange={(e) => handleMudarSlider('rate', e.target.value)}
              style={{ width: '100%', accentColor: 'var(--color-rosa)' }}
            />
          </div>
        </div>

        {/* 4. Opções Adicionais */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
            <input
              type="checkbox"
              checked={prefs.autoFalarChat || false}
              onChange={(e) => handleToggleAutoFalar(e.target.checked)}
              style={{ accentColor: 'var(--color-rosa)', width: '16px', height: '16px' }}
            />
            <span style={{ color: 'var(--color-text-main)' }}>
              Falar automaticamente as respostas da Nymphia no Chat
            </span>
          </label>
        </div>

        {/* Ações Inferiores */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleOuvirPrevia}
            className="btn btn-outline"
            style={{ flex: 1, borderColor: 'var(--color-rosa)', color: 'var(--color-rosa)' }}
          >
            {tocandoPrevia ? (
              <>
                <Square size={16} /> Parar Áudio
              </>
            ) : (
              <>
                <Play size={16} /> Ouvir Teste
              </>
            )}
          </button>

          <button onClick={handleSalvarEFechar} className="btn btn-primary" style={{ flex: 1 }}>
            Salvar Preferências
          </button>
        </div>
      </div>
    </div>
  );
}
