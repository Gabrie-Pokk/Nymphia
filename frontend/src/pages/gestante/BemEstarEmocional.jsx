import React, { useEffect, useState } from 'react';
import BackButton from '../../components/BackButton';
import { apiFetch } from '../../utils/api';
import { Phone } from 'lucide-react';

// Triagem emocional com a Escala de Edimburgo (EPDS). O texto das perguntas vem
// do servidor (arquivo licenciado fornecido pela equipe); sem ele, a página
// avisa que o questionário ainda não está disponível.

const ESTILO_NIVEL = {
  urgente: { cor: '#922B21', fundo: '#FDEDEC', rotulo: 'Precisa de cuidado agora' },
  atencao: { cor: '#9A5B00', fundo: '#FFF6E5', rotulo: 'Vale conversar com a equipe' },
  sem_sinais: { cor: '#1E7A46', fundo: '#EAF7EF', rotulo: 'Sem sinais de atenção' }
};

const dataCurta = (iso) => new Date(iso).toLocaleDateString('pt-BR');

function Contatos({ contatos }) {
  if (!contatos?.length) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', margin: '12px 0' }}>
      {contatos.map((c) => (
        <a
          key={c.telefone}
          href={`tel:${c.telefone}`}
          className="btn btn-primary"
          style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px', textDecoration: 'none', padding: '10px 12px' }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
            <Phone size={18} /> Ligar {c.telefone} ({c.sigla})
          </span>
          <span style={{ fontWeight: 400, fontSize: '0.76rem' }}>{c.nome}, {c.quando}</span>
        </a>
      ))}
    </div>
  );
}

export default function BemEstarEmocional({ onBack }) {
  const [questionario, setQuestionario] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [etapa, setEtapa] = useState('inicio'); // inicio | perguntas | resultado
  const [atual, setAtual] = useState(0);
  const [respostas, setRespostas] = useState([]);
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState(null);

  const carregarHistorico = () =>
    apiFetch('/epds/minhas').then((h) => setHistorico(Array.isArray(h) ? h : [])).catch(() => {});

  useEffect(() => {
    apiFetch('/epds/questionario')
      .then((q) => setQuestionario(q))
      .catch((e) => setErro(e.message || 'Não foi possível abrir o questionário.'))
      .finally(() => setCarregando(false));
    carregarHistorico();
  }, []);

  const comecar = () => {
    setRespostas(Array(questionario.itens.length).fill(null));
    setAtual(0);
    setResultado(null);
    setErro('');
    setEtapa('perguntas');
  };

  const escolher = (indice) => {
    setRespostas((r) => r.map((v, i) => (i === atual ? indice : v)));
  };

  const enviar = async () => {
    setEnviando(true);
    setErro('');
    try {
      const res = await apiFetch('/epds/respostas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ respostas })
      });
      setResultado(res);
      setEtapa('resultado');
      carregarHistorico();
    } catch (e) {
      setErro(e.message || 'Não foi possível salvar as respostas.');
    } finally {
      setEnviando(false);
    }
  };

  if (carregando) {
    return (
      <div>
        <BackButton onClick={onBack} label="Voltar para Início" />
        <p className="text-muted">Carregando...</p>
      </div>
    );
  }

  if (!questionario?.disponivel) {
    return (
      <div>
        <BackButton onClick={onBack} label="Voltar para Início" />
        <h2>Como você tem se sentido</h2>
        <div className="card">
          <p style={{ margin: 0 }}>
            Este questionário ainda não está disponível no app. Se você não está se sentindo bem, converse com sua
            equipe de pré-natal. Para conversar com alguém agora, o CVV atende no <a href="tel:188">188</a>, de graça,
            24 horas.
          </p>
        </div>
        {erro && <p role="alert" style={{ color: '#922B21' }}>{erro}</p>}
      </div>
    );
  }

  const item = questionario.itens[atual];
  const ultimo = atual === questionario.itens.length - 1;

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />
      <h2>Como você tem se sentido</h2>

      {erro && (
        <div role="alert" style={{ padding: '10px 12px', backgroundColor: '#FDEEE9', color: '#8A2B1A', borderRadius: 'var(--radius-sm)', marginBottom: '12px' }}>
          {erro}
        </div>
      )}

      {etapa === 'inicio' && (
        <div className="card">
          {questionario.instrucao && <p style={{ marginTop: 0 }}>{questionario.instrucao}</p>}
          <p className="text-muted" style={{ fontSize: '0.84rem' }}>
            São {questionario.itens.length} perguntas. Não existe resposta certa ou errada. As respostas ficam no seu
            histórico e aparecem para o profissional com quem você tem vínculo no app.
          </p>
          <p className="text-muted" style={{ fontSize: '0.8rem' }}>{questionario.aviso}</p>
          <button className="btn btn-primary" onClick={comecar} style={{ width: '100%' }}>Começar</button>
        </div>
      )}

      {etapa === 'perguntas' && item && (
        <div className="card">
          <p className="text-muted" style={{ fontSize: '0.78rem', margin: '0 0 6px' }}>
            Pergunta {atual + 1} de {questionario.itens.length}
          </p>
          <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
            <legend style={{ fontWeight: 600, marginBottom: '10px', color: 'var(--color-vinho)' }}>{item.texto}</legend>
            {item.opcoes.map((opcao, indice) => (
              <label
                key={indice}
                style={{
                  display: 'flex', gap: '10px', alignItems: 'center', padding: '10px 12px', marginBottom: '8px',
                  borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                  border: `1.5px solid ${respostas[atual] === indice ? 'var(--color-rosa)' : 'var(--color-border)'}`,
                  backgroundColor: respostas[atual] === indice ? '#FFF5F7' : '#FFFFFF'
                }}
              >
                <input
                  type="radio"
                  name={`epds-${item.numero}`}
                  checked={respostas[atual] === indice}
                  onChange={() => escolher(indice)}
                />
                <span>{opcao}</span>
              </label>
            ))}
          </fieldset>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'space-between', marginTop: '8px' }}>
            <button className="btn btn-secondary" onClick={() => (atual === 0 ? setEtapa('inicio') : setAtual(atual - 1))}>
              Voltar
            </button>
            {ultimo ? (
              <button className="btn btn-primary" disabled={respostas[atual] === null || enviando} onClick={enviar}>
                {enviando ? 'Enviando...' : 'Ver resultado'}
              </button>
            ) : (
              <button className="btn btn-primary" disabled={respostas[atual] === null} onClick={() => setAtual(atual + 1)}>
                Próxima
              </button>
            )}
          </div>
        </div>
      )}

      {etapa === 'resultado' && resultado && (
        <div
          className="card"
          role={resultado.nivel === 'urgente' ? 'alert' : 'status'}
          style={{ borderLeft: `4px solid ${ESTILO_NIVEL[resultado.nivel].cor}`, backgroundColor: ESTILO_NIVEL[resultado.nivel].fundo }}
        >
          <h3 style={{ marginTop: 0, color: ESTILO_NIVEL[resultado.nivel].cor }}>{resultado.titulo}</h3>
          <p>{resultado.mensagem}</p>
          <Contatos contatos={resultado.contatos} />
          {resultado.nivel !== 'sem_sinais' && (
            <p style={{ fontSize: '0.84rem' }}>
              {resultado.equipe_vinculada
                ? 'Este resultado aparece no painel do profissional com quem você tem vínculo no app.'
                : 'Mostre este resultado para sua equipe de pré-natal na próxima consulta, ou antes, se puder.'}
            </p>
          )}
          <p className="text-muted" style={{ fontSize: '0.78rem', marginBottom: 0 }}>{resultado.aviso}</p>
        </div>
      )}

      {etapa !== 'perguntas' && historico.length > 0 && (
        <div className="card" style={{ marginTop: '14px' }}>
          <h3 style={{ marginTop: 0, fontSize: '1rem' }}>Suas respostas anteriores</h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {historico.map((h) => (
              <li key={h.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--color-border)', fontSize: '0.86rem' }}>
                <span>{dataCurta(h.data_hora)}{h.semana_gestacional != null ? `, ${h.semana_gestacional}ª semana` : ''}</span>
                <span style={{ color: ESTILO_NIVEL[h.nivel]?.cor, fontWeight: 600 }}>{ESTILO_NIVEL[h.nivel]?.rotulo}</span>
              </li>
            ))}
          </ul>
          {etapa === 'inicio' ? null : (
            <button className="btn btn-secondary" style={{ marginTop: '10px' }} onClick={() => setEtapa('inicio')}>
              Responder de novo
            </button>
          )}
        </div>
      )}

      {questionario.referencia && (
        <p className="text-muted" style={{ fontSize: '0.72rem', marginTop: '12px' }}>
          {questionario.referencia}. {questionario.versao}.
        </p>
      )}
    </div>
  );
}
