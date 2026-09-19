import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { Eye, EyeOff, Lock, Mail, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login({ onNavigateRegister, onNavigateRegisterProf, onNavigateRegisterParc }) {
  const { login } = useAuth();
  const [perfil, setPerfil] = useState('gestante'); // gestante | profissional | parceiro
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

  const preencherDemo = async (tipo) => {
    setPerfil(tipo);
    let demoEmail = 'gestante@nymphia.com.br';
    if (tipo === 'profissional') demoEmail = 'medico@nymphia.com.br';
    if (tipo === 'parceiro') demoEmail = 'parceiro@nymphia.com.br';
    const demoSenha = 'senhaMaternidade123';

    setEmail(demoEmail);
    setSenha(demoSenha);
    setCarregando(true);
    setErro('');

    let endpoint = '/auth/gestante/login';
    if (tipo === 'profissional') endpoint = '/auth/profissional/login';
    if (tipo === 'parceiro') endpoint = '/auth/parceiro/login';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: demoEmail, senha: demoSenha })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao autenticar na conta demo.');
      }
      login(data.token, data);
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

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
      <div style={{ textAlign: 'center', marginBottom: '22px', paddingTop: '16px' }}>
        <LotusLogo size={52} color="var(--color-vinho)" className="mx-auto" />
        <h1 style={{ fontSize: '1.75rem', marginTop: '12px', color: 'var(--color-vinho)' }}>Nymphia</h1>
        <p className="header-slogan" style={{ color: 'var(--color-rosa)', fontWeight: 600, marginTop: '2px' }}>
          Cada batimento importa.
        </p>
      </div>

      {/* SEÇÃO DE ACESSO RÁPIDO PARA TESTADORES / DEMO (1 CLIQUE) */}
      <div
        className="card"
        style={{
          backgroundColor: '#FFF8F9',
          border: '1.5px solid var(--color-rosa)',
          borderRadius: 'var(--radius-md)',
          padding: '16px',
          marginBottom: '22px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <Sparkles size={18} color="var(--color-rosa)" />
          <h2 style={{ fontSize: '0.98rem', margin: 0, color: 'var(--color-vinho)' }}>
            Acesso Rápido para Avaliação
          </h2>
          <span className="badge-gold" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>1 Clique</span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: '12px', lineHeight: 1.4 }}>
          <strong>Você só precisa testar 1 perfil!</strong> Escolha qual área deseja experimentar e clique abaixo para entrar instantaneamente:
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            type="button"
            onClick={() => preencherDemo('gestante')}
            className="btn"
            disabled={carregando}
            style={{
              backgroundColor: '#FFFFFF',
              border: '1.5px solid var(--color-rosa)',
              color: 'var(--color-vinho)',
              justifyContent: 'space-between',
              padding: '10px 14px',
              fontSize: '0.85rem',
              fontWeight: 600
            }}
          >
            <span>🌸 1. Entrar como Gestante (Mariana)</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--color-rosa)', fontWeight: 700 }}>Testar App</span>
          </button>

          <button
            type="button"
            onClick={() => preencherDemo('profissional')}
            className="btn"
            disabled={carregando}
            style={{
              backgroundColor: '#FFFFFF',
              border: '1.5px solid var(--color-vinho)',
              color: 'var(--color-vinho)',
              justifyContent: 'space-between',
              padding: '10px 14px',
              fontSize: '0.85rem',
              fontWeight: 600
            }}
          >
            <span>🩺 2. Entrar como Médico (Dr. Carlos)</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--color-vinho)', fontWeight: 700 }}>Painel Clínico</span>
          </button>

          <button
            type="button"
            onClick={() => preencherDemo('parceiro')}
            className="btn"
            disabled={carregando}
            style={{
              backgroundColor: '#FFFFFF',
              border: '1.5px solid #27AE60',
              color: '#1E7E34',
              justifyContent: 'space-between',
              padding: '10px 14px',
              fontSize: '0.85rem',
              fontWeight: 600
            }}
          >
            <span>🤝 3. Entrar como Parceiro (Lucas)</span>
            <span style={{ fontSize: '0.72rem', color: '#27AE60', fontWeight: 700 }}>Apoio & Quiz</span>
          </button>
        </div>
      </div>

      {/* Seletor de Perfil Manual */}
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
