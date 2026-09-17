import React from 'react';
import { Info } from 'lucide-react';

export default function TriageDisclaimer() {
  return (
    <div className="triage-disclaimer" role="note" aria-label="Aviso legal sobre triagem de inteligência artificial">
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <Info size={18} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--color-dourado)' }} />
        <div>
          <strong style={{ display: 'block', marginBottom: '3px' }}>Aviso Clínico e Regulatório (CFM 2.454/2026):</strong>
          As estimativas de risco e análises apresentadas constituem <strong>triagem estatística de apoio</strong> e <strong>NÃO substituem diagnóstico médico</strong>. Os modelos estão sujeitos a falsos alarmes e imprecisões biológicas. Qualquer sintoma deve ser avaliado presencialmente pelo seu obstetra.
        </div>
      </div>
    </div>
  );
}
