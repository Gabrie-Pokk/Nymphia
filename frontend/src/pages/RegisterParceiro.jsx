import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';

export default function RegisterParceiro({ onBackToLogin }) {
  const { login } = useAuth();
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro('');

    if (nome.trim().length < 3) {
      setErro('O nome deve ter no mínimo 3 caracteres.');
      return;
    }
    if (senha.length < 8) {
      setErro('A senha deve ter no mínimo 8 caracteres.');
      return;
    }

    setCarregando(true);
    try {
      const res = await fetch('/auth/parceiro/cadastro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nome.trim(),
          email: email.trim().toLowerCase(),
          senha
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao cadastrar parceiro.');
      }
      login(data.token, data);
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '440px', margin: '0 auto' }}>
      <BackButton onClick={onBackToLogin} label="Voltar para Login" />

      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <LotusLogo size={44} color="var(--color-vinho)" className="mx-auto" />
        <h1 style={{ fontSize: '1.5rem', marginTop: '8px' }}>Cadastro do Parceiro</h1>
        <p className="text-muted">Apoio contínuo e alerta de emergência conectado</p>
      </div>

      {erro && (
        <div
          role="alert"
          style={{
            padding: '12px',
            backgroundColor: '#FDEEE9',
            color: '#8A2B1A',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            marginBottom: '16px',
            borderLeft: '4px solid #D9534F'
          }}
        >
          {erro}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="parc-nome">Nome Completo</label>
          <input
            id="parc-nome"
            type="text"
            className="form-control"
            placeholder="Seu nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="parc-email">E-mail</label>
          <input
            id="parc-email"
            type="email"
            className="form-control"
            placeholder="seuemail@exemplo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="parc-senha">Senha (Mínimo 8 caracteres)</label>
          <input
            id="parc-senha"
            type="password"
            className="form-control"
            placeholder="Mínimo 8 caracteres"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            minLength={8}
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px', marginTop: '10px' }}
          disabled={carregando}
        >
          {carregando ? 'Cadastrando...' : 'Criar Conta de Parceiro'}
          <ArrowRight size={18} />
        </button>
      </form>
    </div>
  );
}
