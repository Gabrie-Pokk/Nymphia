import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { MessageCircle, Flag, Send, ShieldAlert, Heart, Plus, AlertCircle } from 'lucide-react';

export default function CommunityFeed({ onBack }) {
  const { authHeaders } = useAuth();
  const [grupos, setGrupos] = useState([]);
  const [grupoSelecionado, setGrupoSelecionado] = useState('Primeiro Trimestre');
  const [posts, setPosts] = useState([]);
  const [novoPostConteudo, setNovoPostConteudo] = useState('');
  const [comentarioTexto, setComentarioTexto] = useState({});
  const [mostrarNovoPost, setMostrarNovoPost] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [aviso, setAviso] = useState('');

  const carregarGrupos = async () => {
    try {
      const res = await fetch('/comunidade/grupos');
      if (res.ok) {
        const data = await res.json();
        setGrupos(data);
        if (data.length > 0) setGrupoSelecionado(data[0]);
      }
    } catch (err) {}
  };

  const carregarPosts = async (grupo) => {
    try {
      const res = await fetch(`/comunidade/posts?grupo=${encodeURIComponent(grupo)}`, {
        headers: authHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    carregarGrupos();
  }, []);

  useEffect(() => {
    if (grupoSelecionado) {
      carregarPosts(grupoSelecionado);
    }
  }, [grupoSelecionado]);

  const handleCriarPost = async (e) => {
    e.preventDefault();
    if (!novoPostConteudo.trim()) return;

    setCarregando(true);
    setAviso('');
    try {
      const res = await fetch('/comunidade/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          grupo: grupoSelecionado,
          conteudo: novoPostConteudo.trim()
        })
      });
      const data = await res.json();
      if (res.ok) {
        setNovoPostConteudo('');
        setMostrarNovoPost(false);
        carregarPosts(grupoSelecionado);
      }
    } catch (err) {
    } finally {
      setCarregando(false);
    }
  };

  const handleComentar = async (postId) => {
    const texto = comentarioTexto[postId];
    if (!texto || !texto.trim()) return;

    try {
      const res = await fetch(`/comunidade/posts/${postId}/comentar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ conteudo: texto.trim() })
      });
      if (res.ok) {
        setComentarioTexto((prev) => ({ ...prev, [postId]: '' }));
        carregarPosts(grupoSelecionado);
      }
    } catch (err) {}
  };

  const handleDenunciar = async (postId) => {
    try {
      const res = await fetch(`/comunidade/posts/${postId}/denunciar`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (res.ok) {
        alert('Conteúdo sinalizado para moderação humana.');
        carregarPosts(grupoSelecionado);
      }
    } catch (err) {}
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2>Comunidade Segura Nymphia</h2>
          <p className="text-muted" style={{ fontSize: '0.82rem' }}>
            Apoio mútuo sob anonimato protegido e moderação clínica em 3 camadas
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setMostrarNovoPost(!mostrarNovoPost)}
          style={{ minHeight: '38px', padding: '6px 12px', fontSize: '0.85rem' }}
        >
          <Plus size={16} /> Publicar
        </button>
      </div>

      {/* Seletor de Grupos */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px', marginBottom: '16px' }}>
        {grupos.map((g) => (
          <button
            key={g}
            type="button"
            className={grupoSelecionado === g ? 'btn btn-vinho' : 'btn btn-outline'}
            style={{ whiteSpace: 'nowrap', minHeight: '38px', fontSize: '0.82rem', padding: '6px 14px' }}
            onClick={() => setGrupoSelecionado(g)}
          >
            {g}
          </button>
        ))}
      </div>

      {/* Formulário Novo Post */}
      {mostrarNovoPost && (
        <form onSubmit={handleCriarPost} className="card" style={{ border: '2px solid var(--color-rosa)', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Publicar em "{grupoSelecionado}"</h3>
          <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: '10px' }}>
            Seu nome real nunca é exibido. Você aparecerá com um apelido protegido.
          </p>

          <div className="form-group">
            <textarea
              className="form-control"
              rows={3}
              placeholder="Compartilhe sua dúvida ou momento gestacional..."
              value={novoPostConteudo}
              onChange={(e) => setNovoPostConteudo(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => setMostrarNovoPost(false)}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ flex: 1 }}
              disabled={carregando}
            >
              {carregando ? 'Publicando...' : 'Postar'}
            </button>
          </div>
        </form>
      )}

      {/* Feed de Posts */}
      {posts.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
          <p className="text-muted">Nenhuma postagem neste grupo ainda. Seja a primeira a compartilhar!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {posts.map((p) => (
            <div key={p.id} className="card" style={{ padding: '16px', margin: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 700, color: 'var(--color-vinho)', fontSize: '0.9rem' }}>
                  {p.apelido}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {new Date(p.criado_em).toLocaleDateString('pt-BR')}
                  </span>
                  <button
                    onClick={() => handleDenunciar(p.id)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
                    title="Denunciar conteúdo à moderação"
                    aria-label="Denunciar postagem"
                  >
                    <Flag size={14} />
                  </button>
                </div>
              </div>

              <p style={{ fontSize: '0.92rem', color: 'var(--color-text-main)', lineHeight: 1.45, whiteSpace: 'pre-wrap', marginBottom: '12px' }}>
                {p.conteudo}
              </p>

              {/* Lista de Comentários */}
              {p.comentarios && p.comentarios.length > 0 && (
                <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '10px' }}>
                  {p.comentarios.map((c) => (
                    <div key={c.id} style={{ backgroundColor: '#FFFFFF', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: '0.82rem' }}>
                      <strong style={{ color: 'var(--color-vinho)', display: 'block', fontSize: '0.78rem' }}>{c.apelido}:</strong>
                      <span style={{ color: 'var(--color-text-main)' }}>{c.conteudo}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Campo para responder/comentar */}
              <div style={{ display: 'flex', gap: '6px' }}>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Deixar uma palavra de apoio..."
                  value={comentarioTexto[p.id] || ''}
                  onChange={(e) => setComentarioTexto({ ...comentarioTexto, [p.id]: e.target.value })}
                  style={{ minHeight: '38px', fontSize: '0.85rem' }}
                />
                <button
                  onClick={() => handleComentar(p.id)}
                  className="btn btn-outline"
                  style={{ minHeight: '38px', minWidth: '38px', padding: '0 12px' }}
                  aria-label="Enviar comentário"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
