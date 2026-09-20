import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { Heart, Activity, ShieldCheck, ArrowRight, ArrowLeft } from 'lucide-react';

const SLIDES = [
  {
    icon: Activity,
    titulo: "Acompanhamento diário contínuo",
    descricao: "Entre uma consulta e outra do pré-natal, você não está desamparada. A Nymphia aprende com sua rotina e cruza seus sintomas para proteger você e seu bebê."
  },
  {
    icon: Heart,
    titulo: "Cada batimento importa",
    descricao: "Algoritmos de inteligência clínica e regras obstétricas identificam sinais de alerta antes do agravamento, conectando você ao seu médico na hora certa."
  },
  {
    icon: ShieldCheck,
    titulo: "Sua segurança em primeiro lugar",
    descricao: "Canal de emergência direto para o SAMU 192 e sua maternidade de referência, acessível com um toque em qualquer momento da gestação."
  }
];

export default function WelcomeIntro({ onFinish }) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);

  const minSwipeDistance = 50;

  const handleNext = () => {
    if (currentSlide < SLIDES.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      localStorage.setItem('nymphia_intro_viewed', 'true');
      onFinish();
    }
  };

  const handlePrev = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  const handleSkip = () => {
    localStorage.setItem('nymphia_intro_viewed', 'true');
    onFinish();
  };

  const onTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;
    if (isLeftSwipe) {
      handleNext();
    } else if (isRightSwipe) {
      handlePrev();
    }
  };

  const slide = SLIDES[currentSlide];
  const IconComponent = slide.icon;

  return (
    <div
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px',
        justifyContent: 'space-between',
        backgroundColor: '#FFFFFF',
        userSelect: 'none'
      }}
    >
      {/* Top Bar com Logo e Pular */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <LotusLogo size={28} color="var(--color-vinho)" />
          <span style={{ fontWeight: 700, color: 'var(--color-vinho)', fontSize: '1.1rem' }}>Nymphia</span>
        </div>
        <button
          onClick={handleSkip}
          style={{ background: 'transparent', color: 'var(--color-text-muted)', border: 'none', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
        >
          Pular
        </button>
      </div>

      {/* Slide Content */}
      <div style={{ textAlign: 'center', padding: '32px 12px' }}>
        <div
          style={{
            width: '90px',
            height: '90px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-rosa-claro)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 28px auto',
            color: 'var(--color-rosa)',
            boxShadow: 'var(--shadow-md)'
          }}
        >
          <IconComponent size={44} strokeWidth={1.8} />
        </div>

        <h1 style={{ fontSize: '1.5rem', color: 'var(--color-vinho)', marginBottom: '14px', lineHeight: 1.3 }}>
          {slide.titulo}
        </h1>

        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.98rem', maxWidth: '380px', margin: '0 auto', lineHeight: 1.5 }}>
          {slide.descricao}
        </p>
      </div>

      {/* Footer com Indicadores Clicáveis e Botões Voltar / Avançar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '24px' }}>
          {SLIDES.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentSlide(idx)}
              aria-label={`Ir para o slide ${idx + 1}`}
              style={{
                width: currentSlide === idx ? '24px' : '10px',
                height: '10px',
                borderRadius: '5px',
                backgroundColor: currentSlide === idx ? 'var(--color-rosa)' : 'var(--color-border)',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
                transition: 'all 0.3s ease'
              }}
            />
          ))}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          {currentSlide > 0 && (
            <button
              onClick={handlePrev}
              className="btn btn-outline"
              style={{ minHeight: '52px', minWidth: '100px', fontSize: '1rem' }}
              aria-label="Voltar para o slide anterior"
            >
              <ArrowLeft size={18} /> Voltar
            </button>
          )}

          <button
            onClick={handleNext}
            className="btn btn-primary"
            style={{ flex: 1, minHeight: '52px', fontSize: '1.05rem' }}
          >
            {currentSlide === SLIDES.length - 1 ? "Começar Agora" : "Próximo"}
            <ArrowRight size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
