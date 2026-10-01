import React from 'react';
import { HeartHandshake } from 'lucide-react';

export default function TriageDisclaimer() {
  return (
    <div className="triage-disclaimer" role="note" aria-label="Aviso sobre apoio de inteligência artificial">
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <HeartHandshake size={18} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--color-dourado)' }} />
        <div>
          <strong style={{ display: 'block', marginBottom: '3px' }}>Apoio de Cuidado & Bem-Estar (CFM 2.454/2026 e CDC):</strong>
          As análises estatísticas e orientações apresentadas constituem <strong>triagem preditiva e apoio educativo</strong>, sujeitas a margem probabilística (falsos positivos/negativos), e <strong>NÃO CONSTITUEM DIAGNÓSTICO MÉDICO</strong> nem substituem consultas presenciais e decisões clínicas do seu médico obstetra. Qualquer dúvida ou sintoma deve ser reportado imediatamente à sua equipe de saúde.
        </div>
      </div>
    </div>
  );
}
