import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { Eye, EyeOff, ArrowRight, ShieldCheck, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';
import LegalModal from '../components/LegalModal';

const NOME_REGEX = /^[A-Za-zÀ-ÖØ-öø-ÿ\s'.-]{2,100}$/;

export default function RegisterGestante({ onBackToLogin, onRegisterSuccess }) {
  const { login } = useAuth();
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [aceiteTermos, setAceiteTermos] = useState(false);
  const [consentimentoSaude, setConsentimentoSaude] = useState(false);
  const [recusaIa, setRecusaIa] = useState(false);
  const [modalLegalAberto, setModalLegalAberto] = useState(false);
  const [abaLegalInicial, setAbaLegalInicial] = useState('privacidade');
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro('');

    const nomeTrim = nome.trim();
    if (!NOME_REGEX.test(nomeTrim)) {
      setErro('O nome completo deve conter apenas letras, espaços e hífens, sem números ou símbolos.');
      return;
    }
    if (senha.length < 8) {
      setErro('A senha deve ter no mínimo 8 caracteres.');
      return;
    }
    if (senha.length > 72) {
      setErro('A senha deve ter no máximo 72 caracteres.');
      return;
    }
    if (!aceiteTermos) {
      setErro('É obrigatório ler e concordar com os Termos de Uso e a Política de Privacidade.');
      return;
    }
    if (!consentimentoSaude) {
      setErro('É obrigatório fornecer o consentimento para o tratamento de dados pessoais sensíveis de saúde (Art. 11, I da LGPD).');
      return;
    }

    setCarregando(true);
    try {
      const res = await fetch('/auth/gestante/cadastro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nomeTrim,
          email: email.trim().toLowerCase(),
          senha,
          recusa_ia: recusaIa,
          aceite_termos: aceiteTermos,
          consentimento_dados_saude: consentimentoSaude,
          termos_versao: '1.0-2026'
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao cadastrar gestante.');
      }
      login(data.token, data);
      if (onRegisterSuccess) onRegisterSuccess();
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
        <h1 style={{ fontSize: '1.5rem', marginTop: '8px' }}>Cadastro da Gestante</h1>
        <p className="text-muted">Inicie seu acompanhamento clínico seguro</p>
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
          <label htmlFor="reg-nome">Nome Completo (apenas letras)</label>
          <input
            id="reg-nome"
            type="text"
            className="form-control"
            placeholder="Ex: Maria Clara Santos"
            value={nome}
            maxLength={100}
            onChange={(e) => setNome(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="reg-email">E-mail</label>
          <input
            id="reg-email"
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
          <label htmlFor="reg-senha">Senha (8 a 72 caracteres)</label>
          <div style={{ position: 'relative' }}>
            <input
              id="reg-senha"
              type={mostrarSenha ? 'text' : 'password'}
              className="form-control"
              placeholder="Mínimo 8 caracteres"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              minLength={8}
              maxLength={72}
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

        {/* 1. Consentimento Específico e Destacado de Dados de Saúde (Art. 11, I da LGPD) */}
        <div
          style={{
            backgroundColor: '#F7FAF8',
            border: '1.5px solid #27AE60',
            padding: '12px 14px',
            borderRadius: 'var(--radius-md)',
            marginBottom: '14px'
          }}
        >
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', fontSize: '0.84rem' }}>
            <input
              type="checkbox"
              checked={consentimentoSaude}
              onChange={(e) => setConsentimentoSaude(e.target.checked)}
              required
              style={{ marginTop: '3px', width: '18px', height: '18px', accentColor: '#27AE60' }}
            />
            <span style={{ color: 'var(--color-text-main)', lineHeight: 1.45 }}>
              <strong style={{ color: '#1E7E34' }}>Consentimento de Dados de Saúde (Art. 11, I da LGPD): *</strong>{' '}
              Consinto de forma expressa e destacada com o tratamento dos meus dados pessoais sensíveis de saúde (sinais, exames, histórico obstétrico) para acompanhamento e triagem pré-natal segura.
            </span>
          </label>
        </div>

        {/* 2. Aceite Obrigatório dos Termos de Uso e Política de Privacidade */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid var(--color-border)',
            padding: '12px 14px',
            borderRadius: 'var(--radius-md)',
            marginBottom: '14px'
          }}
        >
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', fontSize: '0.84rem' }}>
            <input
              type="checkbox"
              checked={aceiteTermos}
              onChange={(e) => setAceiteTermos(e.target.checked)}
              required
              style={{ marginTop: '3px', width: '18px', height: '18px', accentColor: 'var(--color-vinho)' }}
            />
            <span style={{ color: 'var(--color-text-main)', lineHeight: 1.45 }}>
              <strong>Concordo com os *</strong>{' '}
              <button
                type="button"
                onClick={() => { setAbaLegalInicial('termos'); setModalLegalAberto(true); }}
                style={{ background: 'transparent', border: 'none', color: 'var(--color-vinho)', fontWeight: 700, padding: 0, textDecoration: 'underline', cursor: 'pointer', fontSize: '0.84rem' }}
              >
                Termos de Uso
              </button>{' '}
              e com a{' '}
              <button
                type="button"
                onClick={() => { setAbaLegalInicial('privacidade'); setModalLegalAberto(true); }}
                style={{ background: 'transparent', border: 'none', color: 'var(--color-vinho)', fontWeight: 700, padding: 0, textDecoration: 'underline', cursor: 'pointer', fontSize: '0.84rem' }}
              >
                Política de Privacidade
              </button>{' '}
              da Nymphia.
            </span>
          </label>
        </div>

        {/* 3. Consentimento e Direito de Recusa de IA (Resolução CFM 2.454/2026) */}
        <div
          style={{
            backgroundColor: 'var(--color-rosa-claro)',
            border: '1px solid var(--color-border)',
            padding: '12px 14px',
            borderRadius: 'var(--radius-md)',
            marginBottom: '14px'
          }}
        >
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', fontSize: '0.84rem' }}>
            <input
              type="checkbox"
              checked={recusaIa}
              onChange={(e) => setRecusaIa(e.target.checked)}
              style={{ marginTop: '3px', width: '18px', height: '18px', accentColor: 'var(--color-rosa)' }}
            />
            <span style={{ lineHeight: 1.45 }}>
              <strong>Direito de Recusa da IA (CFM 2.454/2026):</strong> Desejo utilizar a Nymphia baseando o acompanhamento estritamente em protocolos do Ministério da Saúde, recusando análises por inteligência artificial conversacional.
            </span>
          </label>
        </div>

        {/* Nota acolhedora para gestantes adolescentes */}
        <div style={{ backgroundColor: '#FDF7EE', border: '1px solid var(--color-dourado)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', marginBottom: '18px', fontSize: '0.78rem', color: '#92400E', lineHeight: 1.4 }}>
          <strong>🌸 Acolhimento a Gestantes Adolescentes:</strong> O acompanhamento de saúde sexual e reprodutiva é assegurado com sigilo profissional. A Nymphia não bloqueia seu cadastro e garante socorro emergencial irrestrito.
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px' }}
          disabled={carregando}
        >
          {carregando ? 'Criando Conta...' : 'Criar Minha Conta'}
          <ArrowRight size={18} />
        </button>
      </form>

      <LegalModal
        isOpen={modalLegalAberto}
        onClose={() => setModalLegalAberto(false)}
        initialTab={abaLegalInicial}
      />
    </div>
  );
}
