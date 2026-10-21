import React, { useEffect, useState } from 'react';
import { apiFetch } from '../utils/api';
import PerguntasRiscoGestacional, { daApi, paraApi } from './PerguntasRiscoGestacional';

// Para quem fez o cadastro clínico antes de 15/10/2026: completa as perguntas
// novas (número de bebês, início do pré-natal, estado, saúde antes da gravidez).
export default function CompletarCadastroClinico({ aberto, onFechar, onSalvo }) {
  const [valores, setValores] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    if (!aberto) return;
    setErro('');
    apiFetch('/perfil-clinico')
      .then((perfil) => setValores(daApi(perfil)))
      .catch((e) => setErro(e.message || 'Não foi possível abrir seu cadastro clínico.'));
  }, [aberto]);

  if (!aberto) return null;

  const salvar = async (e) => {
    e.preventDefault();
    setSalvando(true);
    setErro('');
    try {
      await apiFetch('/perfil-clinico', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(paraApi(valores))
      });
      onSalvo?.();
      onFechar();
    } catch (err) {
      setErro(err.message || 'Não foi possível salvar.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '16px' }}
    >
      <div className="card" style={{ maxWidth: '440px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
        <h3 style={{ margin: '0 0 6px 0', color: 'var(--color-vinho)' }}>Completar cadastro clínico</h3>
        <p className="text-muted" style={{ fontSize: '0.82rem', margin: '0 0 12px 0' }}>
          Respostas que deixam as estimativas mais precisas. Pode deixar em "não sei".
        </p>
        {erro && <p style={{ color: '#922B21', fontSize: '0.84rem' }}>{erro}</p>}
        {valores && (
          <form onSubmit={salvar}>
            <PerguntasRiscoGestacional
              valores={valores}
              onChange={(campo, valor) => setValores((v) => ({ ...v, [campo]: valor }))}
            />
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '8px' }}>
              <button type="button" className="btn btn-secondary" onClick={onFechar}>Cancelar</button>
              <button type="submit" className="btn btn-primary" disabled={salvando}>
                {salvando ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
