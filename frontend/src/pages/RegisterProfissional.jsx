import React, { useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { ArrowRight, UploadCloud, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';

export default function RegisterProfissional({ onBackToLogin }) {
  const { login } = useAuth();
  const [etapa, setEtapa] = useState(1); // 1: dados cadastrais, 2: upload documento comprovante
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

    if (registroNumero.trim().length < 3) {
      setErro('Número de registro profissional inválido.');
      return;
    }

    setCarregando(true);
    try {
      const res = await fetch('/auth/profissional/cadastro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nome.trim(),
          email: email.trim().toLowerCase(),
          senha,
          registro_tipo: registroTipo,
          registro_numero: registroNumero.trim(),
          registro_uf: registroUf.toUpperCase()
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao cadastrar profissional.');
      }
      setTokenCriado(data.token);
      setProfCriado(data);
      setEtapa(2); // Avança para etapa de upload opcional
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  const handleUploadDocumento = async () => {
    if (!arquivo) {
      // Conclui sem upload (acesso não fica bloqueado esperando)
      login(tokenCriado, profCriado);
      return;
    }

    setCarregando(true);
    const formData = new FormData();
    formData.append('arquivo', arquivo);

    try {
      const res = await fetch('/auth/profissional/upload-documento', {
        method: 'POST',
        headers: { Authorization: `Bearer ${tokenCriado}` },
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Falha ao enviar documento.');
      }
      login(tokenCriado, profCriado);
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  const handlePularUpload = () => {
    // Acesso liberado imediatamente; verificação é posterior e não bloqueia
    login(tokenCriado, profCriado);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '460px', margin: '0 auto' }}>
      <BackButton onClick={onBackToLogin} label="Voltar para Login" />

      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <LotusLogo size={44} color="var(--color-vinho)" className="mx-auto" />
        <h1 style={{ fontSize: '1.5rem', marginTop: '8px' }}>Cadastro de Profissional</h1>
        <p className="text-muted">Área clínica para Médicos Obstetras e Enfermeiros Obstétricos</p>
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
            <label htmlFor="prof-nome">Nome Completo</label>
            <input
              id="prof-nome"
              type="text"
              className="form-control"
              placeholder="Dr(a). Seu Nome"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="prof-email">E-mail Profissional</label>
            <input
              id="prof-email"
              type="email"
              className="form-control"
              placeholder="doutor@clinica.com.br"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="prof-senha">Senha</label>
            <input
              id="prof-senha"
              type="password"
              className="form-control"
              placeholder="Mínimo 8 caracteres"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              minLength={8}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="prof-tipo">Conselho</label>
              <select
                id="prof-tipo"
                className="form-control"
                value={registroTipo}
                onChange={(e) => setRegistroTipo(e.target.value)}
              >
                <option value="CRM">CRM</option>
                <option value="COREN">COREN</option>
              </select>
            </div>

            <div className="form-group" style={{ flex: 2 }}>
              <label htmlFor="prof-num">Número</label>
              <input
                id="prof-num"
                type="text"
                className="form-control"
                placeholder="123456"
                value={registroNumero}
                onChange={(e) => setRegistroNumero(e.target.value)}
                required
              />
            </div>

            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="prof-uf">UF</label>
              <input
                id="prof-uf"
                type="text"
                className="form-control"
                placeholder="SP"
                maxLength={2}
                value={registroUf}
                onChange={(e) => setRegistroUf(e.target.value.toUpperCase())}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', minHeight: '48px', marginTop: '10px' }}
            disabled={carregando}
          >
            {carregando ? 'Cadastrando...' : 'Avançar para Verificação'}
            <ArrowRight size={18} />
          </button>
        </form>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '24px' }}>
          <UploadCloud size={44} color="var(--color-rosa)" style={{ margin: '0 auto 12px auto' }} />
          <h2 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Comprovante Profissional</h2>
          <p className="text-muted" style={{ fontSize: '0.88rem', marginBottom: '16px' }}>
            Envie uma foto da sua carteira profissional (CRM/COREN) ou diploma (PDF, JPG ou PNG, máx 10MB).
          </p>

          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={(e) => setArquivo(e.target.files[0])}
            style={{ marginBottom: '16px', display: 'block', width: '100%' }}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleUploadDocumento}
              disabled={carregando}
            >
              {carregando ? 'Enviando documento...' : 'Enviar e Acessar Painel'}
            </button>

            <button
              type="button"
              className="btn btn-outline"
              onClick={handlePularUpload}
              disabled={carregando}
            >
              Enviar Depois (Acessar Imediatamente)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
