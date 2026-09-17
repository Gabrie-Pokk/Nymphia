import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { 
  MessageCircle, Flag, Send, ShieldAlert, Heart, Plus, 
  Sparkles, CheckCircle2, SlidersHorizontal, AlertTriangle, X 
} from 'lucide-react';

const OPCOES_EXPERIENCIA = [
  'Primeira gestação (Mãe de 1ª viagem)',
  'Já tenho filhos (Mãe experiente)',
  'Gestação múltipla (Gêmeos ou mais)'
];

const OPCOES_PARTO = [
  'Parto normal humanizado',
  'Cesárea planejada / eletiva',
  'Parto domiciliar planejado',
  'Ainda estou decidindo com meu obstetra'
];

const OPCOES_INTERESSES = [
  { id: 'Nutrição & Receitas Gestacionais', label: '🥗 Nutrição & Receitas Gestacionais' },
  { id: 'Yoga, Exercícios & Bem-Estar', label: '🧘 Yoga, Exercícios & Bem-Estar' },
  { id: 'Amamentação & Cuidados com o Bebê', label: '🤱 Amamentação & Cuidados com o Bebê' },
  { id: 'Saúde Emocional & Puerpério', label: '💖 Saúde Emocional & Puerpério' },
  { id: 'Enxoval, Quarto & Preparativos', label: '🧸 Enxoval, Quarto & Preparativos' }
];

const OPCOES_ESTILO_VIDA = [
  'Tranquila e Conectada',
  'Prática e Dinâmica',
  'Estudiosa e Curiosa'
];

export default function CommunityFeed({ onBack }) {
  const { authHeaders } = useAuth();
  const [grupos, setGrupos] = useState([]);
  const [grupoSelecionado, setGrupoSelecionado] = useState('Primeiro Trimestre');
  const [posts, setPosts] = useState([]);
  const [novoPostConteudo, setNovoPostConteudo] = useState('');
  const [comentarioTexto, setComentarioTexto] = useState({});
  const [mostrarNovoPost, setMostrarNovoPost] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [erroModeracao, setErroModeracao] = useState('');
  const [erroComentario, setErroComentario] = useState({});

  // Questionário de Preferências e Gostos
  const [mostrarQuestionario, setMostrarQuestionario] = useState(false);
  const [preferencias, setPreferencias] = useState({
    experiencia: '',
    preferencia_parto: '',
    interesses: [],
    estilo_vida: '',
    grupos_recomendados: []
  });
  const [filtroApenasRecomendados, setFiltroApenasRecomendados] = useState(false);
  const [salvandoPref, setSalvandoPref] = useState(false);

  const carregarGrupos = async () => {
    try {
      const res = await fetch('/comunidade/grupos');
      if (res.ok) {
        const data = await res.json();
        setGrupos(data);
        if (data.length > 0 && !grupoSelecionado) setGrupoSelecionado(data[0]);
      }
    } catch (err) {}
  };

  const carregarPreferencias = async () => {
    try {
      const res = await fetch('/comunidade/preferencias', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setPreferencias({
          experiencia: data.experiencia || '',
          preferencia_parto: data.preferencia_parto || '',
          interesses: data.interesses || [],
          estilo_vida: data.estilo_vida || '',
          grupos_recomendados: data.grupos_recomendados || []
        });
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
    carregarPreferencias();
  }, []);

  useEffect(() => {
    if (grupoSelecionado) {
      carregarPosts(grupoSelecionado);
    }
  }, [grupoSelecionado]);

  const handleSalvarQuestionario = async (e) => {
    e.preventDefault();
    setSalvandoPref(true);
    try {
      const res = await fetch('/comunidade/preferencias', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          experiencia: preferencias.experiencia,
          preferencia_parto: preferencias.preferencia_parto,
          interesses: preferencias.interesses,
          estilo_vida: preferencias.estilo_vida
        })
      });
      if (res.ok) {
        const data = await res.json();
        setPreferencias(data);
        setMostrarQuestionario(false);
        if (data.grupos_recomendados && data.grupos_recomendados.length > 0) {
          setGrupoSelecionado(data.grupos_recomendados[0]);
        }
      }
    } catch (err) {
    } finally {
      setSalvandoPref(false);
    }
  };

  const toggleInteresse = (id) => {
    setPreferencias((prev) => {
      const jaExiste = prev.interesses.includes(id);
      const novos = jaExiste ? prev.interesses.filter((item) => item !== id) : [...prev.interesses, id];
      return { ...prev, interesses: novos };
    });
  };

  const handleCriarPost = async (e) => {
    e.preventDefault();
    if (!novoPostConteudo.trim()) return;

    setCarregando(true);
    setErroModeracao('');
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
      } else {
        setErroModeracao(data.detail || 'Não foi possível publicar devido às Diretrizes de Segurança da Comunidade.');
      }
    } catch (err) {
      setErroModeracao('Erro ao conectar ao servidor. Tente novamente.');
    } finally {
      setCarregando(false);
    }
  };

  const handleComentar = async (postId) => {
    const texto = comentarioTexto[postId];
    if (!texto || !texto.trim()) return;

    setErroComentario((prev) => ({ ...prev, [postId]: '' }));
    try {
      const res = await fetch(`/comunidade/posts/${postId}/comentar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ conteudo: texto.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        setComentarioTexto((prev) => ({ ...prev, [postId]: '' }));
        carregarPosts(grupoSelecionado);
      } else {
        setErroComentario((prev) => ({ ...prev, [postId]: data.detail || 'Comentário barrado pela moderação.' }));
      }
    } catch (err) {
      setErroComentario((prev) => ({ ...prev, [postId]: 'Erro ao enviar comentário.' }));
    }
  };

  const handleDenunciar = async (postId) => {
    try {
      const res = await fetch(`/comunidade/posts/${postId}/denunciar`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (res.ok) {
        alert('Conteúdo sinalizado com prioridade para a moderação clínica.');
        carregarPosts(grupoSelecionado);
      }
    } catch (err) {}
  };

  const gruposExibidos = filtroApenasRecomendados
    ? grupos.filter((g) => preferencias.grupos_recomendados.includes(g))
    : grupos;

  return (
    <div style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}>
      <BackButton onClick={onBack} label="Voltar para Início" />

      {/* Cabeçalho da Comunidade */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--color-vinho)' }}>Comunidade Segura Nymphia</h2>
          <p className="text-muted" style={{ fontSize: '0.82rem', margin: '2px 0 0' }}>
            Apoio mútuo sob anonimato protegido e moderação clínica em 3 camadas
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn btn-outline"
            onClick={() => setMostrarQuestionario(true)}
            style={{ minHeight: '38px', padding: '6px 12px', fontSize: '0.82rem', borderColor: 'var(--color-dourado)', color: 'var(--color-vinho)' }}
            title="Personalizar comunidade conforme seus gostos"
          >
            <Sparkles size={16} color="var(--color-dourado)" /> {preferencias.experiencia ? 'Meus Gostos' : 'Questionário de Gostos'}
          </button>
          <button
            className="btn btn-primary"
            onClick={() => { setMostrarNovoPost(!mostrarNovoPost); setErroModeracao(''); }}
            style={{ minHeight: '38px', padding: '6px 14px', fontSize: '0.82rem' }}
          >
            <Plus size={16} /> Publicar
          </button>
        </div>
      </div>

      {/* Banner de Personalização / Questionário de Gostos */}
      {preferencias.experiencia ? (
        <div className="card" style={{ padding: '12px 16px', marginBottom: '14px', backgroundColor: 'var(--color-rosa-claro)', border: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ fontSize: '0.82rem' }}>
              <span style={{ fontWeight: 700, color: 'var(--color-vinho)' }}>✨ Comunidade voltada ao seu perfil: </span>
              <span style={{ color: 'var(--color-text-main)' }}>{preferencias.experiencia} • {preferencias.preferencia_parto || 'Parto em definição'}</span>
            </div>
            <button
              onClick={() => setMostrarQuestionario(true)}
              style={{ background: 'transparent', border: 'none', color: 'var(--color-rosa)', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
            >
              Editar preferências
            </button>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: '14px', marginBottom: '14px', border: '1.5px dashed var(--color-dourado)', backgroundColor: '#FFFCF5' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={24} color="var(--color-dourado)" />
            <div style={{ flex: 1 }}>
              <strong style={{ fontSize: '0.88rem', color: 'var(--color-vinho)' }}>Questionário de Gostos da Gestante:</strong>
              <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: '2px 0 0' }}>
                Responda em 30 segundos para recomendarmos grupos afins com suas preferências de parto, nutrição e bem-estar.
              </p>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => setMostrarQuestionario(true)}
              style={{ minHeight: '34px', padding: '4px 12px', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
            >
              Responder
            </button>
          </div>
        </div>
      )}

      {/* Filtro Rápido de Recomendados vs Todos */}
      {preferencias.grupos_recomendados.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
          <button
            type="button"
            className={!filtroApenasRecomendados ? 'btn btn-vinho' : 'btn btn-outline'}
            style={{ fontSize: '0.75rem', minHeight: '30px', padding: '4px 10px' }}
            onClick={() => setFiltroApenasRecomendados(false)}
          >
            Todos os Grupos ({grupos.length})
          </button>
          <button
            type="button"
            className={filtroApenasRecomendados ? 'btn btn-vinho' : 'btn btn-outline'}
            style={{ fontSize: '0.75rem', minHeight: '30px', padding: '4px 10px', borderColor: 'var(--color-dourado)' }}
            onClick={() => setFiltroApenasRecomendados(true)}
          >
            ✨ Recomendados para Você ({preferencias.grupos_recomendados.length})
          </button>
        </div>
      )}

      {/* Seletor de Grupos em Rolagem Horizontal Segura */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px', marginBottom: '16px', width: '100%', maxWidth: '100%' }}>
        {gruposExibidos.map((g) => {
          const isRecomendado = preferencias.grupos_recomendados.includes(g);
          const isSelected = grupoSelecionado === g;
          return (
            <button
              key={g}
              type="button"
              className={isSelected ? 'btn btn-vinho' : 'btn btn-outline'}
              style={{
                whiteSpace: 'nowrap',
                minHeight: '38px',
                fontSize: '0.82rem',
                padding: '6px 14px',
                borderColor: isRecomendado ? 'var(--color-dourado)' : undefined,
                fontWeight: isRecomendado ? 700 : 500
              }}
              onClick={() => setGrupoSelecionado(g)}
            >
              {isRecomendado && !isSelected && '✨ '}
              {g}
            </button>
          );
        })}
      </div>

      {/* Formulário Novo Post com Moderação Visual */}
      {mostrarNovoPost && (
        <form onSubmit={handleCriarPost} className="card" style={{ border: '2px solid var(--color-rosa)', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '6px', color: 'var(--color-vinho)' }}>Publicar em "{grupoSelecionado}"</h3>
          <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: '10px' }}>
            Seu nome real nunca é revelado. Você será identificada com um pseudônimo anônimo e seguro.
          </p>

          {erroModeracao && (
            <div style={{ backgroundColor: '#FDEDEC', border: '1.5px solid var(--color-vermelho)', color: '#922B21', padding: '10px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '12px', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, marginBottom: '4px' }}>
                <ShieldAlert size={16} /> Moderação da Comunidade Segura:
              </div>
              {erroModeracao}
            </div>
          )}

          <div className="form-group">
            <textarea
              className="form-control"
              rows={3}
              placeholder="Compartilhe sua dúvida, momento ou experiência gestacional..."
              value={novoPostConteudo}
              maxLength={1500}
              minLength={5}
              onChange={(e) => setNovoPostConteudo(e.target.value)}
              required
              style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box', overflowWrap: 'anywhere', wordBreak: 'break-word' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => { setMostrarNovoPost(false); setErroModeracao(''); }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ flex: 1 }}
              disabled={carregando}
            >
              {carregando ? 'Publicando...' : 'Postar com Segurança'}
            </button>
          </div>
        </form>
      )}

      {/* Feed de Posts com Contenção de Texto */}
      {posts.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
          <p className="text-muted">Nenhuma postagem neste grupo ainda. Seja a primeira a compartilhar!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', width: '100%', maxWidth: '100%' }}>
          {posts.map((p) => (
            <div key={p.id} className="card" style={{ padding: '16px', margin: 0, width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}>
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
                    style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: '4px' }}
                    title="Denunciar conteúdo à moderação"
                    aria-label="Denunciar postagem"
                  >
                    <Flag size={14} />
                  </button>
                </div>
              </div>

              <p style={{ fontSize: '0.92rem', color: 'var(--color-text-main)', lineHeight: 1.45, whiteSpace: 'pre-wrap', marginBottom: '12px', overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
                {p.conteudo}
              </p>

              {/* Lista de Comentários */}
              {p.comentarios && p.comentarios.length > 0 && (
                <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '10px' }}>
                  {p.comentarios.map((c) => (
                    <div key={c.id} style={{ backgroundColor: '#FFFFFF', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: '0.82rem', overflowWrap: 'anywhere', wordBreak: 'break-word' }}>
                      <strong style={{ color: 'var(--color-vinho)', display: 'block', fontSize: '0.78rem' }}>{c.apelido}:</strong>
                      <span style={{ color: 'var(--color-text-main)' }}>{c.conteudo}</span>
                    </div>
                  ))}
                </div>
              )}

              {erroComentario[p.id] && (
                <div style={{ fontSize: '0.78rem', color: 'var(--color-vermelho)', marginBottom: '8px' }}>
                  ⚠️ {erroComentario[p.id]}
                </div>
              )}

              {/* Campo para responder/comentar */}
              <div style={{ display: 'flex', gap: '6px', width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Deixar uma palavra de apoio..."
                  value={comentarioTexto[p.id] || ''}
                  onChange={(e) => setComentarioTexto({ ...comentarioTexto, [p.id]: e.target.value })}
                  style={{ minHeight: '38px', fontSize: '0.85rem', flex: 1, minWidth: 0 }}
                />
                <button
                  onClick={() => handleComentar(p.id)}
                  className="btn btn-outline"
                  style={{ minWidth: '40px', minHeight: '38px', padding: '0 10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  aria-label="Enviar comentário"
                >
                  <Send size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Interativo: Questionário de Gostos da Gestante */}
      {mostrarQuestionario && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(34, 10, 16, 0.65)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 9999,
          padding: '16px'
        }}>
          <div className="card" style={{
            width: '100%',
            maxWidth: '520px',
            maxHeight: '90vh',
            overflowY: 'auto',
            backgroundColor: '#FFFFFF',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)',
            padding: '24px',
            position: 'relative'
          }}>
            <button
              onClick={() => setMostrarQuestionario(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
              aria-label="Fechar"
            >
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Sparkles size={24} color="var(--color-dourado)" />
              <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--color-vinho)' }}>Questionário de Gostos da Gestante</h3>
            </div>
            <p className="text-muted" style={{ fontSize: '0.84rem', marginBottom: '18px' }}>
              Conte-nos sobre seus gostos e fase gestacional para adaptarmos a Comunidade Segura aos tópicos que mais fazem sentido para você.
            </p>

            <form onSubmit={handleSalvarQuestionario}>
              {/* Pergunta 1: Experiência */}
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.88rem' }}>
                  1. Qual é a sua experiência na gestação?
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {OPCOES_EXPERIENCIA.map((opt) => (
                    <label
                      key={opt}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        border: preferencias.experiencia === opt ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                        backgroundColor: preferencias.experiencia === opt ? 'var(--color-rosa-claro)' : '#FFFFFF',
                        cursor: 'pointer',
                        fontSize: '0.86rem'
                      }}
                    >
                      <input
                        type="radio"
                        name="experiencia"
                        checked={preferencias.experiencia === opt}
                        onChange={() => setPreferencias({ ...preferencias, experiencia: opt })}
                        style={{ width: 'auto !important' }}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>

              {/* Pergunta 2: Preferência de Parto */}
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.88rem' }}>
                  2. Qual a sua preferência ou expectativa de parto?
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {OPCOES_PARTO.map((opt) => (
                    <label
                      key={opt}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        border: preferencias.preferencia_parto === opt ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                        backgroundColor: preferencias.preferencia_parto === opt ? 'var(--color-rosa-claro)' : '#FFFFFF',
                        cursor: 'pointer',
                        fontSize: '0.86rem'
                      }}
                    >
                      <input
                        type="radio"
                        name="preferencia_parto"
                        checked={preferencias.preferencia_parto === opt}
                        onChange={() => setPreferencias({ ...preferencias, preferencia_parto: opt })}
                        style={{ width: 'auto !important' }}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>

              {/* Pergunta 3: Interesses e Gostos (Múltipla Seleção) */}
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.88rem' }}>
                  3. Quais temas e gostos você mais gostaria de acompanhar? (Selecione todos que desejar)
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {OPCOES_INTERESSES.map((item) => {
                    const selecionado = preferencias.interesses.includes(item.id);
                    return (
                      <label
                        key={item.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          border: selecionado ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                          backgroundColor: selecionado ? 'var(--color-rosa-claro)' : '#FFFFFF',
                          cursor: 'pointer',
                          fontSize: '0.86rem'
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={selecionado}
                          onChange={() => toggleInteresse(item.id)}
                          style={{ width: 'auto !important' }}
                        />
                        {item.label}
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Pergunta 4: Estilo de Vida */}
              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.88rem' }}>
                  4. Como você define seu estilo de rotina e autocuidado?
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {OPCOES_ESTILO_VIDA.map((opt) => (
                    <label
                      key={opt}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        border: preferencias.estilo_vida === opt ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                        backgroundColor: preferencias.estilo_vida === opt ? 'var(--color-rosa-claro)' : '#FFFFFF',
                        cursor: 'pointer',
                        fontSize: '0.86rem'
                      }}
                    >
                      <input
                        type="radio"
                        name="estilo_vida"
                        checked={preferencias.estilo_vida === opt}
                        onChange={() => setPreferencias({ ...preferencias, estilo_vida: opt })}
                        style={{ width: 'auto !important' }}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{ flex: 1 }}
                  onClick={() => setMostrarQuestionario(false)}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  disabled={salvandoPref}
                >
                  {salvandoPref ? 'Salvando...' : 'Salvar Preferências'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
