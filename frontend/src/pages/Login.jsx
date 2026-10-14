import React, { useState } from 'react';
import LotusLogo, { NymphiaBrandName } from '../components/LotusLogo';
import { Eye, EyeOff, Lock, Mail, ArrowRight, CheckCircle, AlertTriangle, ShieldCheck, X, KeyRound, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import LegalModal from '../components/LegalModal';

import { apiFetch } from '../utils/api';

const UFS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

export default function Login({ onLoginSuccess, onNavigateRegister, onNavigateRegisterProf, onNavigateRegisterParc }) {
  const { login, authMessage, clearAuthMessage } = useAuth();
  const [perfil, setPerfil] = useState('gestante'); // gestante | profissional | parceiro
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [crm, setCrm] = useState('');
  const [crmUf, setCrmUf] = useState('SP');
  const [crmStatus, setCrmStatus] = useState(null);
  const [verificandoCrm, setVerificandoCrm] = useState(false);
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [modalLegalAberto, setModalLegalAberto] = useState(false);
  const [abaLegalInicial, setAbaLegalInicial] = useState('privacidade');

  // Estados de Recuperação de Senha ("Esqueci minha senha")
  const [modalEsqueciAberto, setModalEsqueciAberto] = useState(false);
  const [etapaEsqueci, setEtapaEsqueci] = useState(1); // 1 = solicitar email, 2 = redefinir
  const [emailRecuperacao, setEmailRecuperacao] = useState('');
  const [tokenRecuperacao, setTokenRecuperacao] = useState('');
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmarNovaSenha, setConfirmarNovaSenha] = useState('');
  const [carregandoRecuperacao, setCarregandoRecuperacao] = useState(false);
  const [erroRecuperacao, setErroRecuperacao] = useState('');
  const [sucessoRecuperacao, setSucessoRecuperacao] = useState('');

  const verificarCrmAoDigitar = async (numDigitado, ufDigitada) => {
    const numCrm = (numDigitado !== undefined ? numDigitado : crm).trim().replace(/[^0-9]/g, '');
    const estadoUf = (ufDigitada !== undefined ? ufDigitada : crmUf).trim().toUpperCase();
    if (!numCrm || numCrm.length < 3) {
      setCrmStatus(null);
      return;
    }

    setVerificandoCrm(true);
    try {
      const res = await apiFetch(`/auth/profissional/validar-crm?crm=${numCrm}&uf=${estadoUf}`, { skipAuth: true });
      setCrmStatus(res);
    } catch (err) {
      setCrmStatus({ valido: false, mensagem: err.message || 'Falha ao consultar CRM no CFM.' });
    } finally {
      setVerificandoCrm(false);
    }
  };

  const handleSolicitarRecuperacao = async (e) => {
    e.preventDefault();
    setErroRecuperacao('');
    setSucessoRecuperacao('');
    if (!emailRecuperacao || !emailRecuperacao.includes('@')) {
      setErroRecuperacao('Por favor, informe um e-mail válido.');
      return;
    }
    setCarregandoRecuperacao(true);
    try {
      const res = await apiFetch('/auth/esqueci-senha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailRecuperacao.trim(), perfil }),
        skipAuth: true
      });
      if (res && res.reset_token) {
        setTokenRecuperacao(res.reset_token);
        setSucessoRecuperacao('Token de redefinição validado. Digite sua nova senha abaixo:');
        setEtapaEsqueci(2);
      } else {
        setSucessoRecuperacao(res.mensagem || 'Orientações enviadas. Verifique o código recebido.');
        setEtapaEsqueci(2);
      }
    } catch (err) {
      setErroRecuperacao(err.message || 'Falha ao solicitar recuperação de senha.');
    } finally {
      setCarregandoRecuperacao(false);
    }
  };

  const handleRedefinirSenha = async (e) => {
    e.preventDefault();
    setErroRecuperacao('');
    setSucessoRecuperacao('');
    if (!tokenRecuperacao) {
      setErroRecuperacao('Informe o token de redefinição.');
      return;
    }
    if (novaSenha.length < 8) {
      setErroRecuperacao('A nova senha deve possuir pelo menos 8 caracteres.');
      return;
    }
    if (novaSenha !== confirmarNovaSenha) {
      setErroRecuperacao('As senhas digitadas não conferem.');
      return;
    }
    setCarregandoRecuperacao(true);
    try {
      const res = await apiFetch('/auth/redefinir-senha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: tokenRecuperacao.trim(), nova_senha: novaSenha }),
        skipAuth: true
      });
      setSucessoRecuperacao(res.mensagem || 'Senha redefinida com sucesso!');
      setEmail(emailRecuperacao);
      setSenha('');
      setTimeout(() => {
        setModalEsqueciAberto(false);
        setEtapaEsqueci(1);
        setSucessoRecuperacao('');
        setNovaSenha('');
        setConfirmarNovaSenha('');
        setTokenRecuperacao('');
      }, 2000);
    } catch (err) {
      setErroRecuperacao(err.message || 'Falha ao salvar a nova senha.');
    } finally {
      setCarregandoRecuperacao(false);
    }
  };


  const handleSubmit = async (e) => {
    e.preventDefault();
    clearAuthMessage && clearAuthMessage();
    setErro('');

    if (perfil === 'profissional') {
      const crmLimpo = crm.trim().replace(/[^0-9]/g, '');
      if (!crmLimpo || crmLimpo.length < 3) {
        setErro('Por favor, informe o número do seu CRM com ao menos 3 dígitos para validação profissional.');
        return;
      }
    }

    if (!email || !senha) {
      setErro('Por favor, preencha todos os campos.');
      return;
    }

    setCarregando(true);
    const emailLimpo = email.trim().toLowerCase();

    try {
      const payload = {
        email: emailLimpo,
        senha,
        perfil
      };
      if (perfil === 'profissional') {
        payload.crm = crm.trim().replace(/[^0-9]/g, '');
        payload.crm_uf = crmUf.trim().toUpperCase();
      }

      const data = await apiFetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        skipAuth: true
      });

      if (!data || !data.token) {
        throw new Error('Resposta de autenticação inválida.');
      }

      login(data.token, data);
      if (onLoginSuccess) onLoginSuccess();
    } catch (err) {
      if (err.status === 401) {
        setErro(err.message || 'E-mail, CRM ou senha incorretos.');
      } else if (err.status === 400 || err.status === 403 || err.status === 422) {
        setErro(err.message || 'Registro profissional não validado ou inativo no CRM.');
      } else if (err.isTimeout || err.isNetworkError || err.status >= 500) {
        setErro('O servidor seguro da Nymphia está inicializando ou com instabilidade momentânea. Aguarde alguns instantes e tente novamente.');
      } else {
        setErro(err.message || 'Falha ao entrar na plataforma.');
      }
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '440px', margin: '0 auto' }}>
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '22px', paddingTop: '16px' }}>
        <LotusLogo size={68} className="mx-auto" />
        <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'center' }}>
          <NymphiaBrandName height={34} />
        </div>
        <p className="header-slogan" style={{ color: 'var(--color-rosa)', fontWeight: 600, marginTop: '4px' }}>
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

      {authMessage && (
        <div
          role="alert"
          style={{
            padding: '12px 14px',
            backgroundColor: '#FFF9E6',
            color: '#7A5F1C',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            marginBottom: '16px',
            borderLeft: '4px solid var(--color-dourado)',
            lineHeight: 1.4
          }}
        >
          🔒 {authMessage}
        </div>
      )}

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
        <div style={{ marginBottom: '14px', fontSize: '0.84rem', color: 'var(--color-vinho)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>Acessando como:</span>
          <span className="badge-rosa" style={{ fontSize: '0.78rem' }}>
            {perfil === 'parceiro' ? '🤝 Parceiro(a) / Rede de Apoio' : perfil === 'profissional' ? '🩺 Profissional de Saúde' : '🌸 Gestante'}
          </span>
        </div>

        {/* Bloco de CRM e UF exclusivo para Médico / Profissional de Saúde */}
        {perfil === 'profissional' && (
          <div
            style={{
              marginBottom: '16px',
              padding: '12px 14px',
              backgroundColor: '#FDF0F2',
              borderRadius: 'var(--radius-sm)',
              border: '1.5px solid var(--color-vinho)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label
                htmlFor="login-crm"
                style={{
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: 'var(--color-vinho)',
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <ShieldCheck size={16} color="var(--color-vinho)" />
                Registro Profissional (CRM)
              </label>
              <span className="badge-gold" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>Checagem CFM</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 90px', gap: '8px' }}>
              <div>
                <input
                  id="login-crm"
                  type="text"
                  className="form-control"
                  placeholder="Número do CRM (ex: 123456)"
                  value={crm}
                  onChange={(e) => {
                    const val = e.target.value.replace(/[^0-9-]/g, '');
                    setCrm(val);
                    if (crmStatus) setCrmStatus(null);
                  }}
                  onBlur={() => verificarCrmAoDigitar()}
                  required={perfil === 'profissional'}
                  style={{ fontWeight: 600 }}
                />
              </div>
              <div>
                <select
                  id="login-crm-uf"
                  className="form-control"
                  value={crmUf}
                  onChange={(e) => {
                    const novaUf = e.target.value;
                    setCrmUf(novaUf);
                    if (crm && crm.length >= 3) {
                      verificarCrmAoDigitar(crm, novaUf);
                    }
                  }}
                  style={{ fontWeight: 600 }}
                >
                  {UFS_BRASIL.map((uf) => (
                    <option key={uf} value={uf}>{uf}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Status de Verificação do CRM em Tempo Real */}
            {verificandoCrm && (
              <div style={{ fontSize: '0.75rem', color: 'var(--color-vinho)', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-rosa)' }} />
                Consultando situação cadastral do CRM junto ao CFM...
              </div>
            )}

            {crmStatus && (
              <div
                style={{
                  fontSize: '0.78rem',
                  marginTop: '8px',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: crmStatus.valido ? '#E8F5E9' : '#FFEBEE',
                  color: crmStatus.valido ? '#2E7D32' : '#C62828',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '6px',
                  lineHeight: 1.3
                }}
              >
                {crmStatus.valido ? (
                  <>
                    <CheckCircle size={16} color="#2E7D32" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <strong>CRM {crmStatus.crm}/{crmStatus.uf} Válido & Ativo</strong>
                      <div style={{ fontSize: '0.72rem' }}>{crmStatus.mensagem}</div>
                    </div>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={16} color="#C62828" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <strong>CRM Não Homologado ou Inativo</strong>
                      <div style={{ fontSize: '0.72rem' }}>{crmStatus.mensagem}</div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="login-email">
            {perfil === 'parceiro' ? 'E-mail do(a) Parceiro(a)' : perfil === 'profissional' ? 'E-mail Profissional (Médico / Enfermeira)' : 'E-mail da Gestante'}
          </label>
          <div style={{ position: 'relative' }}>
            <input
              id="login-email"
              type="email"
              className="form-control"
              placeholder={perfil === 'parceiro' ? 'parceiro@exemplo.com' : perfil === 'profissional' ? 'medico@clinica.com' : 'gestante@exemplo.com'}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="login-senha">Senha de Acesso</label>
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
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
            <button
              type="button"
              onClick={() => {
                setEmailRecuperacao(email);
                setErroRecuperacao('');
                setSucessoRecuperacao('');
                setEtapaEsqueci(1);
                setModalEsqueciAberto(true);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--color-vinho)',
                fontSize: '0.82rem',
                cursor: 'pointer',
                fontWeight: 600,
                textDecoration: 'underline',
                padding: '4px 0'
              }}
            >
              Esqueci minha senha
            </button>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px', marginTop: '10px' }}
          disabled={carregando}
        >
          {carregando
            ? 'Entrando...'
            : perfil === 'parceiro'
            ? 'Entrar como Parceiro(a)'
            : perfil === 'profissional'
            ? 'Entrar como Profissional'
            : 'Entrar como Gestante'}
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

        {/* Rodapé Institucional & Governança LGPD */}
        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--color-border)', fontSize: '0.76rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '6px' }}>
            <button
              type="button"
              onClick={() => { setAbaLegalInicial('privacidade'); setModalLegalAberto(true); }}
              style={{ background: 'transparent', border: 'none', color: 'var(--color-vinho)', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline', fontSize: '0.78rem' }}
            >
              Política de Privacidade (LGPD)
            </button>
            <span>•</span>
            <button
              type="button"
              onClick={() => { setAbaLegalInicial('termos'); setModalLegalAberto(true); }}
              style={{ background: 'transparent', border: 'none', color: 'var(--color-vinho)', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline', fontSize: '0.78rem' }}
            >
              Termos de Uso
            </button>
          </div>
          <div>
            Encarregado de Privacidade (DPO): <a href="mailto:privacidade@nymphia.com.br" style={{ color: 'var(--color-rosa)', fontWeight: 600 }}>privacidade@nymphia.com.br</a>
          </div>
          <div style={{ marginTop: '2px', opacity: 0.85 }}>
            Conforme Leis 13.709/2018 (LGPD), Resoluções CFM 2.454/2026 e CFM 1.821/2007.
          </div>
        </div>
      </div>

      {/* Modal de Recuperação de Senha */}
      {modalEsqueciAberto && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100,
            padding: '16px'
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setModalEsqueciAberto(false); }}
        >
          <div
            className="card"
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '420px',
              width: '100%',
              padding: '24px',
              position: 'relative',
              boxShadow: 'var(--shadow-lg)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--color-rosa-claro)',
                    color: 'var(--color-vinho)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <KeyRound size={20} />
                </div>
                <h2 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--color-vinho)' }}>
                  Recuperar Senha
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setModalEsqueciAberto(false)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
                aria-label="Fechar modal"
              >
                <X size={20} />
              </button>
            </div>

            {erroRecuperacao && (
              <div
                role="alert"
                style={{
                  padding: '10px 12px',
                  backgroundColor: '#FDEEE9',
                  color: '#8A2B1A',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.82rem',
                  marginBottom: '14px',
                  borderLeft: '4px solid #D9534F'
                }}
              >
                {erroRecuperacao}
              </div>
            )}

            {sucessoRecuperacao && (
              <div
                role="status"
                style={{
                  padding: '10px 12px',
                  backgroundColor: '#E8F5E9',
                  color: '#2E7D32',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.82rem',
                  marginBottom: '14px',
                  borderLeft: '4px solid #2E7D32'
                }}
              >
                {sucessoRecuperacao}
              </div>
            )}

            {etapaEsqueci === 1 ? (
              <form onSubmit={handleSolicitarRecuperacao}>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', lineHeight: 1.5, marginBottom: '16px' }}>
                  Digite o e-mail associado à sua conta. Geraremos um token temporário seguro para você redefinir sua senha.
                </p>

                <div className="form-group" style={{ marginBottom: '16px' }}>
                  <label htmlFor="recupera-email" style={{ fontSize: '0.82rem', fontWeight: 600 }}>E-mail da Conta</label>
                  <input
                    id="recupera-email"
                    type="email"
                    className="form-control"
                    placeholder="seu.email@exemplo.com"
                    value={emailRecuperacao}
                    onChange={(e) => setEmailRecuperacao(e.target.value)}
                    required
                    autoFocus
                  />
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setModalEsqueciAberto(false)}
                    className="btn btn-outline"
                    style={{ flex: 1, minHeight: '42px', fontSize: '0.85rem' }}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={carregandoRecuperacao}
                    style={{ flex: 1.5, minHeight: '42px', fontSize: '0.85rem' }}
                  >
                    {carregandoRecuperacao ? 'Processando...' : 'Avançar'}
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleRedefinirSenha}>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
                  Defina a sua nova senha de acesso:
                </p>

                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label htmlFor="recupera-token" style={{ fontSize: '0.82rem', fontWeight: 600 }}>Código / Token de Validação</label>
                  <input
                    id="recupera-token"
                    type="text"
                    className="form-control"
                    placeholder="Cole ou confirme o token recebido"
                    value={tokenRecuperacao}
                    onChange={(e) => setTokenRecuperacao(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label htmlFor="recupera-nova-senha" style={{ fontSize: '0.82rem', fontWeight: 600 }}>Nova Senha (mínimo 8 caracteres)</label>
                  <input
                    id="recupera-nova-senha"
                    type="password"
                    className="form-control"
                    placeholder="••••••••"
                    value={novaSenha}
                    onChange={(e) => setNovaSenha(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>

                <div className="form-group" style={{ marginBottom: '18px' }}>
                  <label htmlFor="recupera-confirma-senha" style={{ fontSize: '0.82rem', fontWeight: 600 }}>Confirmar Nova Senha</label>
                  <input
                    id="recupera-confirma-senha"
                    type="password"
                    className="form-control"
                    placeholder="••••••••"
                    value={confirmarNovaSenha}
                    onChange={(e) => setConfirmarNovaSenha(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => { setEtapaEsqueci(1); setErroRecuperacao(''); }}
                    className="btn btn-outline"
                    style={{ flex: 1, minHeight: '42px', fontSize: '0.85rem' }}
                  >
                    Voltar
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={carregandoRecuperacao}
                    style={{ flex: 1.5, minHeight: '42px', fontSize: '0.85rem' }}
                  >
                    {carregandoRecuperacao ? 'Salvando...' : 'Salvar Nova Senha'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      <LegalModal
        isOpen={modalLegalAberto}
        onClose={() => setModalLegalAberto(false)}
        initialTab={abaLegalInicial}
      />
    </div>
  );
}
