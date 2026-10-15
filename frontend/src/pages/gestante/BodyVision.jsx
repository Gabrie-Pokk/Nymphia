import React, { useEffect, useRef, useState } from 'react';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import { apiFetch } from '../../utils/api';
import { speakNymphia, stopNymphiaVoice } from '../../utils/voiceService';
import { Activity, Camera, CameraOff, Phone, ShieldAlert, ShieldCheck, Volume2, VolumeX } from 'lucide-react';

// Guia de postura e movimento. O app NÃO mede o corpo.
// Até 15/10/2026 esta tela mostrava "nota de postura", ângulos, "desnível dos
// ombros em centímetros" e um modo demonstração com números simulados, nada
// disso validado. Agora são orientações em texto (e em voz), e a câmera, se a
// gestante quiser, funciona só como espelho: sem análise, sem gravação, sem envio.

const GUIAS = [
  {
    id: 'postura',
    titulo: 'Postura em pé',
    passos: [
      'Pés afastados na largura do quadril, com o peso dividido entre os dois pés.',
      'Joelhos levemente soltos, sem travar.',
      'Quadril em posição neutra: nem empinado para trás, nem encaixado demais.',
      'Ombros relaxados, para trás e para baixo, longe das orelhas.',
      'Cabeça alinhada, com o queixo paralelo ao chão e o olhar para a frente.',
      'Se precisar ficar muito tempo em pé, troque o apoio de um pé para o outro ou sente um pouco.'
    ]
  },
  {
    id: 'bascula',
    titulo: 'Báscula pélvica',
    passos: [
      'Fique em pé com as costas perto de uma parede, ou sentada numa cadeira firme, com os joelhos soltos.',
      'Ao soltar o ar, encaixe o quadril devagar, levando o cóccix para baixo e para a frente.',
      'Ao puxar o ar, volte devagar para a posição neutra, sem empinar.',
      'Repita algumas vezes, devagar, enquanto for confortável. Não deve doer.'
    ]
  },
  {
    id: 'respiracao',
    titulo: 'Respiração',
    passos: [
      'Sente-se com as costas apoiadas e os ombros soltos.',
      'Coloque uma mão no peito e a outra na lateral das costelas.',
      'Puxe o ar pelo nariz, devagar, sentindo as costelas abrirem para os lados.',
      'Solte o ar pela boca, mais devagar do que puxou.',
      'Continue por alguns minutos. Se ficar tonta, volte a respirar normalmente.'
    ]
  }
];

// Diretriz canadense de atividade física na gestação (Mottola et al., 2018), Quadro 2
const QUANDO_PARAR = [
  'Falta de ar forte que continua mesmo parada',
  'Dor forte no peito',
  'Contrações regulares e doloridas',
  'Sangramento vaginal',
  'Perda de líquido pela vagina',
  'Tontura ou desmaio que continua mesmo parada'
];

const DISPOSICOES = [
  { id: 'disposta', label: 'Disposta' },
  { id: 'leve_cansaco', label: 'Um pouco cansada' },
  { id: 'exausta', label: 'Exausta' }
];

const QUEIXAS = [
  { id: 'dor_lombar', label: 'Dor na lombar' },
  { id: 'dor_pelvica', label: 'Dor na bacia' },
  { id: 'ciatico', label: 'Dor que desce pela perna' },
  { id: 'pernas_inchadas', label: 'Pernas pesadas ou inchadas' },
  { id: 'azia', label: 'Azia' }
];

const SINAIS = [
  { id: 'sangramento', label: 'Sangramento vaginal' },
  { id: 'perda_liquido', label: 'Perda de líquido' },
  { id: 'contracoes', label: 'Contrações regulares e doloridas' },
  { id: 'tontura', label: 'Tontura forte ou falta de ar parada' }
];

function alternar(lista, id) {
  return lista.includes(id) ? lista.filter((x) => x !== id) : [...lista, id];
}

export default function BodyVision({ onBack }) {
  const [guiaAtual, setGuiaAtual] = useState('postura');
  const [falando, setFalando] = useState(false);

  const [disposicao, setDisposicao] = useState('disposta');
  const [queixas, setQueixas] = useState([]);
  const [sinais, setSinais] = useState([]);
  const [resultado, setResultado] = useState(null);
  const [avaliando, setAvaliando] = useState(false);
  const [erro, setErro] = useState('');

  const [espelhoAtivo, setEspelhoAtivo] = useState(false);
  const [erroCamera, setErroCamera] = useState('');
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const avaliar = async (d = disposicao, q = queixas, s = sinais) => {
    setAvaliando(true);
    setErro('');
    try {
      const res = await apiFetch('/antropometria/avaliar-movimento', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disposicao: d, queixas: q, sinais_alerta: s })
      });
      setResultado(res);
      if (!res.apta_exercicio) pararEspelho();
    } catch (e) {
      // Sem resposta do servidor: com sinal de alerta marcado, a orientação de segurança vale do mesmo jeito
      if (s.length > 0) {
        setResultado({
          apta_exercicio: false,
          mensagem_ia: 'Você marcou um sinal de alerta. Não faça exercício agora. Procure a maternidade ou ligue 192 (SAMU).'
        });
      } else {
        setErro(e.message || 'Não foi possível carregar as sugestões agora.');
      }
    } finally {
      setAvaliando(false);
    }
  };

  const pararEspelho = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setEspelhoAtivo(false);
  };

  const ligarEspelho = async () => {
    setErroCamera('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      streamRef.current = stream;
      setEspelhoAtivo(true);
      // O vídeo só existe depois do render
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      }, 0);
    } catch {
      setErroCamera('Não foi possível abrir a câmera. Você pode seguir o guia normalmente sem ela.');
    }
  };

  const ouvir = () => {
    if (falando) {
      stopNymphiaVoice();
      setFalando(false);
      return;
    }
    const guia = GUIAS.find((g) => g.id === guiaAtual);
    setFalando(true);
    speakNymphia(`${guia.titulo}. ${guia.passos.join(' ')}`, {
      onEnd: () => setFalando(false),
      onError: () => setFalando(false)
    });
  };

  useEffect(() => {
    avaliar('disposta', [], []);
    // Medidas do corpo que a versão antiga guardava neste aparelho
    try { localStorage.removeItem('nymphia_calibracao_postura'); } catch {}
    return () => {
      pararEspelho();
      stopNymphiaVoice();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const guia = GUIAS.find((g) => g.id === guiaAtual);
  const bloqueado = resultado && resultado.apta_exercicio === false;
  const orientacoes = (resultado?.orientacoes_especificas || []).filter((o) => !o.startsWith('Pare o exercício'));

  return (
    <div style={{ paddingBottom: '36px' }}>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <div style={{ width: '44px', height: '44px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-vinho)', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Activity size={24} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--color-vinho)' }}>Postura e movimento</h2>
          <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0' }}>
            Orientações e exercícios leves. O app não mede o seu corpo.
          </p>
        </div>
      </div>

      <TriageDisclaimer />

      {/* Como você está hoje */}
      <div className="card" style={{ borderLeft: `5px solid ${bloqueado ? '#C0392B' : '#27AE60'}` }}>
        <h3 style={{ marginTop: 0, fontSize: '1rem', color: 'var(--color-vinho)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          {bloqueado ? <ShieldAlert size={18} color="#C0392B" /> : <ShieldCheck size={18} color="#27AE60" />}
          Como você está hoje?
        </h3>

        <p style={{ fontSize: '0.82rem', fontWeight: 600, margin: '0 0 6px' }}>Energia</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '10px' }}>
          {DISPOSICOES.map((d) => (
            <button key={d.id} type="button" onClick={() => setDisposicao(d.id)}
              className={`btn ${disposicao === d.id ? 'btn-primary' : 'btn-outline'}`} style={{ fontSize: '0.78rem', padding: '8px 4px' }}>
              {d.label}
            </button>
          ))}
        </div>

        <p style={{ fontSize: '0.82rem', fontWeight: 600, margin: '0 0 6px' }}>Algum desconforto?</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
          {QUEIXAS.map((q) => (
            <button key={q.id} type="button" onClick={() => setQueixas(alternar(queixas, q.id))}
              className={`btn ${queixas.includes(q.id) ? 'btn-primary' : 'btn-outline'}`} style={{ fontSize: '0.76rem', padding: '6px 10px' }}>
              {q.label}
            </button>
          ))}
        </div>

        <fieldset style={{ border: '1px solid #FFD1D8', backgroundColor: '#FFF5F5', borderRadius: 'var(--radius-sm)', padding: '8px 10px', margin: '0 0 10px' }}>
          <legend style={{ fontSize: '0.8rem', fontWeight: 700, color: '#C0392B', padding: '0 4px' }}>Algum destes sinais agora?</legend>
          {SINAIS.map((s) => (
            <label key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#7E1D2D', cursor: 'pointer', marginBottom: '2px' }}>
              <input type="checkbox" checked={sinais.includes(s.id)} onChange={() => setSinais(alternar(sinais, s.id))} />
              <span>{s.label}</span>
            </label>
          ))}
        </fieldset>

        <button className="btn btn-primary" style={{ width: '100%' }} disabled={avaliando} onClick={() => avaliar()}>
          {avaliando ? 'Carregando...' : 'Ver sugestões para hoje'}
        </button>

        {erro && <p role="alert" style={{ color: '#922B21', fontSize: '0.82rem', marginBottom: 0 }}>{erro}</p>}

        {resultado && (
          <div style={{ marginTop: '12px', fontSize: '0.84rem', lineHeight: 1.45 }} role={bloqueado ? 'alert' : 'status'}>
            <p style={{ margin: '0 0 8px', fontWeight: bloqueado ? 700 : 400, color: bloqueado ? '#922B21' : 'var(--color-text)' }}>
              {resultado.mensagem_ia}
            </p>
            {bloqueado ? (
              <a href="tel:192" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', textDecoration: 'none', backgroundColor: '#C0392B' }}>
                <Phone size={18} /> Ligar 192 (SAMU)
              </a>
            ) : (
              <>
                {resultado.exercicios_permitidos?.length > 0 && (
                  <div style={{ backgroundColor: '#F0FAF4', padding: '8px 10px', borderRadius: 'var(--radius-sm)', marginBottom: '8px' }}>
                    <strong style={{ color: '#1E7A46', display: 'block', marginBottom: '4px' }}>Sugestões para hoje</strong>
                    <ul style={{ margin: 0, paddingLeft: '18px' }}>
                      {resultado.exercicios_permitidos.map((e) => (
                        <li key={e.id} style={{ marginBottom: '4px' }}>
                          <strong>{e.titulo}:</strong> {e.como_fazer} <span className="text-muted">({e.beneficio})</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {resultado.exercicios_proibidos?.length > 0 && (
                  <div style={{ backgroundColor: '#FFF0F2', padding: '8px 10px', borderRadius: 'var(--radius-sm)', marginBottom: '8px' }}>
                    <strong style={{ color: '#C0392B', display: 'block', marginBottom: '4px' }}>Melhor evitar hoje</strong>
                    <ul style={{ margin: 0, paddingLeft: '18px' }}>
                      {resultado.exercicios_proibidos.map((p, i) => <li key={i}>{p}</li>)}
                    </ul>
                  </div>
                )}
                {orientacoes.length > 0 && (
                  <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--color-text-muted)' }}>
                    {orientacoes.map((o, i) => <li key={i}>{o}</li>)}
                  </ul>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Guias passo a passo */}
      {!bloqueado && (
        <div className="card">
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '6px', marginBottom: '8px' }}>
            {GUIAS.map((g) => (
              <button key={g.id} type="button"
                onClick={() => { stopNymphiaVoice(); setFalando(false); setGuiaAtual(g.id); }}
                className={`btn ${guiaAtual === g.id ? 'btn-primary' : 'btn-outline'}`}
                style={{ flex: '0 0 auto', padding: '8px 14px', fontSize: '0.84rem', borderRadius: 'var(--radius-full)' }}>
                {g.titulo}
              </button>
            ))}
          </div>

          <ol style={{ margin: '0 0 10px', paddingLeft: '20px', fontSize: '0.88rem', lineHeight: 1.5 }}>
            {guia.passos.map((p, i) => <li key={i} style={{ marginBottom: '4px' }}>{p}</li>)}
          </ol>

          <button type="button" className="btn btn-outline" onClick={ouvir} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {falando ? <VolumeX size={16} /> : <Volume2 size={16} />}
            {falando ? 'Parar a voz' : 'Ouvir os passos'}
          </button>
        </div>
      )}

      {/* Espelho opcional */}
      {!bloqueado && (
        <div className="card">
          <h3 style={{ marginTop: 0, fontSize: '1rem', color: 'var(--color-vinho)' }}>Câmera como espelho (opcional)</h3>
          <p className="text-muted" style={{ fontSize: '0.8rem' }}>
            Para você se ver enquanto segue os passos. A imagem aparece só na sua tela: nada é gravado, analisado ou enviado.
          </p>
          {espelhoAtivo ? (
            <>
              <div style={{ position: 'relative', borderRadius: 'var(--radius-md)', overflow: 'hidden', backgroundColor: '#000' }}>
                <video ref={videoRef} playsInline muted style={{ width: '100%', display: 'block', transform: 'scaleX(-1)' }} />
                {/* Linha de referência no centro, só visual */}
                <div aria-hidden="true" style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: '2px', backgroundColor: 'rgba(255,255,255,0.55)' }} />
              </div>
              <button type="button" className="btn btn-secondary" style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={pararEspelho}>
                <CameraOff size={16} /> Desligar a câmera
              </button>
            </>
          ) : (
            <button type="button" className="btn btn-outline" style={{ display: 'flex', alignItems: 'center', gap: '6px' }} onClick={ligarEspelho}>
              <Camera size={16} /> Ligar a câmera
            </button>
          )}
          {erroCamera && <p style={{ color: '#922B21', fontSize: '0.8rem', marginBottom: 0 }}>{erroCamera}</p>}
        </div>
      )}

      {/* Quando parar */}
      <div className="card" style={{ borderLeft: '5px solid #C0392B' }}>
        <h3 style={{ marginTop: 0, fontSize: '1rem', color: '#922B21' }}>Pare e procure atendimento se tiver</h3>
        <ul style={{ margin: '0 0 6px', paddingLeft: '18px', fontSize: '0.84rem', lineHeight: 1.5 }}>
          {QUANDO_PARAR.map((s) => <li key={s}>{s}</li>)}
        </ul>
        <p className="text-muted" style={{ fontSize: '0.72rem', margin: 0 }}>
          Fonte: diretriz canadense de atividade física na gestação (Mottola et al., Br J Sports Med, 2018).
          Em caso de dúvida, fale com sua equipe de pré-natal.
        </p>
      </div>
    </div>
  );
}
