import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { Heart, Activity, ShieldCheck, ArrowRight } from 'lucide-react';

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

  const handleNext = () => {
    if (currentSlide < SLIDES.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      localStorage.setItem('nymphia_intro_viewed', 'true');
      onFinish();
    }
  };

  const handleSkip = () => {
    localStorage.setItem('nymphia_intro_viewed', 'true');
    onFinish();
  };

  const slide = SLIDES[currentSlide];
  const IconComponent = slide.icon;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', padding: '24px', justifyContent: 'space-between', backgroundColor: '#FFFFFF' }}>
      {/* Top Bar com Logo e Pular */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <LotusLogo size={28} color="var(--color-vinho)" />
          <span style={{ fontWeight: 700, color: 'var(--color-vinho)', fontSize: '1.1rem' }}>Nymphia</span>
        </div>
        <button
          onClick={handleSkip}
          style={{ background: 'transparent', color: 'var(--color-text-muted)', border: 'none', fontWeight: 600, fontSize: '0.85rem' }}
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

      {/* Footer com Indicadores e Botão Avançar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '24px' }}>
          {SLIDES.map((_, idx) => (
            <div
              key={idx}
              style={{
                width: currentSlide === idx ? '24px' : '8px',
                height: '8px',
                borderRadius: '4px',
                backgroundColor: currentSlide === idx ? 'var(--color-rosa)' : 'var(--color-border)',
                transition: 'all 0.3s ease'
              }}
            />
          ))}
        </div>

        <button
          onClick={handleNext}
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '52px', fontSize: '1.05rem' }}
        >
          {currentSlide === SLIDES.length - 1 ? "Começar Agora" : "Próximo"}
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}
