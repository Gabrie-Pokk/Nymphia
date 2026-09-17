import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { ArrowRight, UploadCloud, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';

const NOME_REGEX = /^[A-Za-zÀ-ÖØ-öø-ÿ\s'.-]{2,100}$/;
const REGISTRO_REGEX = /^[0-9]{3,10}(-[A-Za-z0-9])?$/;
const UFS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

export default function RegisterProfissional({ onBackToLogin }) {
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

  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

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
          registro_uf: registroUf.toUpperCase()
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
    } catch (err) {
      login(tokenCriado, profCriado);
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
                onChange={(e) => setRegistroNumero(e.target.value.replace(/[^0-9-]/g, ''))}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="reg-prof-uf">UF</label>
              <select
                id="reg-prof-uf"
                className="form-control"
                value={registroUf}
                onChange={(e) => setRegistroUf(e.target.value)}
              >
                {UFS_BRASIL.map((uf) => (
                  <option key={uf} value={uf}>{uf}</option>
                ))}
              </select>
            </div>
          </div>

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
    </div>
  );
}
