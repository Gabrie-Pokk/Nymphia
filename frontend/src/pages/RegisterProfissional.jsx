import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { ArrowRight, UploadCloud, CheckCircle, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';
import LegalModal from '../components/LegalModal';

const NOME_REGEX = /^[A-Za-zÀ-ÖØ-öø-ÿ\s'.-]{2,100}$/;
const REGISTRO_REGEX = /^[0-9]{3,10}(-[A-Za-z0-9])?$/;
const UFS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

export default function RegisterProfissional({ onBackToLogin, onRegisterSuccess }) {
  const { login } = useAuth();
  const [etapa, setEtapa] = useState(1);
  const [tokenCriado, setTokenCriado] = useState(null);
  const [profCriado, setProfCriado] = useState(null);

  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [registroTipo, setRegistroTipo] = useState('CRM');
  const [registroNumero, setRegistroNumero] = useState('');
  const [registroUf, setRegistroUf] = useState('SP');
  const [arquivo, setArquivo] = useState(null);
  const [aceiteTermos, setAceiteTermos] = useState(false);
  const [modalLegalAberto, setModalLegalAberto] = useState(false);
  const [abaLegalInicial, setAbaLegalInicial] = useState('termos');

  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [crmStatus, setCrmStatus] = useState(null);
  const [verificandoCrm, setVerificandoCrm] = useState(false);

  const checarCrmOnline = async (num, uf) => {
    const numLimpo = (num !== undefined ? num : registroNumero).replace(/[^0-9]/g, '');
    const ufLimpa = (uf !== undefined ? uf : registroUf).toUpperCase();
    if (registroTipo !== 'CRM' || !numLimpo || numLimpo.length < 3) {
      setCrmStatus(null);
      return;
    }
    setVerificandoCrm(true);
    try {
      const res = await fetch(`/auth/profissional/validar-crm?crm=${numLimpo}&uf=${ufLimpa}`);
      const data = await res.json();
      setCrmStatus(data);
      if (data.valido && data.nome_medico && !nome.trim()) {
        setNome(`Dr(a). ${data.nome_medico}`);
      }
    } catch (e) {
      setCrmStatus({ valido: false, mensagem: 'Falha ao consultar CRM na internet.' });
    } finally {
      setVerificandoCrm(false);
    }
  };


  const handleCadastro = async (e) => {
    e.preventDefault();
    setErro('');

    const nomeTrim = nome.trim();
    if (!NOME_REGEX.test(nomeTrim)) {
      setErro('O nome deve conter apenas letras, espaços e abreviações (ex: Dr. Lucas), sem números.');
      return;
    }

    const regTrim = registroNumero.trim();
    if (!REGISTRO_REGEX.test(regTrim)) {
      setErro('Número de registro inválido. Digite entre 3 e 10 dígitos numéricos.');
      return;
    }

    if (senha.length < 8 || senha.length > 72) {
      setErro('A senha deve ter entre 8 e 72 caracteres.');
      return;
    }

    if (!aceiteTermos) {
      setErro('É obrigatório concordar com os Termos de Uso e a Política de Privacidade para cadastrar uma conta profissional.');
      return;
    }

    setCarregando(true);
    try {
      const res = await fetch('/auth/profissional/cadastro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nomeTrim,
          email: email.trim().toLowerCase(),
          senha,
          registro_tipo: registroTipo,
          registro_numero: regTrim,
          registro_uf: registroUf.toUpperCase(),
          aceite_termos: aceiteTermos,
          termos_versao: '1.0-2026'
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao cadastrar profissional.');
      }
      setTokenCriado(data.token);
      setProfCriado(data);
      setEtapa(2);
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  const handleUploadDocumento = async (e) => {
    e.preventDefault();
    if (!arquivo) {
      login(tokenCriado, profCriado);
      if (onRegisterSuccess) onRegisterSuccess();
      return;
    }

    setCarregando(true);
    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);

      await fetch('/auth/profissional/upload-documento', {
        method: 'POST',
        headers: { Authorization: `Bearer ${tokenCriado}` },
        body: formData
      });

      login(tokenCriado, { ...profCriado, status_verificacao: 'em_analise' });
      if (onRegisterSuccess) onRegisterSuccess();
    } catch (err) {
      login(tokenCriado, profCriado);
      if (onRegisterSuccess) onRegisterSuccess();
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '440px', margin: '0 auto' }}>
      <BackButton onClick={onBackToLogin} label="Voltar para Login" />

      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <LotusLogo size={44} color="var(--color-vinho)" className="mx-auto" />
        <h1 style={{ fontSize: '1.5rem', marginTop: '8px' }}>Cadastro de Obstetra / Enfermeira</h1>
        <p className="text-muted">Acesso clínico e monitoramento em tempo real</p>
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

      {etapa === 1 ? (
        <form onSubmit={handleCadastro}>
          <div className="form-group">
            <label htmlFor="reg-prof-nome">Nome Completo (com titulação)</label>
            <input
              id="reg-prof-nome"
              type="text"
              className="form-control"
              placeholder="Ex: Dra. Helena Silveira"
              value={nome}
              maxLength={100}
              onChange={(e) => setNome(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-prof-email">E-mail Corporativo ou Pessoal</label>
            <input
              id="reg-prof-email"
              type="email"
              className="form-control"
              placeholder="helena@clinica.med.br"
              value={email}
              maxLength={120}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr 1fr', gap: '8px' }}>
            <div className="form-group">
              <label htmlFor="reg-prof-tipo">Conselho</label>
              <select
                id="reg-prof-tipo"
                className="form-control"
                value={registroTipo}
                onChange={(e) => setRegistroTipo(e.target.value)}
              >
                <option value="CRM">CRM</option>
                <option value="COREN">COREN</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="reg-prof-num">Número</label>
              <input
                id="reg-prof-num"
                type="text"
                className="form-control"
                placeholder="123456"
                value={registroNumero}
                maxLength={10}
                onChange={(e) => {
                  const val = e.target.value.replace(/[^0-9]/g, '');
                  setRegistroNumero(val);
                  checarCrmOnline(val, registroUf);
                }}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="reg-prof-uf">UF</label>
              <select
                id="reg-prof-uf"
                className="form-control"
                value={registroUf}
                onChange={(e) => {
                  const val = e.target.value;
                  setRegistroUf(val);
                  checarCrmOnline(registroNumero, val);
                }}
              >
                {UFS_BRASIL.map((uf) => (
                  <option key={uf} value={uf}>{uf}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Feedback de Validação Real de CRM na Internet */}
          {verificandoCrm && (
            <p style={{ fontSize: '0.78rem', color: 'var(--color-vinho)', marginTop: '-8px', marginBottom: '12px' }}>
              🔍 Consultando Conselho Regional de Medicina na internet...
            </p>
          )}
          {crmStatus && !verificandoCrm && (
            <div
              style={{
                marginTop: '-8px',
                marginBottom: '14px',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: crmStatus.valido ? '#E8F8F0' : '#FDEEE9',
                border: crmStatus.valido ? '1px solid #27AE60' : '1px solid #E74C3C',
                color: crmStatus.valido ? '#1E7E34' : '#8A2B1A',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {crmStatus.valido ? (
                <>
                  <CheckCircle size={16} color="#1E7E34" style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Registro Ativo no CRM:</strong> {crmStatus.nome_medico || ''} ({crmStatus.conselho || 'CREMESP'})
                    {crmStatus.especialidade && <div><span style={{ fontSize: '0.74rem', opacity: 0.9 }}>{crmStatus.especialidade}</span></div>}
                  </div>
                </>
              ) : (
                <div>
                  <strong>Não Válido:</strong> {crmStatus.mensagem}
                </div>
              )}
            </div>
          )}


          <div className="form-group">
            <label htmlFor="reg-prof-senha">Senha (8 a 72 caracteres)</label>
            <input
              id="reg-prof-senha"
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

          {/* Consentimento Legal e Termos de Uso (LGPD e CFM) */}
          <div
            style={{
              padding: '12px',
              backgroundColor: '#FAFAFA',
              border: '1px solid #E0E0E0',
              borderRadius: '8px',
              marginBottom: '16px'
            }}
          >
            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                fontSize: '0.85rem',
                color: '#333',
                cursor: 'pointer'
              }}
            >
              <input
                type="checkbox"
                checked={aceiteTermos}
                onChange={(e) => setAceiteTermos(e.target.checked)}
                style={{ marginTop: '3px', cursor: 'pointer' }}
                required
              />
              <span>
                Li e aceito os{' '}
                <button
                  type="button"
                  onClick={() => abrirLegal('termos')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-primary, #5C1A2A)',
                    textDecoration: 'underline',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0
                  }}
                >
                  Termos de Uso
                </button>{' '}
                e a{' '}
                <button
                  type="button"
                  onClick={() => abrirLegal('politica')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-primary, #5C1A2A)',
                    textDecoration: 'underline',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0
                  }}
                >
                  Política de Privacidade
                </button>
                , comprometendo-me a zelar pelo sigilo profissional (CFM/COREN) e proteção de dados de saúde das pacientes (LGPD).
              </span>
            </label>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', minHeight: '48px', marginTop: '12px' }}
            disabled={carregando}
          >
            {carregando ? 'Cadastrando...' : 'Avançar'}
            <ArrowRight size={18} />
          </button>
        </form>
      ) : (
        <div>
          <div
            style={{
              padding: '16px',
              backgroundColor: '#E8F8F0',
              color: '#1E7E34',
              borderRadius: 'var(--radius-md)',
              marginBottom: '16px',
              display: 'flex',
              gap: '10px'
            }}
          >
            <CheckCircle size={24} />
            <div>
              <strong>Cadastro inicial realizado!</strong>
              <p style={{ margin: 0, fontSize: '0.85rem' }}>
                Para liberar a prescrição e acesso total, anexe seu comprovante de registro ou faça isso mais tarde.
              </p>
            </div>
          </div>

          <form onSubmit={handleUploadDocumento}>
            <div className="form-group">
              <label>Comprovante de Registro Profissional (PDF, JPG ou PNG - máx 10MB)</label>
              <input
                type="file"
                accept="application/pdf,image/*"
                className="form-control"
                onChange={(e) => setArquivo(e.target.files[0])}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
              <button
                type="button"
                className="btn btn-outline"
                style={{ flex: 1 }}
                onClick={() => login(tokenCriado, profCriado)}
              >
                Pular por enquanto
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ flex: 1 }}
                disabled={carregando}
              >
                {carregando ? 'Enviando...' : 'Enviar e Entrar'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Modal Institucional de Termos e LGPD */}
      <LegalModal
        isOpen={modalLegalAberto}
        onClose={() => setModalLegalAberto(false)}
        initialTab={abaLegalInicial}
      />
    </div>
  );
}
