import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';

const NOME_REGEX = /^[A-Za-zÀ-ÖØ-öø-ÿ\s'.-]{2,100}$/;

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

    const nomeTrim = nome.trim();
    if (!NOME_REGEX.test(nomeTrim)) {
      setErro('O nome completo deve conter apenas letras, espaços e hífens (não são permitidos números).');
      return;
    }
    if (senha.length < 8 || senha.length > 72) {
      setErro('A senha deve ter entre 8 e 72 caracteres.');
      return;
    }

    setCarregando(true);
    try {
      const res = await fetch('/auth/parceiro/cadastro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nomeTrim,
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
        <h1 style={{ fontSize: '1.5rem', marginTop: '8px' }}>Cadastro do Parceiro / Rede de Apoio</h1>
        <p className="text-muted">Apoio logístico, marcos gestacionais e socorro rápido</p>
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
          <label htmlFor="reg-parc-nome">Nome Completo (apenas letras)</label>
          <input
            id="reg-parc-nome"
            type="text"
            className="form-control"
            placeholder="Ex: Carlos Eduardo Lima"
            value={nome}
            maxLength={100}
            onChange={(e) => setNome(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="reg-parc-email">E-mail</label>
          <input
            id="reg-parc-email"
            type="email"
            className="form-control"
            placeholder="seuemail@exemplo.com"
            value={email}
            maxLength={120}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="reg-parc-senha">Senha (8 a 72 caracteres)</label>
          <input
            id="reg-parc-senha"
            type="password"
            className="form-control"
            placeholder="Mínimo 8 caracteres"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            minLength={8}
            maxLength={72}
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px', marginTop: '12px' }}
          disabled={carregando}
        >
          {carregando ? 'Criando Conta...' : 'Cadastrar e Conectar'}
          <ArrowRight size={18} />
        </button>
      </form>
    </div>
  );
}
