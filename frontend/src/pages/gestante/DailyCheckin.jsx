import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import { AlertTriangle, CheckCircle, Plus, Minus, Send, Brain, Sparkles } from 'lucide-react';

const HUMORES = [
  { nivel: 1, emoji: '😫', label: 'Muito Mal' },
  { nivel: 2, emoji: '🙁', label: 'Indisposta' },
  { nivel: 3, emoji: '😐', label: 'Regular' },
  { nivel: 4, emoji: '🙂', label: 'Bem' },
  { nivel: 5, emoji: '🥰', label: 'Excelente' }
];

const SINTOMAS_DISPONIVEIS = [
  'Náusea / Enjoo',
  'Azia / Queimação',
  'Dor de cabeça',
  'Inchaço nas pernas',
  'Visão embaçada',
  'Dor nas costas',
  'Dor no estômago',
  'Cólicas leves',
  'Cansaço excessivo',
  'Sangramento vaginal',
  'Perda de líquido'
];

export default function DailyCheckin({ onBack }) {
  const { authHeaders } = useAuth();
  const [humor, setHumor] = useState(4);
  const [descricao, setDescricao] = useState('');
  const [sintomas, setSintomas] = useState([]);
  const [movimentosBebe, setMovimentosBebe] = useState(6);
  const [semanaGestacional, setSemanaGestacional] = useState(24);
  const [carregando, setCarregando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [erro, setErro] = useState('');

  const carregarHistorico = () => {
    fetch('/checkin/historico?limite=10', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setHistorico(data))
      .catch(() => {});
  };

  useEffect(() => {
    carregarHistorico();

    // Carrega semana gestacional calculada do perfil clínico
    fetch('/perfil-clinico', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : null))
      .then((perfil) => {
        if (perfil && perfil.dum) {
          const d = new Date(perfil.dum + 'T12:00:00');
          const agora = new Date();
          const dias = Math.floor((agora - d) / (1000 * 60 * 60 * 24));
          const semanas = Math.max(1, Math.min(42, Math.floor(dias / 7)));
          setSemanaGestacional(semanas);
        }
      })
      .catch(() => {});
  }, []);

  const toggleSintoma = (s) => {
    if (sintomas.includes(s)) {
      setSintomas(sintomas.filter((item) => item !== s));
    } else {
      setSintomas([...sintomas, s]);
    }
  };

  const handleSalvarCheckin = async (e) => {
    e.preventDefault();
    setErro('');
    setResultado(null);
    setCarregando(true);

    try {
      const res = await fetch('/checkin/registrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          humor,
          descricao,
          sintomas,
          movimentos_bebe: movimentosBebe,
          semana_gestacional: semanaGestacional
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao registrar check-in.');
      }

      setResultado(data);
      setDescricao('');
      setSintomas([]);
      carregarHistorico();
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h2>Check-in Diário de Bem-Estar</h2>
        <span className="badge-rosa" style={{ fontSize: '0.8rem' }}>Semana {semanaGestacional}</span>
      </div>
      <p className="text-muted" style={{ marginBottom: '20px' }}>
        Seu momento de escuta e cuidado: registre como você e seu bebê estão hoje.
      </p>

      {/* FEEDBACK DE RESULTADO APÓS REGISTRAR */}
      {resultado && (
        <div
          role="alert"
          style={{
            padding: '16px',
            borderRadius: 'var(--radius-lg)',
            marginBottom: '24px',
            backgroundColor: (resultado.alerta_sintoma_fisico && resultado.alerta_sintoma_fisico.length > 0) ? '#FDEDEC' : '#EAF7EF',
            border: (resultado.alerta_sintoma_fisico && resultado.alerta_sintoma_fisico.length > 0) ? '2px solid var(--color-vermelho)' : '1px solid #27AE60'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            {(resultado.alerta_sintoma_fisico && resultado.alerta_sintoma_fisico.length > 0) ? (
              <AlertTriangle size={24} color="var(--color-vermelho)" />
            ) : (
              <CheckCircle size={24} color="#27AE60" />
            )}
            <h3
              style={{
                fontSize: '1.05rem',
                margin: 0,
                color: (resultado.alerta_sintoma_fisico && resultado.alerta_sintoma_fisico.length > 0) ? 'var(--color-vermelho)' : '#1E7E34'
              }}
            >
              {(resultado.alerta_sintoma_fisico && resultado.alerta_sintoma_fisico.length > 0) ? "Orientação Médica de Cuidado" : "Check-in Registrado com Sucesso"}
            </h3>
          </div>
          <p style={{ fontSize: '0.92rem', color: '#2C181E', lineHeight: 1.4, margin: '0 0 10px 0' }}>
            {resultado.recomendacao}
          </p>

          {/* Acolhimento Emocional Positivo */}
          <div style={{ background: 'rgba(255,255,255,0.85)', padding: '10px 14px', borderRadius: 8, fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="var(--color-rosa)" />
            <span style={{ color: 'var(--color-vinho)', fontWeight: 600 }}>
              🌸 Seu relato foi acolhido com carinho e guardado no seu histórico de bem-estar.
            </span>
          </div>
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

      <form onSubmit={handleSalvarCheckin} className="card">
        {/* 1. Humor do Dia */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 600, color: 'var(--color-vinho)', marginBottom: '10px' }}>
            Como você está se sentindo hoje?
          </label>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
            {HUMORES.map((h) => {
              const selecionado = humor === h.nivel;
              return (
                <button
                  key={h.nivel}
                  type="button"
                  onClick={() => setHumor(h.nivel)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '10px 4px',
                    borderRadius: 'var(--radius-md)',
                    border: selecionado ? '2px solid var(--color-vinho)' : '1px solid var(--color-border)',
                    backgroundColor: selecionado ? 'var(--color-rosa-claro)' : '#FFFFFF',
                    cursor: 'pointer',
                    minHeight: '64px'
                  }}
                  aria-pressed={selecionado}
                >
                  <span style={{ fontSize: '1.5rem', marginBottom: '4px' }}>{h.emoji}</span>
                  <span style={{ fontSize: '0.72rem', fontWeight: selecionado ? 700 : 400, color: selecionado ? 'var(--color-vinho)' : 'var(--color-text-muted)' }}>
                    {h.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. Sintomas Físicos */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 600, color: 'var(--color-vinho)', marginBottom: '8px' }}>
            Algum sintoma físico hoje? (Selecione todos os que sentir)
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {SINTOMAS_DISPONIVEIS.map((s) => {
              const selecionado = sintomas.includes(s);
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => toggleSintoma(s)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    backgroundColor: selecionado ? 'var(--color-rosa)' : '#FFFFFF',
                    color: selecionado ? '#FFFFFF' : 'var(--color-text-main)',
                    border: selecionado ? '1px solid var(--color-rosa)' : '1px solid var(--color-border)',
                    cursor: 'pointer',
                    minHeight: '38px'
                  }}
                >
                  {s}
                </button>
              );
            })}
          </div>
        </div>

                {/* 3. Acompanhamento de Movimentos Fetais (Baseado na Idade Gestacional) */}
        {semanaGestacional >= 20 ? (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: 600, color: 'var(--color-vinho)', marginBottom: '4px' }}>
              Movimentos do bebê sentidos hoje:
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setMovimentosBebe(Math.max(0, movimentosBebe - 1))}
                aria-label="Diminuir contador de movimentos"
                style={{ minHeight: '44px', minWidth: '44px' }}
              >
                <Minus size={18} />
              </button>
              <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--color-vinho)', minWidth: '40px', textAlign: 'center' }}>
                {movimentosBebe}
              </span>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setMovimentosBebe(Math.min(150, movimentosBebe + 1))}
                aria-label="Aumentar contador de movimentos"
                style={{ minHeight: '44px', minWidth: '44px' }}
              >
                <Plus size={18} />
              </button>
              <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                (No 3º trimestre, o ideal é notar pelo menos 6 movimentos por hora após as refeições)
              </span>
            </div>
          </div>
        ) : (
          <div style={{
            marginBottom: '20px',
            padding: '12px 16px',
            backgroundColor: 'var(--color-rosa-claro)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            fontSize: '0.84rem',
            color: 'var(--color-text-main)',
            lineHeight: 1.45
          }}>
            <strong style={{ color: 'var(--color-vinho)', display: 'block', marginBottom: '2px' }}>
              🍼 Movimentos Fetais (Semana {semanaGestacional}):
            </strong>
            A percepção consistente dos movimentos do bebê inicia-se clinicamente entre a 20ª e a 24ª semana de gestação. Nesta fase anterior, é absolutamente normal e esperado não sentir chutes diários.
          </div>
        )}

        {/* 4. Descrição Livre */}
        <div className="form-group" style={{ marginBottom: '20px' }}>
          <label htmlFor="checkin-desc">
            Descreva com suas palavras como você está:
          </label>
          <textarea
            id="checkin-desc"
            className="form-control"
            rows={3}
            maxLength={1500}
            placeholder="Ex: Estou me sentindo bem, mas um pouco ansiosa e com dor de cabeça leve..."
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            style={{ resize: 'vertical' }}
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'block', marginTop: '4px', textAlign: 'right' }}>{descricao.length}/1500 caracteres</span>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px' }}
          disabled={carregando}
        >
          {carregando ? 'Processando Modelos Neurais...' : 'Salvar Check-in e Analisar com IA'}
          <Send size={18} />
        </button>
      </form>

      {/* Histórico Recente de Check-ins */}
      <h3 style={{ marginTop: '28px', marginBottom: '12px' }}>Histórico dos Últimos Check-ins</h3>
      {historico.length === 0 ? (
        <p className="text-muted">Nenhum registro anterior encontrado.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {historico.map((h) => (
            <div key={h.id} className="card" style={{ padding: '14px', margin: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontWeight: 700, color: 'var(--color-vinho)', fontSize: '0.88rem' }}>
                  {new Date(h.data_hora).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}
                </span>
                <span className="badge-gold">Humor {h.humor}/5</span>
              </div>
              {h.descricao && (
                <p style={{ fontSize: '0.88rem', color: 'var(--color-text-main)', marginBottom: '6px' }}>
                  "{h.descricao}"
                </p>
              )}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                {h.sintomas && h.sintomas.map((s, idx) => (
                  <span key={idx} className="badge-rosa" style={{ fontSize: '0.72rem' }}>{s}</span>
                ))}
                {h.alerta_sintoma_fisico && h.alerta_sintoma_fisico.length > 0 && (
                  <span style={{ backgroundColor: '#FDEEE9', color: '#C0392B', padding: '3px 8px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700 }}>
                    ⚠️ {h.alerta_sintoma_fisico.join(', ')}
                  </span>
                )}
                {/* Visualização da classificação neural BERTimbau no histórico */}
                {h.categorias_bertimbau && Object.entries(h.categorias_bertimbau).some(([_, p]) => p >= 0.4) && (
                  <span style={{ background: '#F4EAE6', color: '#5C1A2A', padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <Brain size={12} />
                    {Object.entries(h.categorias_bertimbau)
                      .filter(([_, p]) => p >= 0.4)
                      .map(([cat]) => cat.replace(/_/g, ' '))
                      .join(', ')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <TriageDisclaimer />
    </div>
  );
}
