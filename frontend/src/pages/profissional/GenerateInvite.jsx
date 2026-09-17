import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { QrCode, Copy, Share2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function GenerateInvite({ onBack }) {
  const { authHeaders } = useAuth();
  const [codigo, setCodigo] = useState('');
  const [expiraEm, setExpiraEm] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const [erro, setErro] = useState('');

  const handleGerarCodigo = async () => {
    setCarregando(true);
    setErro('');
    setCopiado(false);
    try {
      const res = await fetch('/vinculo/convite/gerar', {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao gerar código de convite.');
      }
      setCodigo(data.codigo);
      setExpiraEm(data.expira_em);
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  const handleCopiar = () => {
    if (!codigo) return;
    navigator.clipboard.writeText(codigo);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2500);
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar ao Painel" />

      <h2>Gerar Código de Convite</h2>
      <p className="text-muted" style={{ marginBottom: '20px' }}>
        Forneça este código seguro de 8 caracteres à sua paciente para ela conectar o aplicativo dela ao seu painel.
      </p>

      {erro && (
        <div role="alert" style={{ padding: '12px', backgroundColor: '#FDEEE9', color: '#8A2B1A', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
          {erro}
        </div>
      )}

      {/* Regra Clínica Seção 5.5 */}
      <div style={{ backgroundColor: 'var(--color-rosa-claro)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', marginBottom: '20px', fontSize: '0.85rem' }}>
        <strong>Importante:</strong> Gerar o código de convite <strong>NÃO</strong> cria vínculo nenhum de forma unilateral. O vínculo é estabelecido exclusivamente quando a <strong>gestante</strong> ativa o código em sua conta.
      </div>

      <div className="card" style={{ textAlign: 'center', padding: '28px 16px' }}>
        {!codigo ? (
          <div>
            <QrCode size={64} color="var(--color-vinho)" style={{ margin: '0 auto 16px auto', opacity: 0.8 }} />
            <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '20px' }}>
              Clique abaixo para gerar um novo código criptográfico com validade de 7 dias.
            </p>
            <button
              onClick={handleGerarCodigo}
              className="btn btn-primary"
              style={{ minHeight: '48px', padding: '0 24px' }}
              disabled={carregando}
            >
              {carregando ? 'Gerando Código...' : 'Gerar Código de Convite'}
            </button>
          </div>
        ) : (
          <div>
            <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Código para a Paciente:
            </span>

            <div
              style={{
                fontSize: '2.4rem',
                fontWeight: 900,
                letterSpacing: '0.15em',
                color: 'var(--color-vinho)',
                backgroundColor: 'var(--color-rosa-claro)',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                margin: '12px 0 16px 0',
                userSelect: 'all'
              }}
            >
              {codigo}
            </div>

            {/* Representação do QR Code com SVG estilizado */}
            <div style={{ margin: '16px auto', width: '140px', height: '140px', backgroundColor: '#FFFFFF', padding: '10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
              <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
                {/* QR Code pattern decorativo com fidelidade visual */}
                <rect width="100" height="100" fill="#FFFFFF" />
                <rect x="10" y="10" width="25" height="25" fill="#5C1A2A" />
                <rect x="15" y="15" width="15" height="15" fill="#FFFFFF" />
                <rect x="18" y="18" width="9" height="9" fill="#5C1A2A" />

                <rect x="65" y="10" width="25" height="25" fill="#5C1A2A" />
                <rect x="70" y="15" width="15" height="15" fill="#FFFFFF" />
                <rect x="73" y="18" width="9" height="9" fill="#5C1A2A" />

                <rect x="10" y="65" width="25" height="25" fill="#5C1A2A" />
                <rect x="15" y="70" width="15" height="15" fill="#FFFFFF" />
                <rect x="18" y="73" width="9" height="9" fill="#5C1A2A" />

                <rect x="45" y="45" width="10" height="10" fill="#C2185B" />
                <rect x="60" y="60" width="8" height="8" fill="#5C1A2A" />
                <rect x="42" y="15" width="6" height="14" fill="#5C1A2A" />
                <rect x="15" y="45" width="12" height="6" fill="#5C1A2A" />
                <rect x="75" y="75" width="15" height="15" fill="#5C1A2A" />
              </svg>
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '16px' }}>
              Válido até: {new Date(expiraEm).toLocaleDateString('pt-BR')} (ou até o primeiro uso)
            </p>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={handleCopiar}
                className="btn btn-outline"
                style={{ flex: 1 }}
              >
                {copiado ? <CheckCircle2 size={18} color="#27AE60" /> : <Copy size={18} />}
                {copiado ? 'Código Copiado!' : 'Copiar Código'}
              </button>

              <button
                onClick={handleGerarCodigo}
                className="btn btn-primary"
                style={{ flex: 1 }}
              >
                Gerar Outro
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
