import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { Eye, EyeOff, Lock, Mail, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login({ onNavigateRegister, onNavigateRegisterProf, onNavigateRegisterParc }) {
  const { login } = useAuth();
  const [perfil, setPerfil] = useState('gestante'); // gestante | profissional | parceiro
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro('');
    if (!email || !senha) {
      setErro('Por favor, preencha todos os campos.');
      return;
    }

    setCarregando(true);
    let endpoint = '/auth/gestante/login';
    if (perfil === 'profissional') endpoint = '/auth/profissional/login';
    if (perfil === 'parceiro') endpoint = '/auth/parceiro/login';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, senha })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao autenticar.');
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
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '28px', paddingTop: '20px' }}>
        <LotusLogo size={52} color="var(--color-vinho)" className="mx-auto" />
        <h1 style={{ fontSize: '1.75rem', marginTop: '12px', color: 'var(--color-vinho)' }}>Nymphia</h1>
        <p className="header-slogan" style={{ color: 'var(--color-rosa)', fontWeight: 600, marginTop: '2px' }}>
          Cada batimento importa.
        </p>
      </div>

      {/* Seletor de Perfil */}
      <div style={{ display: 'flex', backgroundColor: 'var(--color-rosa-claro)', padding: '4px', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
        <button
          type="button"
          onClick={() => setPerfil('gestante')}
          style={{
            flex: 1,
            backgroundColor: perfil === 'gestante' ? 'var(--color-vinho)' : 'transparent',
            color: perfil === 'gestante' ? '#FFFFFF' : 'var(--color-text-muted)',
            borderRadius: 'var(--radius-sm)',
            minHeight: '38px',
            fontSize: '0.85rem'
          }}
        >
          Gestante
        </button>
        <button
          type="button"
          onClick={() => setPerfil('profissional')}
          style={{
            flex: 1,
            backgroundColor: perfil === 'profissional' ? 'var(--color-vinho)' : 'transparent',
            color: perfil === 'profissional' ? '#FFFFFF' : 'var(--color-text-muted)',
            borderRadius: 'var(--radius-sm)',
            minHeight: '38px',
            fontSize: '0.85rem'
          }}
        >
          Profissional
        </button>
        <button
          type="button"
          onClick={() => setPerfil('parceiro')}
          style={{
            flex: 1,
            backgroundColor: perfil === 'parceiro' ? 'var(--color-vinho)' : 'transparent',
            color: perfil === 'parceiro' ? '#FFFFFF' : 'var(--color-text-muted)',
            borderRadius: 'var(--radius-sm)',
            minHeight: '38px',
            fontSize: '0.85rem'
          }}
        >
          Parceiro
        </button>
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

      {/* Formulário de Login */}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="login-email">E-mail</label>
          <div style={{ position: 'relative' }}>
            <input
              id="login-email"
              type="email"
              className="form-control"
              placeholder="seuemail@exemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="login-senha">Senha</label>
          <div style={{ position: 'relative' }}>
            <input
              id="login-senha"
              type={mostrarSenha ? 'text' : 'password'}
              className="form-control"
              placeholder="••••••••"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              autoComplete="current-password"
              style={{ paddingRight: '44px' }}
            />
            <button
              type="button"
              onClick={() => setMostrarSenha(!mostrarSenha)}
              style={{
                position: 'absolute',
                right: '4px',
                top: '4px',
                background: 'transparent',
                border: 'none',
                minWidth: '38px',
                minHeight: '38px',
                color: 'var(--color-text-muted)'
              }}
              aria-label={mostrarSenha ? 'Ocultar senha' : 'Exibir senha'}
            >
              {mostrarSenha ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px', marginTop: '10px' }}
          disabled={carregando}
        >
          {carregando ? 'Entrando...' : 'Entrar na Plataforma'}
          <ArrowRight size={18} />
        </button>
      </form>

      {/* Links de Criação de Conta */}
      <div style={{ marginTop: '28px', textAlign: 'center', borderTop: '1px solid var(--color-border)', paddingTop: '20px' }}>
        <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
          Ainda não tem conta?
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onNavigateRegister}
          >
            Cadastrar como Gestante
          </button>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1, fontSize: '0.8rem' }}
              onClick={onNavigateRegisterProf}
            >
              Área do Médico/Enfermeiro
            </button>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1, fontSize: '0.8rem' }}
              onClick={onNavigateRegisterParc}
            >
              Cadastro de Parceiro
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
