import React from 'react';
import { HeartHandshake } from 'lucide-react';

export default function TriageDisclaimer() {
  return (
    <div className="triage-disclaimer" role="note" aria-label="Aviso sobre apoio de inteligência artificial">
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <HeartHandshake size={18} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--color-dourado)' }} />
        <div>
          <strong style={{ display: 'block', marginBottom: '3px' }}>Apoio de Cuidado & Bem-Estar (CFM 2.454/2026):</strong>
          As orientações apresentadas constituem <strong>apoio educativo e preventivo para seu bem-estar</strong> e <strong>NÃO substituem as consultas e condutas do seu médico obstetra</strong>. Qualquer dúvida ou sensação diferente deve ser compartilhada com sua equipe de saúde.
        </div>
      </div>
    </div>
  );
}
