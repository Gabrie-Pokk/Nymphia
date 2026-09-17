import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { Link, ShieldCheck, UserCheck, Trash2, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function VinculoMedico({ onBack }) {
  const { authHeaders } = useAuth();
  const [codigoConvite, setCodigoConvite] = useState('');
  const [profissionais, setProfissionais] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState('');

  const carregarProfissionais = async () => {
    try {
      const res = await fetch('/vinculo/meus-profissionais', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setProfissionais(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    carregarProfissionais();
  }, []);

  const handleUsarCodigo = async (e) => {
    e.preventDefault();
    setErro('');
    setSucesso('');

    const codLimpo = codigoConvite.trim().toUpperCase();
    if (!codLimpo) {
      setErro('Informe o código de 8 caracteres fornecido pelo seu médico.');
      return;
    }

    setCarregando(true);
    try {
      const res = await fetch('/vinculo/convite/usar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ codigo: codLimpo })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Código inválido ou já utilizado.');
      }

      setSucesso(`Vínculo ativo com Dr(a). ${data.profissional_nome || 'Profissional'} estabelecido com sucesso!`);
      setCodigoConvite('');
      carregarProfissionais();
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  const handleRevogar = async (vinculoId) => {
    if (!window.confirm('Tem certeza de que deseja revogar o acesso deste profissional? Ele deixará de ver seus dados imediatamente.')) {
      return;
    }

    try {
      const res = await fetch(`/vinculo/${vinculoId}/revogar`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (res.ok) {
        setSucesso('Vínculo revogado imediatamente com sucesso.');
        carregarProfissionais();
      }
    } catch (err) {}
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <h2>Conectar com Profissional de Saúde</h2>
      <p className="text-muted" style={{ marginBottom: '20px' }}>
        Conecte seu pré-natal ao médico obstetra ou enfermeiro de sua confiança através do código gerado por ele.
      </p>

      {sucesso && (
        <div role="status" style={{ padding: '12px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-sm)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} /> {sucesso}
        </div>
      )}

      {erro && (
        <div role="alert" style={{ padding: '12px', backgroundColor: '#FDEEE9', color: '#8A2B1A', borderRadius: 'var(--radius-sm)', marginBottom: '16px', borderLeft: '4px solid #D9534F' }}>
          {erro}
        </div>
      )}

      {/* Formulário de Resgate de Código */}
      <form onSubmit={handleUsarCodigo} className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Digitar Código de Convite</h3>
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '16px' }}>
          Solicite o código de 8 dígitos ao seu médico durante a consulta presencial ou remota.
        </p>

        <div className="form-group">
          <label htmlFor="codigo-input">Código de Convite (8 dígitos)</label>
          <input
            id="codigo-input"
            type="text"
            className="form-control"
            placeholder="Ex: ABC12345"
            maxLength={8}
            value={codigoConvite}
            onChange={(e) => setCodigoConvite(e.target.value.toUpperCase())}
            style={{ fontSize: '1.2rem', letterSpacing: '0.15em', fontWeight: 700, textAlign: 'center' }}
            required
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px' }}
          disabled={carregando}
        >
          {carregando ? 'Conectando...' : 'Ativar Vínculo com Médico'}
          <ArrowRight size={18} />
        </button>
      </form>

      {/* Lista de Médicos Conectados */}
      <h3 style={{ marginTop: '24px', marginBottom: '12px' }}>Profissionais Vinculados</h3>
      {profissionais.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '24px' }}>
          <p className="text-muted">Nenhum profissional vinculado no momento.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {profissionais.map((p) => (
            <div
              key={p.id}
              className="card"
              style={{
                margin: 0,
                padding: '14px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--color-rosa-claro)',
                    color: 'var(--color-vinho)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <UserCheck size={22} />
                </div>
                <div>
                  <h4 style={{ margin: 0, fontSize: '0.98rem' }}>{p.profissional_nome || 'Dr(a). Médico'}</h4>
                  <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                    Conectado em: {new Date(p.criado_em).toLocaleDateString('pt-BR')} • Status: Ativo
                  </span>
                </div>
              </div>

              <button
                onClick={() => handleRevogar(p.id)}
                className="btn btn-outline"
                style={{
                  minHeight: '36px',
                  padding: '6px 12px',
                  fontSize: '0.8rem',
                  color: 'var(--color-vermelho)',
                  borderColor: 'var(--color-border)'
                }}
                title="Revogar acesso do profissional"
              >
                <Trash2 size={14} /> Revogar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
