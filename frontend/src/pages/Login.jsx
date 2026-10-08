import React, { useState } from 'react';
import LotusLogo, { NymphiaBrandName } from '../components/LotusLogo';
import { Eye, EyeOff, Lock, Mail, ArrowRight, Sparkles, CheckCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

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

  const preencherDemo = async (tipo) => {
    setPerfil(tipo);
    clearAuthMessage && clearAuthMessage();
    let demoEmail = 'gestante@nymphia.com.br';
    let demoCrm = '';
    let demoUf = 'SP';

    if (tipo === 'profissional') {
      demoEmail = 'medico@nymphia.com.br';
      demoCrm = '123456';
      demoUf = 'SP';
      setCrm('123456');
      setCrmUf('SP');
      setCrmStatus({
        valido: true,
        crm: '123456',
        uf: 'SP',
        situacao: 'ATIVO',
        mensagem: 'Dr. Carlos Silva • CRM Ativo e Regular no CREMESP'
      });
    } else {
      setCrm('');
      setCrmStatus(null);
    }

    if (tipo === 'parceiro') demoEmail = 'parceiro@nymphia.com.br';
    const demoSenha = 'senhaMaternidade123';

    setEmail(demoEmail);
    setSenha(demoSenha);
    setCarregando(true);
    setErro('');

    try {
      const payload = { email: demoEmail, senha: demoSenha, perfil: tipo };
      if (tipo === 'profissional') {
        payload.crm = demoCrm;
        payload.crm_uf = demoUf;
      }

      const data = await apiFetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        skipAuth: true
      });

      if (data && data.token) {
        login(data.token, data);
        if (onLoginSuccess) onLoginSuccess();
      } else {
        throw new Error('Falha ao autenticar na conta demo.');
      }
    } catch (err) {
      if (err.isTimeout || err.isNetworkError || err.status >= 500) {
        setErro('O servidor da Nymphia está inicializando na nuvem. Aguarde cerca de 20 a 30 segundos e toque novamente no perfil desejado.');
      } else {
        setErro(err.message || 'Falha ao autenticar na conta de teste.');
      }
    } finally {
      setCarregando(false);
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
      </div>
    </div>
  );
}
