import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { formatDate } from '../../utils/dateUtils';
import { 
  MessageCircle, Flag, Send, ShieldAlert, Heart, Plus, 
  Sparkles, CheckCircle2, SlidersHorizontal, AlertTriangle, X,
  Shield, PhoneCall, Scale, BookOpen, HeartHandshake, HelpCircle, Check, Info
} from 'lucide-react';

const MOTIVOS_DENUNCIA = [
  { id: 'desinformacao_saude', label: '🩺 Desinformação sobre saúde, vacinas ou parto', desc: 'Alegações médicas falsas, perigosas ou sem evidência' },
  { id: 'automedicacao', label: '💊 Indicação de medicamentos ou fórmulas caseiras de risco', desc: 'Indicação de remédios, dosagens ou chás contraindicados na gravidez' },
  { id: 'automutilacao_suicidio', label: '🆘 Sofrimento mental agudo / risco de ideação ou automutilação', desc: 'Aciona imediatamente o acolhimento emergencial humanizado (CVV 188)' },
  { id: 'violencia_assedio', label: '⚠️ Discurso de ódio, assédio, julgamento materno ou agressão', desc: 'Violação às diretrizes de respeito e convivência acolhedora' },
  { id: 'comercial_spam', label: '📢 Venda não autorizada, publicidade ou spam', desc: 'Divulgação comercial de produtos ou serviços não autorizados' },
  { id: 'outro', label: '❓ Outro motivo', desc: 'Descreva os detalhes na caixa de texto' }
];

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

  // Diretrizes da Comunidade & Moderação Estruturada (STF Tema 987)
  const [mostrarDiretrizes, setMostrarDiretrizes] = useState(false);
  const [denunciaModal, setDenunciaModal] = useState({ aberto: false, postId: null, comentarioId: null });
  const [denunciaMotivo, setDenunciaMotivo] = useState('desinformacao_saude');
  const [denunciaDetalhes, setDenunciaDetalhes] = useState('');
  const [enviandoDenuncia, setEnviandoDenuncia] = useState(false);

  // Protocolo CVV 188 / Saúde Mental
  const [modalAcolhimentoCvv, setModalAcolhimentoCvv] = useState({ aberto: false, dados: null });

  // Minhas Moderações & Recursos (STF Tema 987)
  const [modalModeracoes, setModalModeracoes] = useState(false);
  const [minhasModeracoes, setMinhasModeracoes] = useState([]);
  const [carregandoModeracoes, setCarregandoModeracoes] = useState(false);
  const [recursoForm, setRecursoForm] = useState({ postId: null, justificativa: '' });
  const [enviandoRecurso, setEnviandoRecurso] = useState(false);
  const [msgRecurso, setMsgRecurso] = useState({ texto: '', tipo: '' });

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

  const handleAbrirDenuncia = (postId, comentarioId = null) => {
    setDenunciaModal({ aberto: true, postId, comentarioId });
    setDenunciaMotivo('desinformacao_saude');
    setDenunciaDetalhes('');
  };

  const handleSubmeterDenuncia = async (e) => {
    e.preventDefault();
    if (!denunciaModal.postId && !denunciaModal.comentarioId) return;

    setEnviandoDenuncia(true);
    try {
      const endpoint = denunciaModal.postId
        ? `/comunidade/posts/${denunciaModal.postId}/denunciar`
        : `/comunidade/comentarios/${denunciaModal.comentarioId}/denunciar`;

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          motivo: denunciaMotivo,
          detalhes: denunciaDetalhes.trim() || undefined
        })
      });

      const data = await res.json();
      setDenunciaModal({ aberto: false, postId: null, comentarioId: null });

      if (data.protocolo_acolhimento) {
        setModalAcolhimentoCvv({ aberto: true, dados: data.protocolo_acolhimento });
      } else {
        alert(data.mensagem || 'Denúncia registrada com sucesso.');
      }
      carregarPosts(grupoSelecionado);
    } catch (err) {
      alert('Erro ao enviar denúncia. Tente novamente.');
    } finally {
      setEnviandoDenuncia(false);
    }
  };

  const carregarMinhasModeracoes = async () => {
    setCarregandoModeracoes(true);
    try {
      const res = await fetch('/comunidade/minhas-moderacoes', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setMinhasModeracoes(data);
      }
    } catch (err) {
    } finally {
      setCarregandoModeracoes(false);
    }
  };

  const handleSubmeterRecurso = async (e) => {
    e.preventDefault();
    if (!recursoForm.postId || !recursoForm.justificativa.trim()) return;

    setEnviandoRecurso(true);
    setMsgRecurso({ texto: '', tipo: '' });
    try {
      const res = await fetch(`/comunidade/posts/${recursoForm.postId}/recorrer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ justificativa: recursoForm.justificativa.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        setMsgRecurso({ texto: 'Recurso submetido com sucesso! A moderação clínica analisará sua justificativa.', tipo: 'sucesso' });
        setRecursoForm({ postId: null, justificativa: '' });
        carregarMinhasModeracoes();
      } else {
        setMsgRecurso({ texto: data.detail || 'Não foi possível submeter o recurso.', tipo: 'erro' });
      }
    } catch (err) {
      setMsgRecurso({ texto: 'Erro de comunicação ao submeter recurso.', tipo: 'erro' });
    } finally {
      setEnviandoRecurso(false);
    }
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
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          <button
            className="btn btn-outline"
            onClick={() => setMostrarDiretrizes(true)}
            style={{ minHeight: '36px', padding: '6px 10px', fontSize: '0.78rem', color: 'var(--color-vinho)' }}
            title="Diretrizes de Segurança da Comunidade (STF Tema 987)"
          >
            <BookOpen size={14} color="var(--color-vinho)" /> Regras
          </button>
          <button
            className="btn btn-outline"
            onClick={() => { setModalModeracoes(true); carregarMinhasModeracoes(); setMsgRecurso({ texto: '', tipo: '' }); }}
            style={{ minHeight: '36px', padding: '6px 10px', fontSize: '0.78rem', borderColor: 'var(--color-dourado)', color: 'var(--color-vinho)' }}
            title="Ver meus conteúdos moderados e recursos (Direito de Resposta STF)"
          >
            <Scale size={14} color="var(--color-dourado)" /> Meus Recursos
          </button>
          <button
            className="btn btn-outline"
            onClick={() => setMostrarQuestionario(true)}
            style={{ minHeight: '36px', padding: '6px 10px', fontSize: '0.78rem', borderColor: 'var(--color-dourado)', color: 'var(--color-vinho)' }}
            title="Personalizar comunidade conforme seus gostos"
          >
            <Sparkles size={14} color="var(--color-dourado)" /> {preferencias.experiencia ? 'Meus Gostos' : 'Questionário'}
          </button>
          <button
            className="btn btn-primary"
            onClick={() => { setMostrarNovoPost(!mostrarNovoPost); setErroModeracao(''); }}
            style={{ minHeight: '36px', padding: '6px 12px', fontSize: '0.78rem' }}
          >
            <Plus size={14} /> Publicar
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
                flex: '0 0 auto',
                flexShrink: 0,
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <h3 style={{ fontSize: '1rem', margin: 0, color: 'var(--color-vinho)' }}>Publicar em "{grupoSelecionado}"</h3>
            <span style={{ fontSize: '0.72rem', backgroundColor: 'var(--color-creme)', padding: '2px 8px', borderRadius: '4px', color: 'var(--color-vinho)' }}>
              🔒 Anonimato Protegido
            </span>
          </div>

          <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: '10px' }}>
            Seu nome real nunca é revelado. Você será identificada com um pseudônimo anônimo e seguro.
          </p>

          {/* Diretriz clínica visível na caixa de postagem */}
          <div style={{ backgroundColor: '#FFFBEB', border: '1px solid var(--color-dourado)', borderRadius: 'var(--radius-sm)', padding: '8px 12px', marginBottom: '12px', fontSize: '0.76rem', color: '#92400E', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={16} color="var(--color-dourado)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Aviso de Segurança (CFM / STF Tema 987):</strong> É terminantemente proibido indicar dosagens,
              medicamentos alopáticos ou receitas caseiras. Conteúdos médicos requerem avaliação do seu obstetra.
            </div>
          </div>

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
                    {formatDate(p.criado_em)}
                  </span>
                  <button
                    onClick={() => handleAbrirDenuncia(p.id)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center', gap: '3px' }}
                    title="Denunciar conteúdo com motivo estruturado à moderação"
                    aria-label="Denunciar postagem"
                  >
                    <Flag size={14} />
                    <span style={{ fontSize: '0.7rem' }}>Denunciar</span>
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
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                        <strong style={{ color: 'var(--color-vinho)', fontSize: '0.78rem' }}>{c.apelido}:</strong>
                        <button
                          onClick={() => handleAbrirDenuncia(null, c.id)}
                          style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: 0 }}
                          title="Denunciar comentário"
                        >
                          <Flag size={12} />
                        </button>
                      </div>
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

      {/* Modal: Diretrizes de Segurança da Comunidade (STF Tema 987 & CFM) */}
      {mostrarDiretrizes && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(34, 10, 16, 0.65)',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          zIndex: 9999, padding: '16px'
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: '560px', maxHeight: '90vh', overflowY: 'auto',
            backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-lg)', padding: '24px', position: 'relative'
          }}>
            <button
              onClick={() => setMostrarDiretrizes(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
              aria-label="Fechar"
            >
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Shield size={22} color="var(--color-vinho)" />
              <h3 style={{ margin: 0, fontSize: '1.15rem', color: 'var(--color-vinho)' }}>Diretrizes da Comunidade Segura</h3>
            </div>
            <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '16px' }}>
              Fundamentadas no Marco Civil da Internet (Lei 12.965/2014), decisão do STF no Tema 987 e Resoluções CFM/COFEN.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.84rem' }}>
              <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)', backgroundColor: '#FFFBEB' }}>
                <strong style={{ color: '#92400E' }}>1. Vedação Absoluta à Automedicação</strong>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-main)', fontSize: '0.8rem' }}>
                  É expressamente proibido sugerir doses, indicar medicamentos alopáticos ou substâncias de risco. Trocas de experiências não substituem o obstetra.
                </p>
              </div>

              <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                <strong style={{ color: 'var(--color-vinho)' }}>2. Anonimato Protetivo e Sigilo</strong>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-main)', fontSize: '0.8rem' }}>
                  Sua identidade real nunca é exibida. Nunca divulgue números de telefone, endereços ou dados pessoais identificáveis nas postagens.
                </p>
              </div>

              <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                <strong style={{ color: 'var(--color-vinho)' }}>3. Respeito Mútuo e Comunicação Empática</strong>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-main)', fontSize: '0.8rem' }}>
                  Não toleramos julgamentos estigmatizantes sobre ganho de peso, tipo de parto ou escolhas familiares. Qualquer assédio é removido.
                </p>
              </div>

              <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-creme)' }}>
                <strong style={{ color: 'var(--color-vinho)' }}>4. Direito de Recurso & Contraditório (STF Tema 987)</strong>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-main)', fontSize: '0.8rem' }}>
                  Caso uma publicação sua seja sinalizada ou ocultada, você tem o direito garantido de justificar o contexto e requerer revisão humana.
                </p>
              </div>

              <div style={{ border: '1px solid var(--color-border)', padding: '12px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-rosa-claro)' }}>
                <strong style={{ color: 'var(--color-vinho)' }}>5. Protocolo de Sofrimento Mental & Acolhimento (CVV 188)</strong>
                <p style={{ margin: '4px 0 0', color: 'var(--color-text-main)', fontSize: '0.8rem' }}>
                  Sinais de sofrimento agudo, depressão perinatal ou ideação ativam imediata rede de apoio emergencial humanizado e gratuito.
                </p>
              </div>
            </div>

            <div style={{ marginTop: '18px', textAlign: 'right' }}>
              <button className="btn btn-primary" onClick={() => setMostrarDiretrizes(false)} style={{ minHeight: '36px', padding: '6px 16px', fontSize: '0.82rem' }}>
                Entendi as Diretrizes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Denúncia Estruturada (STF Tema 987) */}
      {denunciaModal.aberto && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(34, 10, 16, 0.65)',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          zIndex: 9999, padding: '16px'
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: '520px', maxHeight: '90vh', overflowY: 'auto',
            backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-lg)', padding: '24px', position: 'relative'
          }}>
            <button
              onClick={() => setDenunciaModal({ aberto: false, postId: null, comentarioId: null })}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
              aria-label="Fechar"
            >
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Flag size={20} color="var(--color-vermelho)" />
              <h3 style={{ margin: 0, fontSize: '1.15rem', color: 'var(--color-vinho)' }}>Denunciar Conteúdo à Moderação</h3>
            </div>
            <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '16px' }}>
              Selecione o motivo da denúncia estruturada conforme as normas de segurança perinatal (STF Tema 987):
            </p>

            <form onSubmit={handleSubmeterDenuncia}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                {MOTIVOS_DENUNCIA.map((m) => (
                  <label
                    key={m.id}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: denunciaMotivo === m.id ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                      backgroundColor: denunciaMotivo === m.id ? 'var(--color-rosa-claro)' : '#FFFFFF',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '0.84rem' }}>
                      <input
                        type="radio"
                        name="motivo"
                        value={m.id}
                        checked={denunciaMotivo === m.id}
                        onChange={(e) => setDenunciaMotivo(e.target.value)}
                        style={{ width: 'auto !important' }}
                      />
                      <span>{m.label}</span>
                    </div>
                    <span style={{ fontSize: '0.74rem', color: 'var(--color-text-muted)', marginLeft: '22px' }}>
                      {m.desc}
                    </span>
                  </label>
                ))}
              </div>

              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.82rem', fontWeight: 600 }}>
                  Detalhes adicionais (opcional):
                </label>
                <textarea
                  className="form-control"
                  rows={2}
                  placeholder="Explique resumidamente o motivo da sinalização..."
                  value={denunciaDetalhes}
                  onChange={(e) => setDenunciaDetalhes(e.target.value)}
                  maxLength={500}
                  style={{ width: '100%', fontSize: '0.82rem' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{ flex: 1 }}
                  onClick={() => setDenunciaModal({ aberto: false, postId: null, comentarioId: null })}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 1, backgroundColor: 'var(--color-vermelho)', borderColor: 'var(--color-vermelho)' }}
                  disabled={enviandoDenuncia}
                >
                  {enviandoDenuncia ? 'Registrando...' : 'Confirmar Denúncia'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Protocolo de Acolhimento Imediato (CVV 188 / SAMU 192) */}
      {modalAcolhimentoCvv.aberto && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(34, 10, 16, 0.75)',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          zIndex: 10000, padding: '16px'
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: '520px', maxHeight: '90vh', overflowY: 'auto',
            backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-lg)', padding: '24px', position: 'relative',
            border: '2px solid var(--color-dourado)'
          }}>
            <button
              onClick={() => setModalAcolhimentoCvv({ aberto: false, dados: null })}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
              aria-label="Fechar"
            >
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '50%', backgroundColor: 'var(--color-rosa-claro)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <HeartHandshake size={24} color="var(--color-vinho)" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--color-vinho)' }}>Você não está sozinha</h3>
                <span style={{ fontSize: '0.78rem', color: 'var(--color-dourado)', fontWeight: 700 }}>
                  Protocolo Institucional de Apoio & Acolhimento
                </span>
              </div>
            </div>

            <p style={{ fontSize: '0.86rem', color: 'var(--color-text-main)', lineHeight: 1.5, marginBottom: '16px' }}>
              A gestação e o puerpério envolvem transformações hormonais e psicológicas intensas. Se você ou alguém que você conhece está enfrentando momentos de angústia, tristeza profunda ou exaustão, há apoio gratuito e sigiloso disponível agora mesmo.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '18px' }}>
              <a
                href="tel:188"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 16px',
                  backgroundColor: 'var(--color-vinho)',
                  color: '#FFFFFF',
                  borderRadius: 'var(--radius-sm)',
                  textDecoration: 'none',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>📞 Disque 188 — CVV (Gratuito)</div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.9 }}>Centro de Valorização da Vida • 24 horas por dia • Sigilo Absoluto</div>
                </div>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, backgroundColor: 'var(--color-dourado)', color: 'var(--color-vinho)', padding: '4px 10px', borderRadius: '12px' }}>
                  LIGAR AGORA
                </span>
              </a>

              <a
                href="tel:192"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  backgroundColor: '#FEF2F2',
                  border: '1.5px solid var(--color-vermelho)',
                  color: '#991B1B',
                  borderRadius: 'var(--radius-sm)',
                  textDecoration: 'none'
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>🚑 SAMU — Disque 192</div>
                  <div style={{ fontSize: '0.74rem' }}>Para situações de urgência médica ou risco físico imediato</div>
                </div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#991B1B' }}>
                  LIGAR 192
                </span>
              </a>

              <div style={{ padding: '10px 14px', backgroundColor: 'var(--color-creme)', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem', color: 'var(--color-vinho)' }}>
                🏥 <strong>Rede SUS:</strong> As unidades do CAPS (Centro de Atenção Psicossocial) e UPAs oferecem acolhimento psicológico multiprofissional presencial e gratuito.
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <button
                className="btn btn-outline"
                onClick={() => setModalAcolhimentoCvv({ aberto: false, dados: null })}
                style={{ minHeight: '36px', padding: '6px 16px', fontSize: '0.82rem' }}
              >
                Fechar Acolhimento
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Minhas Moderações & Recursos (STF Tema 987) */}
      {modalModeracoes && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(34, 10, 16, 0.65)',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          zIndex: 9999, padding: '16px'
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: '600px', maxHeight: '90vh', overflowY: 'auto',
            backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-lg)', padding: '24px', position: 'relative'
          }}>
            <button
              onClick={() => setModalModeracoes(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
              aria-label="Fechar"
            >
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Scale size={22} color="var(--color-vinho)" />
              <h3 style={{ margin: 0, fontSize: '1.15rem', color: 'var(--color-vinho)' }}>Minhas Moderações & Recursos</h3>
            </div>
            <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '16px' }}>
              Direito ao devido processo legal e contraditório de moderação digital (STF Tema 987 / Marco Civil da Internet):
            </p>

            {msgRecurso.texto && (
              <div style={{
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                marginBottom: '14px',
                fontSize: '0.82rem',
                backgroundColor: msgRecurso.tipo === 'sucesso' ? '#ECFDF5' : '#FEF2F2',
                color: msgRecurso.tipo === 'sucesso' ? '#065F46' : '#991B1B',
                border: `1px solid ${msgRecurso.tipo === 'sucesso' ? '#A7F3D0' : '#FECACA'}`
              }}>
                {msgRecurso.texto}
              </div>
            )}

            {carregandoModeracoes ? (
              <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', padding: '20px' }}>Carregando histórico de moderações...</p>
            ) : minhasModeracoes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px 20px', backgroundColor: 'var(--color-creme)', borderRadius: 'var(--radius-sm)' }}>
                <CheckCircle2 size={32} color="#059669" style={{ margin: '0 auto 8px', display: 'block' }} />
                <strong style={{ fontSize: '0.9rem', color: 'var(--color-vinho)' }}>Nenhuma publicação sua sofreu moderação</strong>
                <p className="text-muted" style={{ fontSize: '0.8rem', margin: '4px 0 0' }}>
                  Todas as suas postagens cumprem plenamente as Diretrizes de Segurança da Comunidade Nymphia.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '16px' }}>
                {minhasModeracoes.map((item) => (
                  <div key={item.id} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: item.ocultado ? 'var(--color-vermelho)' : '#D97706' }}>
                        {item.ocultado ? '🚫 Ocultado Preventivamente' : '⚠️ Sinalizado para Auditoria'}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                        {formatDate(item.criado_em)}
                      </span>
                    </div>

                    <p style={{ fontSize: '0.84rem', margin: '0 0 8px', color: 'var(--color-text-main)', fontStyle: 'italic' }}>
                      "{item.conteudo}"
                    </p>

                    <div style={{ fontSize: '0.76rem', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                      <strong>Motivo:</strong> {item.motivo_ocultacao || item.motivo_sinalizacao || 'Análise preventiva'}
                    </div>

                    {/* Situação do Recurso */}
                    {item.recurso_status ? (
                      <div style={{ backgroundColor: 'var(--color-creme)', padding: '8px 10px', borderRadius: '4px', fontSize: '0.78rem' }}>
                        <strong>Status do Recurso:</strong>{' '}
                        <span style={{ fontWeight: 700, textTransform: 'capitalize', color: item.recurso_status === 'deferido' ? '#059669' : item.recurso_status === 'indeferido' ? 'var(--color-vermelho)' : '#D97706' }}>
                          {item.recurso_status}
                        </span>
                        {item.recurso_decisao && (
                          <div style={{ marginTop: '4px' }}>
                            <em>Decisão clínica: {item.recurso_decisao}</em>
                          </div>
                        )}
                      </div>
                    ) : (
                      recursoForm.postId === item.id ? (
                        <form onSubmit={handleSubmeterRecurso} style={{ marginTop: '8px', borderTop: '1px dashed var(--color-border)', paddingTop: '8px' }}>
                          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, marginBottom: '4px' }}>
                            Justificativa do Recurso (STF Tema 987):
                          </label>
                          <textarea
                            className="form-control"
                            rows={3}
                            placeholder="Descreva o contexto da publicação e solicite reanálise humana..."
                            value={recursoForm.justificativa}
                            onChange={(e) => setRecursoForm({ ...recursoForm, justificativa: e.target.value })}
                            required
                            minLength={5}
                            style={{ width: '100%', fontSize: '0.8rem', marginBottom: '8px' }}
                          />
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button
                              type="button"
                              className="btn btn-outline"
                              onClick={() => setRecursoForm({ postId: null, justificativa: '' })}
                              style={{ flex: 1, minHeight: '30px', padding: '4px 8px', fontSize: '0.75rem' }}
                            >
                              Cancelar
                            </button>
                            <button
                              type="submit"
                              className="btn btn-primary"
                              disabled={enviandoRecurso}
                              style={{ flex: 1, minHeight: '30px', padding: '4px 8px', fontSize: '0.75rem' }}
                            >
                              {enviandoRecurso ? 'Submetendo...' : 'Enviar Recurso'}
                            </button>
                          </div>
                        </form>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-outline"
                          onClick={() => { setRecursoForm({ postId: item.id, justificativa: '' }); setMsgRecurso({ texto: '', tipo: '' }); }}
                          style={{ fontSize: '0.75rem', minHeight: '30px', padding: '4px 10px', borderColor: 'var(--color-dourado)', color: 'var(--color-vinho)' }}
                        >
                          <Scale size={13} /> Contestar / Submeter Recurso
                        </button>
                      )
                    )}
                  </div>
                ))}
              </div>
            )}

            <div style={{ textAlign: 'right' }}>
              <button className="btn btn-outline" onClick={() => setModalModeracoes(false)} style={{ minHeight: '36px', padding: '6px 16px', fontSize: '0.82rem' }}>
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

