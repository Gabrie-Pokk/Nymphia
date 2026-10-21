import React, { useEffect, useState } from 'react';
import LotusLogo from '../components/LotusLogo';
import { apiFetch } from '../utils/api';
import { ShieldCheck, FileText, Check, X, RefreshCw, ExternalLink, LogOut } from 'lucide-react';

import { formatDate } from '../utils/dateUtils';
/**
 * Área da equipe Nymphia: conferência e aprovação de profissionais.
 *
 * Todo profissional entra como pendente e só acessa pacientes depois que a
 * equipe confere o registro no portal do Conselho e aprova aqui.
 * O token da equipe (NYMPHIA_ADMIN_TOKEN, configurado no servidor) fica só
 * nesta aba do navegador (sessionStorage) e some quando a aba é fechada.
 */

const CHAVE_TOKEN = 'nymphia_equipe_token';
const CHAVE_NOME = 'nymphia_equipe_nome';
const PORTAL_CFM = 'https://portal.cfm.org.br/busca-medicos';

function lerSessao(chave) {
  try {
    return sessionStorage.getItem(chave) || '';
  } catch {
    return '';
  }
}

function gravarSessao(chave, valor) {
  try {
    if (valor) sessionStorage.setItem(chave, valor);
    else sessionStorage.removeItem(chave);
  } catch {
    // Sem sessionStorage a página funciona, só pede o token de novo ao recarregar
  }
}

const SITUACOES = [
  { id: 'pendente', rotulo: 'Pendentes' },
  { id: 'aprovado', rotulo: 'Aprovados' },
  { id: 'rejeitado', rotulo: 'Rejeitados' },
  { id: 'todos', rotulo: 'Todos' }
];

const COR_SITUACAO = {
  pendente: '#E67E22',
  aprovado: '#27AE60',
  rejeitado: 'var(--color-vermelho)'
};

export default function EquipeAdmin({ onExit }) {
  const [token, setToken] = useState(() => lerSessao(CHAVE_TOKEN));
  const [tokenDigitado, setTokenDigitado] = useState('');
  const [nome, setNome] = useState(() => lerSessao(CHAVE_NOME));
  const [situacao, setSituacao] = useState('pendente');
  const [lista, setLista] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [aviso, setAviso] = useState('');
  const [rejeitandoId, setRejeitandoId] = useState(null);
  const [motivo, setMotivo] = useState('');
  const [ocupadoId, setOcupadoId] = useState(null);
  const [documento, setDocumento] = useState(null); // { url, tipo, nome }

  const cabecalhos = () => ({ 'X-Admin-Token': token, 'X-Admin-Nome': nome || 'equipe' });

  const sair = () => {
    gravarSessao(CHAVE_TOKEN, '');
    setToken('');
    setLista([]);
    fecharDocumento();
  };

  const carregar = async () => {
    if (!token) return;
    setCarregando(true);
    setErro('');
    try {
      const data = await apiFetch(`/admin/profissionais?situacao=${situacao}`, {
        headers: cabecalhos(),
        skipAuth: true
      });
      setLista(Array.isArray(data) ? data : []);
    } catch (err) {
      if (err.status === 401) {
        sair();
        setErro('Token da equipe incorreto. Confira o valor de NYMPHIA_ADMIN_TOKEN no servidor.');
      } else if (err.status === 503) {
        setErro('A área da equipe está desligada neste servidor: falta configurar NYMPHIA_ADMIN_TOKEN (32 caracteres ou mais).');
      } else {
        setErro(err.message || 'Não foi possível carregar a lista.');
      }
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregar();
  }, [token, situacao]);

  const entrar = (e) => {
    e.preventDefault();
    const limpo = tokenDigitado.trim();
    if (limpo.length < 32) {
      setErro('O token da equipe tem 32 caracteres ou mais.');
      return;
    }
    gravarSessao(CHAVE_TOKEN, limpo);
    gravarSessao(CHAVE_NOME, nome.trim());
    setTokenDigitado('');
    setToken(limpo);
  };

  const fecharDocumento = () => {
    if (documento?.url) URL.revokeObjectURL(documento.url);
    setDocumento(null);
  };

  const abrirDocumento = async (prof) => {
    setErro('');
    setOcupadoId(prof.id);
    try {
      const res = await fetch(`/admin/profissionais/${prof.id}/documento`, { headers: cabecalhos() });
      if (!res.ok) {
        let mensagem = 'Não foi possível abrir o documento.';
        try {
          const corpo = await res.json();
          if (corpo?.detail) mensagem = corpo.detail;
        } catch {
          // resposta sem JSON
        }
        throw new Error(mensagem);
      }
      const blob = await res.blob();
      fecharDocumento();
      setDocumento({ url: URL.createObjectURL(blob), tipo: blob.type, nome: prof.nome });
    } catch (err) {
      setErro(err.message);
    } finally {
      setOcupadoId(null);
    }
  };

  const aprovar = async (prof) => {
    setErro('');
    setAviso('');
    setOcupadoId(prof.id);
    try {
      await apiFetch(`/admin/profissionais/${prof.id}/aprovar`, {
        method: 'POST',
        headers: cabecalhos(),
        skipAuth: true
      });
      setAviso(`Aprovado: ${prof.nome} (${prof.registro}). A pessoa recebe um e-mail se o SMTP estiver configurado.`);
      await carregar();
    } catch (err) {
      setErro(err.message);
    } finally {
      setOcupadoId(null);
    }
  };

  const rejeitar = async (prof) => {
    if (motivo.trim().length < 5) {
      setErro('Escreva o motivo da rejeição (pelo menos 5 caracteres). Ele vai no e-mail para a pessoa.');
      return;
    }
    setErro('');
    setAviso('');
    setOcupadoId(prof.id);
    try {
      await apiFetch(`/admin/profissionais/${prof.id}/rejeitar`, {
        method: 'POST',
        headers: { ...cabecalhos(), 'Content-Type': 'application/json' },
        skipAuth: true,
        body: JSON.stringify({ motivo: motivo.trim() })
      });
      setAviso(`Rejeitado: ${prof.nome} (${prof.registro}).`);
      setRejeitandoId(null);
      setMotivo('');
      await carregar();
    } catch (err) {
      setErro(err.message);
    } finally {
      setOcupadoId(null);
    }
  };

  const caixaMensagem = (texto, cor, fundo, papel) => (
    <div
      role={papel}
      style={{
        padding: '10px 14px',
        borderRadius: 'var(--radius-sm)',
        borderLeft: `4px solid ${cor}`,
        backgroundColor: fundo,
        fontSize: '0.85rem',
        marginBottom: '14px',
        lineHeight: 1.45
      }}
    >
      {texto}
    </div>
  );

  return (
    <div style={{ padding: '24px', maxWidth: '760px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', marginBottom: '18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <LotusLogo size={36} />
          <div>
            <h1 style={{ fontSize: '1.3rem', margin: 0, color: 'var(--color-vinho)' }}>Área da equipe</h1>
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Conferência de profissionais de saúde</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {token && (
            <button type="button" className="btn btn-outline" onClick={sair} style={{ minHeight: '38px', fontSize: '0.82rem' }}>
              <LogOut size={14} /> Sair
            </button>
          )}
          <button type="button" className="btn btn-outline" onClick={onExit} style={{ minHeight: '38px', fontSize: '0.82rem' }}>
            Voltar ao app
          </button>
        </div>
      </div>

      {erro && caixaMensagem(erro, 'var(--color-vermelho)', '#FDEDEC', 'alert')}
      {aviso && caixaMensagem(aviso, '#27AE60', '#EAF7EF', 'status')}

      {!token ? (
        <form onSubmit={entrar} className="card" style={{ padding: '18px' }}>
          <p style={{ fontSize: '0.88rem', lineHeight: 1.5, marginTop: 0 }}>
            Cole o token da equipe (o mesmo valor de <code>NYMPHIA_ADMIN_TOKEN</code> no servidor). Ele fica guardado só nesta aba e
            some quando ela é fechada.
          </p>
          <div className="form-group" style={{ marginBottom: '12px' }}>
            <label htmlFor="equipe-nome" style={{ fontSize: '0.82rem', fontWeight: 600 }}>Seu nome (vai para o registro de auditoria)</label>
            <input id="equipe-nome" className="form-control" value={nome} onChange={(e) => setNome(e.target.value)} maxLength={80} placeholder="Ex.: Gabriel" />
          </div>
          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label htmlFor="equipe-token" style={{ fontSize: '0.82rem', fontWeight: 600 }}>Token da equipe</label>
            <input
              id="equipe-token"
              type="password"
              autoComplete="off"
              className="form-control"
              value={tokenDigitado}
              onChange={(e) => setTokenDigitado(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ minHeight: '42px' }}>
            <ShieldCheck size={16} /> Entrar
          </button>
        </form>
      ) : (
        <>
          <div className="card" style={{ padding: '14px 16px', marginBottom: '14px', fontSize: '0.84rem', lineHeight: 1.5 }}>
            <strong>Como conferir:</strong> abra o documento enviado, procure o nome e o número no{' '}
            <a href={PORTAL_CFM} target="_blank" rel="noopener noreferrer">portal do CFM <ExternalLink size={12} /></a>{' '}
            (para COREN, no site do COREN do estado) e confira se a situação é regular. Só aprove quando nome, número e UF baterem.
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px', alignItems: 'center' }}>
            {SITUACOES.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setSituacao(s.id)}
                className={`btn ${situacao === s.id ? 'btn-primary' : 'btn-outline'}`}
                style={{ minHeight: '36px', fontSize: '0.82rem', padding: '6px 12px' }}
              >
                {s.rotulo}
              </button>
            ))}
            <button type="button" className="btn btn-outline" onClick={carregar} disabled={carregando} style={{ minHeight: '36px', fontSize: '0.82rem' }}>
              <RefreshCw size={14} /> {carregando ? 'Carregando...' : 'Atualizar'}
            </button>
          </div>

          {!carregando && lista.length === 0 && (
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.88rem' }}>Nenhum profissional nesta lista.</p>
          )}

          {lista.map((prof) => (
            <div key={prof.id} className="card" style={{ padding: '14px 16px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
                <div>
                  <strong style={{ color: 'var(--color-vinho)' }}>{prof.nome}</strong>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>{prof.email}</div>
                  <div style={{ fontSize: '0.86rem', marginTop: '4px' }}>
                    <strong>{prof.registro}</strong>
                    {prof.criado_em && <> · cadastro em {formatDate(prof.criado_em)}</>}
                  </div>
                  <div style={{ fontSize: '0.78rem', marginTop: '2px', color: prof.enviou_documento ? '#1E7E34' : '#A04000' }}>
                    {prof.enviou_documento ? 'Enviou documento' : 'Não enviou documento'}
                  </div>
                </div>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: COR_SITUACAO[prof.status_verificacao] || 'inherit' }}>
                  {prof.status_verificacao}
                </span>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
                {prof.enviou_documento && (
                  <button type="button" className="btn btn-outline" disabled={ocupadoId === prof.id} onClick={() => abrirDocumento(prof)} style={{ minHeight: '36px', fontSize: '0.82rem' }}>
                    <FileText size={14} /> Ver documento
                  </button>
                )}
                {prof.status_verificacao !== 'aprovado' && (
                  <button type="button" className="btn btn-primary" disabled={ocupadoId === prof.id} onClick={() => aprovar(prof)} style={{ minHeight: '36px', fontSize: '0.82rem' }}>
                    <Check size={14} /> Aprovar
                  </button>
                )}
                {prof.status_verificacao !== 'rejeitado' && rejeitandoId !== prof.id && (
                  <button type="button" className="btn btn-outline" disabled={ocupadoId === prof.id} onClick={() => { setRejeitandoId(prof.id); setMotivo(''); }} style={{ minHeight: '36px', fontSize: '0.82rem', color: 'var(--color-vermelho)' }}>
                    <X size={14} /> Rejeitar
                  </button>
                )}
              </div>

              {rejeitandoId === prof.id && (
                <div style={{ marginTop: '12px' }}>
                  <label htmlFor={`motivo-${prof.id}`} style={{ fontSize: '0.82rem', fontWeight: 600 }}>Motivo (vai no e-mail para a pessoa)</label>
                  <textarea
                    id={`motivo-${prof.id}`}
                    className="form-control"
                    rows={2}
                    maxLength={500}
                    value={motivo}
                    onChange={(e) => setMotivo(e.target.value)}
                    placeholder="Ex.: registro não encontrado no portal do CFM com este nome"
                  />
                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                    <button type="button" className="btn btn-outline" onClick={() => setRejeitandoId(null)} style={{ minHeight: '36px', fontSize: '0.82rem' }}>
                      Cancelar
                    </button>
                    <button type="button" className="btn btn-primary" disabled={ocupadoId === prof.id} onClick={() => rejeitar(prof)} style={{ minHeight: '36px', fontSize: '0.82rem', backgroundColor: 'var(--color-vermelho)' }}>
                      Confirmar rejeição
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}

          {documento && (
            <div className="card" style={{ padding: '12px', marginTop: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <strong style={{ fontSize: '0.9rem' }}>Documento de {documento.nome}</strong>
                <button type="button" className="btn btn-outline" onClick={fecharDocumento} style={{ minHeight: '32px', fontSize: '0.8rem' }}>
                  Fechar
                </button>
              </div>
              {documento.tipo.startsWith('image/') ? (
                <img src={documento.url} alt={`Documento de ${documento.nome}`} style={{ maxWidth: '100%', borderRadius: 'var(--radius-sm)' }} />
              ) : (
                <iframe title={`Documento de ${documento.nome}`} src={documento.url} style={{ width: '100%', height: '70vh', border: 'none' }} />
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
