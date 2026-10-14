import React, { useState } from 'react';
import { HeartHandshake, Info } from 'lucide-react';
import AiTransparencyModal from './AiTransparencyModal';

export default function TriageDisclaimer() {
  const [modalAberto, setModalAberto] = useState(false);

  return (
    <>
      <div className="triage-disclaimer" role="note" aria-label="Aviso sobre apoio de inteligência artificial">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <HeartHandshake size={18} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--color-dourado)' }} />
          <div style={{ flex: 1 }}>
            <strong style={{ display: 'block', marginBottom: '3px' }}>Apoio de Cuidado & Bem-Estar (CFM 2.454/2026 e CDC):</strong>
            As análises estatísticas e orientações apresentadas constituem <strong>triagem preditiva e apoio educativo</strong>, sujeitas a margem probabilística (falsos positivos/negativos), e <strong>NÃO CONSTITUEM DIAGNÓSTICO MÉDICO</strong> nem substituem consultas presenciais e decisões clínicas do seu médico obstetra. Qualquer dúvida ou sintoma deve ser reportado imediatamente à sua equipe de saúde.
            <div style={{ marginTop: '6px' }}>
              <button
                type="button"
                onClick={() => setModalAberto(true)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  padding: 0,
                  color: 'var(--color-vinho)',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Info size={13} color="var(--color-dourado)" />
                Ver Matriz de Métricas dos Modelos & Governança de IA (CFM nº 2.454/2026)
              </button>
            </div>
          </div>
        </div>
      </div>

      <AiTransparencyModal isOpen={modalAberto} onClose={() => setModalAberto(false)} />
    </>
  );
}

