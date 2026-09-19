import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { Sparkles, Heart, Coffee, Moon, Music, CheckCircle2, UserCheck, ShieldAlert, Award } from 'lucide-react';

export default function QuizGostos({ onBack }) {
  const { user, authHeaders } = useAuth();
  const isParceiro = user?.perfil === 'parceiro';

  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [sucesso, setSucesso] = useState('');
  const [erro, setErro] = useState('');
  const [infoRespondente, setInfoRespondente] = useState(null);

  const [respostas, setRespostas] = useState({
    desejo_estranho: '',
    repulsa_cheiro: '',
    comida_conforto: '',
    bebida_favorita: '',
    mimo_rapido: '',
    trilha_sonora: '',
    aroma_ambiente: '',
    temperatura_quarto: '',
    clima_parto: '',
    frase_proibida: '',
    frase_superpoder: '',
    momento_bebe: '',
    saudade_pre_gravidez: '',
    estilo_enxoval: ''
  });

  useEffect(() => {
    const endpoint = isParceiro ? '/parceiro/quiz-gostos' : '/quiz-gostos';
    fetch(endpoint, { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.preenchido) {
          setRespostas((prev) => ({ ...prev, ...data.respostas }));
          setInfoRespondente({
            respondido_por: data.respondido_por,
            nome_respondente: data.nome_respondente,
            atualizado_em: data.atualizado_em
          });
        }
      })
      .catch(() => {})
      .finally(() => setCarregando(false));
  }, []);

  const handleChange = (campo, valor) => {
    setRespostas((prev) => ({ ...prev, [campo]: valor }));
  };

  const handleSalvar = async (e) => {
    e.preventDefault();
    setSalvando(true);
    setSucesso('');
    setErro('');

    const endpoint = isParceiro ? '/parceiro/quiz-gostos' : '/quiz-gostos';
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          respostas,
          respondido_por: isParceiro ? 'parceiro' : 'gestante',
          nome_respondente: user?.nome
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Falha ao salvar o quiz.');

      setSucesso(isParceiro ? 'Quiz respondido com muito carinho pelo parceiro!' : 'Seus gostos e mimos foram salvos com sucesso!');
      setInfoRespondente({
        respondido_por: isParceiro ? 'parceiro' : 'gestante',
        nome_respondente: user?.nome,
        atualizado_em: new Date().toISOString()
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setErro(err.message);
    } finally {
      setSalvando(false);
    }
  };

  if (carregando) {
    return <div style={{ padding: '32px', textAlign: 'center' }}>Carregando quiz de mimos...</div>;
  }

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto', paddingBottom: '60px' }}>
      <BackButton onClick={onBack} label="Voltar para o Início" />

      {/* Header do Quiz */}
      <div className="card card-vinho" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span className="badge-gold">Opcional & Afetivo</span>
          {isParceiro && <span className="badge-rosa" style={{ backgroundColor: '#FFFFFF', color: 'var(--color-vinho)' }}>Modo Parceiro</span>}
        </div>
        <h2 style={{ fontSize: '1.4rem', color: '#FFFFFF', margin: '4px 0 8px 0' }}>
          Quiz dos Gostos, Desejos & Mimos da Gestante 🌸
        </h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--color-rosa-claro)', margin: 0 }}>
          {isParceiro
            ? "Mostre o quanto você conhece a sua parceira! Você pode preencher este quiz com as vontades e gostos dela para garantir que ela receba os melhores mimos."
            : "Um espaço divertido e acolhedor para registrar seus gostos, manias, vontades e como você ama ser cuidada. O seu parceiro também pode preencher ou consultar quando quiser te surpreender!"}
        </p>
      </div>

      {/* Status de preenchimento */}
      {infoRespondente && (
        <div className="card" style={{ backgroundColor: '#FDF0F2', border: '1px solid var(--color-rosa)', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <UserCheck size={24} color="var(--color-vinho)" />
          <div>
            <strong style={{ display: 'block', fontSize: '0.88rem', color: 'var(--color-vinho)' }}>
              {infoRespondente.respondido_por === 'parceiro' ? 'Respondido pelo Parceiro com Amor' : 'Preenchido pela Gestante'}
            </strong>
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
              Por {infoRespondente.nome_respondente} em {new Date(infoRespondente.atualizado_em).toLocaleDateString('pt-BR')}
            </span>
          </div>
        </div>
      )}

      {sucesso && (
        <div role="status" style={{ padding: '14px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-md)', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={20} /> {sucesso}
        </div>
      )}

      {erro && (
        <div role="alert" style={{ padding: '14px', backgroundColor: '#FDEDEC', color: '#C0392B', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
          {erro}
        </div>
      )}

      <form onSubmit={handleSalvar}>
        {/* SEÇÃO 1: Paladar & Desejos */}
        <div className="card" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-vinho)', marginBottom: '14px' }}>
            <Sparkles size={20} color="var(--color-rosa)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>1. Desejos & Paladar Gestacional</h3>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              Qual o desejo mais inusitado ou repentino até agora?
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: Melancia com queijo, pipoca com mostarda, brigadeiro de madrugada..."
              value={respostas.desejo_estranho}
              onChange={(e) => handleChange('desejo_estranho', e.target.value)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              O que ela NÃO suporta nem sentir o cheiro atualmente? (Repulsa)
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: Alho refogando, café passado, perfume forte, fritura..."
              value={respostas.repulsa_cheiro}
              onChange={(e) => handleChange('repulsa_cheiro', e.target.value)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              A comida sagrada de conforto para os dias difíceis:
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: Macarrão com queijo, sopinha da vovó, açaí, chocolate..."
              value={respostas.comida_conforto}
              onChange={(e) => handleChange('comida_conforto', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              A bebida favorita para se manter hidratada:
            </label>
            <select
              className="form-control"
              value={respostas.bebida_favorita}
              onChange={(e) => handleChange('bebida_favorita', e.target.value)}
            >
              <option value="">Selecione uma opção...</option>
              <option value="Água de coco geladinha">Água de coco bem geladinha</option>
              <option value="Água com gás e rodelas de limão">Água com gás e rodelas de limão</option>
              <option value="Suco natural de maracujá">Suco de maracujá calmante</option>
              <option value="Chá gelado seguro (camomila/frutas)">Chá suave e refrescante</option>
              <option value="Água mineral trincando de gelada">Água mineral purinha e gelada</option>
            </select>
          </div>
        </div>

        {/* SEÇÃO 2: Mimos & Relaxamento */}
        <div className="card" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-vinho)', marginBottom: '14px' }}>
            <Heart size={20} color="var(--color-rosa)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>2. Mimos, Massagens & Acalento</h3>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              O gesto de carinho que melhora o humor dela em 5 minutos:
            </label>
            <select
              className="form-control"
              value={respostas.mimo_rapido}
              onChange={(e) => handleChange('mimo_rapido', e.target.value)}
            >
              <option value="">Selecione...</option>
              <option value="Massagem nos pés e panturrilha">Massagem nos pés e panturrilhas</option>
              <option value="Cafuné no cabelo até pegar no sono">Cafuné no cabelo com calma</option>
              <option value="Trazer um lanchinho surpresa na cama">Trazer um lanche surpresa sem ela pedir</option>
              <option value="Um abraço longo, apertado e silencioso">Um abraço bem longo e acolhedor</option>
              <option value="Assumir a louça e as tarefas da casa">Assumir as tarefas da casa para ela descansar</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              Trilha sonora para acalmar a mamãe e o bebê:
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: MPB acústica, sons de chuva, clássica, louvores, pop suave..."
              value={respostas.trilha_sonora}
              onChange={(e) => handleChange('trilha_sonora', e.target.value)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              Aroma do quarto ou ambiente preferido:
            </label>
            <select
              className="form-control"
              value={respostas.aroma_ambiente}
              onChange={(e) => handleChange('aroma_ambiente', e.target.value)}
            >
              <option value="">Selecione...</option>
              <option value="Lavanda suave e calmante">Lavanda suave e relaxante</option>
              <option value="Cheirinho de banho tomado e limpeza">Cheirinho de banho tomado / limpeza</option>
              <option value="Sem aroma nenhum (olfato tá sensível)">Sem aroma nenhum (olfato hiper sensível)</option>
              <option value="Camomila ou erva-doce">Camomila ou erva-doce</option>
            </select>
          </div>

          <div className="form-group">
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              Posição favorita para o sono dos sonhos:
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: Deitada para a esquerda abraçada no travesseirão de corpo..."
              value={respostas.temperatura_quarto}
              onChange={(e) => handleChange('temperatura_quarto', e.target.value)}
            />
          </div>
        </div>

        {/* SEÇÃO 3: O Parto & Apoio */}
        <div className="card" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-vinho)', marginBottom: '14px' }}>
            <Award size={20} color="var(--color-vinho)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>3. O Grande Dia & Palavras de Poder</h3>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              Como ela idealiza o ambiente do parto:
            </label>
            <select
              className="form-control"
              value={respostas.clima_parto}
              onChange={(e) => handleChange('clima_parto', e.target.value)}
            >
              <option value="">Selecione...</option>
              <option value="Meia-luz, música suave e muito silêncio acolhedor">Meia-luz, playlist suave e silêncio acolhedor</option>
              <option value="O mais prático, rápido e seguro possível">O mais prático, rápido e seguro possível</option>
              <option value="Parceiro segurando a mão o tempo todo sem soltar">Parceiro segurando a mão o tempo todo</option>
              <option value="Banho morno, bola de pilates e liberdade">Banho morno, bola de pilates e liberdade</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              A frase que NINGUÉM deve dizer durante uma contração ou cansaço:
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: 'Calma, nem deve doer tanto', 'Você tá muito nervosa', 'Falta muito?'..."
              value={respostas.frase_proibida}
              onChange={(e) => handleChange('frase_proibida', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              A frase que dá superpoderes e acalma o coração:
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: 'Você é a mulher mais forte do mundo', 'Estou 100% aqui com você'..."
              value={respostas.frase_superpoder}
              onChange={(e) => handleChange('frase_superpoder', e.target.value)}
            />
          </div>
        </div>

        {/* SEÇÃO 4: Curiosidades & Vida Real */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-vinho)', marginBottom: '14px' }}>
            <Moon size={20} color="var(--color-rosa)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>4. Curiosidades da Gestação</h3>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              A maior saudade divertida da rotina pré-gravidez:
            </label>
            <input
              type="text"
              className="form-control"
              placeholder="Ex: Dormir de bruços, tomar baldes de café, não fazer xixi a cada 15 min..."
              value={respostas.saudade_pre_gravidez}
              onChange={(e) => handleChange('saudade_pre_gravidez', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '6px' }}>
              Estilo e vibe do quartinho / enxoval:
            </label>
            <select
              className="form-control"
              value={respostas.estilo_enxoval}
              onChange={(e) => handleChange('estilo_enxoval', e.target.value)}
            >
              <option value="">Selecione...</option>
              <option value="Minimalista e prático">Minimalista, elegante e super funcional</option>
              <option value="Delicado, clássico e temático">Delicado, romântico e cheio de detalhes</option>
              <option value="Boho chic com tons neutros e terrosos">Boho chic com tons neutros e madeira</option>
              <option value="Colorido, divertido e cheio de vida">Colorido, lúdico e vibrante</option>
            </select>
          </div>
        </div>

        {/* Botão de Envio */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ flex: 1, minHeight: '48px', fontSize: '0.95rem' }}
            disabled={salvando}
          >
            {salvando ? 'Guardando com carinho...' : (isParceiro ? 'Salvar Quiz pelo Parceiro 💖' : 'Salvar Meus Gostos e Mimos 🌸')}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onBack}
            style={{ minWidth: '90px' }}
          >
            Voltar
          </button>
        </div>
      </form>
    </div>
  );
}
