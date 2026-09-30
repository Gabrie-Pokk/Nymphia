import React, { useState, useEffect, useRef } from 'react';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import VoiceSettingsModal from '../../components/VoiceSettingsModal';
import {
  Eye,
  Camera,
  RotateCcw,
  Volume2,
  VolumeX,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  Activity,
  Sparkles,
  Info,
  Maximize2,
  Sliders,
  RefreshCw,
  Award
} from 'lucide-react';
import {
  speakNymphia,
  stopNymphiaVoice,
  getVoicePreferences
} from '../../utils/voiceService';

export default function BodyVision({ onBack }) {
  const [modo, setModo] = useState('postura'); // postura | bascula | respiracao | alongamento
  const [cameraAtiva, setCameraAtiva] = useState(false);
  const [modoDemo, setModoDemo] = useState(false);
  const [vozAtiva, setVozAtiva] = useState(true);
  const [modalVozAberta, setModalVozAberta] = useState(false);
  const [carregandoIA, setCarregandoIA] = useState(false);
  const [erroCamera, setErroCamera] = useState(null);
  const [facingMode, setFacingMode] = useState('user'); // user | environment

  // Métricas do Biofeedback em Tempo Real
  const [posturaScore, setPosturaScore] = useState(95);
  const [inclinacaoGraus, setInclinacaoGraus] = useState(173);
  const [anguloPelvico, setAnguloPelvico] = useState(175);
  const [statusLombar, setStatusLombar] = useState('Segura'); // Segura | Atenção | Sobrecarga
  const [simetriaOmbros, setSimetriaOmbros] = useState('Alinhados'); // Alinhados | Desnível Leve
  const [feedbackMensagem, setFeedbackMensagem] = useState('Postura equilibrada e coluna lombar protegida.');
  const [repeticoes, setRepeticoes] = useState(0);
  const [progressoRepeticao, setProgressoRepeticao] = useState(0); // 0 a 100%
  const [faseExercicio, setFaseExercicio] = useState('Pronta para iniciar');
  const [faseRespiracao, setFaseRespiracao] = useState('inspirando'); // inspirando | expirando

  // Controles de Demonstração
  const [demoInclinacaoManual, setDemoInclinacaoManual] = useState(172);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const animFrameRef = useRef(null);
  const poseDetectorRef = useRef(null);
  const ultimoFeedbackFaladoRef = useRef(0);
  const smoothedLandmarksRef = useRef(null);
  const demoAngleRef = useRef(0);
  const particulasRef = useRef([]);

  // Estado da Máquina de Repetições da Báscula Pélvica
  const basculaStateRef = useRef({
    estagio: 'neutro', // neutro | anteversao | retroversao | pico
    holdTimer: 0,
    calibradoOffset: 0
  });

  const falarInstrucao = (texto, force = false) => {
    if (!vozAtiva) return;
    const agora = Date.now();
    if (!force && agora - ultimoFeedbackFaladoRef.current < 4000) return;
    ultimoFeedbackFaladoRef.current = agora;

    speakNymphia(texto, {
      onError: () => {}
    });
  };

  // Carregador robusto com múltiplos fallbacks de CDN para MediaPipe Pose
  const carregarMediaPipePose = async () => {
    if (window.Pose) return true;

    const cdns = [
      'https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/pose.js',
      'https://unpkg.com/@mediapipe/pose@0.5.1675469404/pose.js'
    ];

    for (const url of cdns) {
      try {
        await new Promise((resolve, reject) => {
          const script = document.createElement('script');
          script.src = url;
          script.crossOrigin = 'anonymous';
          script.onload = () => resolve();
          script.onerror = () => reject();
          document.body.appendChild(script);
        });
        if (window.Pose) return true;
      } catch (e) {}
    }
    return false;
  };

  // Iniciar Câmera Real
  const iniciarCamera = async (novoFacingMode = facingMode) => {
    setErroCamera(null);
    setCarregandoIA(true);
    setModoDemo(false);

    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: novoFacingMode,
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setCameraAtiva(true);
      falarInstrucao('Câmera conectada. A inteligência artificial está calibrando seu corpo em tempo real.', true);

      const ok = await carregarMediaPipePose();
      if (ok && window.Pose) {
        try {
          const pose = new window.Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/${file}`
          });
          pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            enableSegmentation: false,
            minDetectionConfidence: 0.55,
            minTrackingConfidence: 0.55
          });
          pose.onResults(processarPoseLandmarks);
          poseDetectorRef.current = pose;
        } catch (e) {}
      }

      iniciarLoopAnimacao(false);
    } catch (err) {
      setErroCamera(
        'Não foi possível acessar a câmera. Você pode usar o Modo Demonstração Interativo de alta fidelidade!'
      );
      setCameraAtiva(false);
    } finally {
      setCarregandoIA(false);
    }
  };

  const alternarCamera = () => {
    const proximo = facingMode === 'user' ? 'environment' : 'user';
    setFacingMode(proximo);
    iniciarCamera(proximo);
  };

  const iniciarDemo = () => {
    pararCamera();
    setModoDemo(true);
    setCameraAtiva(true);
    setErroCamera(null);
    falarInstrucao('Demonstração interativa iniciada. Veja os eixos e ângulos da inteligência artificial.', true);
    iniciarLoopAnimacao(true);
  };

  const pararCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    stopNymphiaVoice();
    setCameraAtiva(false);
    setModoDemo(false);
  };

  const calibrarPosturaBase = () => {
    basculaStateRef.current.calibradoOffset = 180 - inclinacaoGraus;
    falarInstrucao('Postura base calibrada. Agora a IA medirá seus movimentos a partir desta posição.', true);
  };

  useEffect(() => {
    return () => {
      pararCamera();
    };
  }, []);

  // FILTRO EMA (Exponential Moving Average) para eliminar tremulações da câmera
  const aplicarSuavizacaoEMA = (currentLandmarks) => {
    if (!smoothedLandmarksRef.current) {
      smoothedLandmarksRef.current = currentLandmarks.map((pt) => ({ ...pt }));
      return smoothedLandmarksRef.current;
    }

    const smoothed = smoothedLandmarksRef.current;
    const alpha = 0.28; // Coeficiente de estabilização

    for (let i = 0; i < currentLandmarks.length; i++) {
      if (currentLandmarks[i] && smoothed[i]) {
        smoothed[i].x = smoothed[i].x * (1 - alpha) + currentLandmarks[i].x * alpha;
        smoothed[i].y = smoothed[i].y * (1 - alpha) + currentLandmarks[i].y * alpha;
        smoothed[i].z = (smoothed[i].z || 0) * (1 - alpha) + (currentLandmarks[i].z || 0) * alpha;
      }
    }

    return smoothed;
  };

  // Dispara partículas visuais celebratórias no canvas ao concluir repetição
  const criarParticulas = (x, y) => {
    const novas = [];
    for (let i = 0; i < 24; i++) {
      novas.push({
        x,
        y,
        vx: (Math.random() - 0.5) * 8,
        vy: (Math.random() - 0.5) * 8,
        vida: 1.0,
        cor: i % 2 === 0 ? '#C9A84C' : '#C2185B'
      });
    }
    particulasRef.current = [...particulasRef.current, ...novas];
  };

  // Processa resultados do MediaPipe com Biofeedback Obstétrico Avançado
  const processarPoseLandmarks = (results) => {
    if (!canvasRef.current || !results.poseLandmarks) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    // Aplica estabilizador temporal
    const lm = aplicarSuavizacaoEMA(results.poseLandmarks);

    const nose = lm[0];
    const leftShoulder = lm[11];
    const rightShoulder = lm[12];
    const leftHip = lm[23];
    const rightHip = lm[24];
    const leftKnee = lm[25];
    const rightKnee = lm[26];

    if (!leftShoulder || !rightShoulder || !leftHip || !rightHip) return;

    // 1. Ponto Médio e Ângulo da Coluna Vertebral (Lordose)
    const midShoulder = {
      x: (leftShoulder.x + rightShoulder.x) / 2,
      y: (leftShoulder.y + rightShoulder.y) / 2
    };
    const midHip = {
      x: (leftHip.x + rightHip.x) / 2,
      y: (leftHip.y + rightHip.y) / 2
    };

    const dxSpine = midShoulder.x - midHip.x;
    const dySpine = midShoulder.y - midHip.y;
    const radSpine = Math.atan2(Math.abs(dxSpine), Math.abs(dySpine));
    const degSpine = Math.round(180 - (radSpine * 180) / Math.PI);
    setInclinacaoGraus(degSpine);

    // 2. Simetria dos Ombros (Nível Escapular)
    const diffOmbros = Math.abs(leftShoulder.y - rightShoulder.y);
    setSimetriaOmbros(diffOmbros < 0.035 ? 'Alinhados' : 'Desnível Leve');

    // 3. Ângulo da Báscula Pélvica (Tronco -> Bacia -> Joelhos)
    let degPelvis = 175;
    if (leftKnee && rightKnee) {
      const midKnee = {
        x: (leftKnee.x + rightKnee.x) / 2,
        y: (leftKnee.y + rightKnee.y) / 2
      };
      const v1 = { x: midShoulder.x - midHip.x, y: midShoulder.y - midHip.y };
      const v2 = { x: midKnee.x - midHip.x, y: midKnee.y - midHip.y };
      const dot = v1.x * v2.x + v1.y * v2.y;
      const mag1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y);
      const mag2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y);
      if (mag1 > 0 && mag2 > 0) {
        degPelvis = Math.round((Math.acos(Math.max(-1, Math.min(1, dot / (mag1 * mag2)))) * 180) / Math.PI);
      }
    }
    setAnguloPelvico(degPelvis);

    // 4. Lógica por Modo
    if (modo === 'postura') {
      const desvio = Math.abs(180 - degSpine);
      const score = Math.max(70, Math.min(99, Math.round(100 - desvio * 2.2 - diffOmbros * 120)));
      setPosturaScore(score);

      if (score >= 92) {
        setStatusLombar('Segura');
        setFeedbackMensagem('Excelente postura! A coluna lombar e o diafragma estão em posição equilibrada.');
      } else if (score >= 82) {
        setStatusLombar('Atenção');
        setFeedbackMensagem('Leve sobrecarga na lombar. Aproxime a bacia do encosto e relaxe os ombros.');
      } else {
        setStatusLombar('Sobrecarga');
        setFeedbackMensagem('Ajuste sua postura: incline o tronco 5° para trás para aliviar o peso na coluna.');
      }
    } else if (modo === 'bascula') {
      // Máquina de estados de repetição da báscula pélvica
      const state = basculaStateRef.current;
      const variacao = degPelvis - 175;

      if (variacao > 7 && state.estagio !== 'anteversao') {
        state.estagio = 'anteversao';
        setFaseExercicio('Inclinando a bacia para a frente (anteversão)');
        setProgressoRepeticao(50);
      } else if (variacao < -7 && state.estagio === 'anteversao') {
        state.estagio = 'retroversao';
        setFaseExercicio('Recolhendo suavemente o quadril (retroversão)');
        setProgressoRepeticao(90);
      } else if (Math.abs(variacao) < 4 && state.estagio === 'retroversao') {
        state.estagio = 'neutro';
        setFaseExercicio('Repetição concluída! Retorne à posição neutra');
        setProgressoRepeticao(100);
        setRepeticoes((prev) => {
          const novo = prev + 1;
          falarInstrucao(`Muito bem! Repetição ${novo} concluída com sucesso.`, true);
          criarParticulas(midHip.x * width, midHip.y * height);
          return novo;
        });
        setTimeout(() => setProgressoRepeticao(0), 600);
      }
    }

    // Desenha o Esqueleto e os Indicadores
    desenharOverlayBiomedico(ctx, lm, width, height, posturaScore, degSpine, midShoulder, midHip);
  };

  // Desenha os gráficos biomédicos sofisticados no Canvas
  const desenharOverlayBiomedico = (ctx, lm, width, height, score, degSpine, midShoulder, midHip) => {
    const toPx = (pt) => ({ x: pt.x * width, y: pt.y * height });

    // 1. Linha Vertical de Gravidade (Center of Gravity Guide)
    const pShoulder = toPx(midShoulder);
    ctx.beginPath();
    ctx.setLineDash([6, 6]);
    ctx.moveTo(pShoulder.x, 0);
    ctx.lineTo(pShoulder.x, height);
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.22)';
    ctx.stroke();
    ctx.setLineDash([]); // reset

    // 2. Conexões Anatômicas Principais
    const conexoes = [
      [11, 12], // ombros
      [11, 23], [12, 24], // tronco
      [23, 24], // pelve
      [11, 13], [13, 15], // braço esquerdo
      [12, 14], [14, 16], // braço direito
      [23, 25], [25, 27], // perna esquerda
      [24, 26], [26, 28]  // perna direita
    ];

    const corEixo = score >= 90 ? '#27AE60' : score >= 80 ? '#C9A84C' : '#C2185B';

    ctx.lineWidth = 4;
    ctx.strokeStyle = corEixo;
    ctx.lineCap = 'round';
    ctx.shadowBlur = 12;
    ctx.shadowColor = corEixo;

    conexoes.forEach(([i, j]) => {
      if (lm[i] && lm[j]) {
        const p1 = toPx(lm[i]);
        const p2 = toPx(lm[j]);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }
    });

    // 3. Eixo Central da Coluna & Curvatura Lombar
    const pHip = toPx(midHip);
    const pLumbar = {
      x: (pShoulder.x + pHip.x) / 2 + (180 - degSpine) * 2.2,
      y: (pShoulder.y + pHip.y) / 2
    };

    ctx.beginPath();
    ctx.moveTo(pShoulder.x, pShoulder.y);
    ctx.quadraticCurveTo(pLumbar.x, pLumbar.y, pHip.x, pHip.y);
    ctx.lineWidth = 6;
    ctx.strokeStyle = '#FFFFFF';
    ctx.shadowBlur = 16;
    ctx.shadowColor = '#C2185B';
    ctx.stroke();

    // 4. Arco Medidor de Graus na Região Lombar
    ctx.beginPath();
    ctx.arc(pLumbar.x, pLumbar.y, 28, -Math.PI / 2, -Math.PI / 2 + ((180 - degSpine) * Math.PI) / 90);
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#C9A84C';
    ctx.stroke();

    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.shadowColor = '#000000';
    ctx.shadowBlur = 4;
    ctx.fillText(`${degSpine}°`, pLumbar.x + 34, pLumbar.y + 4);

    // 5. Halo Suave no Abdômen / Útero Gestacional
    ctx.beginPath();
    ctx.arc(pLumbar.x - 22, pLumbar.y + 8, 44, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(253, 240, 242, 0.22)';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(201, 168, 76, 0.6)';
    ctx.stroke();

    // 6. Articulações com Anéis Duplos
    const articulações = [0, 11, 12, 13, 14, 23, 24, 25, 26];
    articulações.forEach((idx) => {
      if (lm[idx]) {
        const p = toPx(lm[idx]);
        ctx.beginPath();
        ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#FFFFFF';
        ctx.fill();

        ctx.beginPath();
        ctx.arc(p.x, p.y, 9, 0, Math.PI * 2);
        ctx.lineWidth = 2;
        ctx.strokeStyle = corEixo;
        ctx.stroke();
      }
    });

    // 7. Renderiza e atualiza partículas celebratórias
    if (particulasRef.current.length > 0) {
      particulasRef.current = particulasRef.current.filter((p) => p.vida > 0.05);
      particulasRef.current.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        p.vida *= 0.92;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4 * p.vida, 0, Math.PI * 2);
        ctx.fillStyle = p.cor;
        ctx.globalAlpha = p.vida;
        ctx.fill();
        ctx.globalAlpha = 1.0;
      });
    }

    ctx.shadowBlur = 0; // reset
  };

  // Loop de Renderização e Animação
  const iniciarLoopAnimacao = (isDemo = false) => {
    const loop = async () => {
      if (!canvasRef.current) return;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const width = canvas.width || 640;
      const height = canvas.height || 480;

      if (isDemo) {
        demoAngleRef.current += 0.035;
        const t = demoAngleRef.current;

        // Fundo com estética de scanner médico com gradiente
        ctx.fillStyle = '#160B10';
        ctx.fillRect(0, 0, width, height);

        // Grade geométrica biomédica sutil
        ctx.strokeStyle = 'rgba(194, 24, 91, 0.08)';
        ctx.lineWidth = 1;
        for (let x = 0; x < width; x += 36) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, height);
          ctx.stroke();
        }
        for (let y = 0; y < height; y += 36) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(width, y);
          ctx.stroke();
        }

        // Modelo Cinemático de Gestante
        const centerX = width / 2;
        const baseHeadY = 95;
        const breathOffset = Math.sin(t * 1.6) * 5;
        const tiltOffset = Math.sin(t * 0.9) * 18;

        const simHead = { x: centerX, y: baseHeadY };
        const simShoulderL = { x: centerX - 58, y: baseHeadY + 54 + breathOffset * 0.5 };
        const simShoulderR = { x: centerX + 58, y: baseHeadY + 54 + breathOffset * 0.5 };
        const simHipL = { x: centerX - 46 + tiltOffset * 0.3, y: baseHeadY + 185 };
        const simHipR = { x: centerX + 46 + tiltOffset * 0.3, y: baseHeadY + 185 };
        const simKneeL = { x: centerX - 52, y: baseHeadY + 295 };
        const simKneeR = { x: centerX + 52, y: baseHeadY + 295 };

        const demoLandmarks = {
          0: { x: simHead.x / width, y: simHead.y / height },
          11: { x: simShoulderL.x / width, y: simShoulderL.y / height },
          12: { x: simShoulderR.x / width, y: simShoulderR.y / height },
          23: { x: simHipL.x / width, y: simHipL.y / height },
          24: { x: simHipR.x / width, y: simHipR.y / height },
          25: { x: simKneeL.x / width, y: simKneeL.y / height },
          26: { x: simKneeR.x / width, y: simKneeR.y / height }
        };

        const midShoulder = {
          x: (simShoulderL.x + simShoulderR.x) / 2 / width,
          y: (simShoulderL.y + simShoulderR.y) / 2 / height
        };
        const midHip = {
          x: (simHipL.x + simHipR.x) / 2 / width,
          y: (simHipL.y + simHipR.y) / 2 / height
        };

        if (modo === 'postura') {
          const simDeg = Math.round(demoInclinacaoManual + Math.sin(t * 0.5) * 4);
          setInclinacaoGraus(simDeg);
          const score = Math.max(75, Math.min(99, Math.round(100 - Math.abs(180 - simDeg) * 2.5)));
          setPosturaScore(score);
          setStatusLombar(score >= 90 ? 'Segura' : score >= 80 ? 'Atenção' : 'Sobrecarga');
          setFeedbackMensagem(
            score >= 90
              ? 'Postura ideal! O centro de gravidade está equilibrado sobre os pés.'
              : 'Ajuste suave: incline o tronco levemente para trás para apoiar a lombar.'
          );
          desenharOverlayBiomedico(ctx, demoLandmarks, width, height, score, simDeg, midShoulder, midHip);
        } else if (modo === 'bascula') {
          const cycle = Math.sin(t * 1.3);
          const simPelvis = Math.round(175 + cycle * 12);
          setAnguloPelvico(simPelvis);

          if (cycle > 0.75 && basculaStateRef.current.estagio !== 'anteversao') {
            basculaStateRef.current.estagio = 'anteversao';
            setFaseExercicio('Inclinando a bacia para a frente (anteversão)');
            setProgressoRepeticao(50);
          } else if (cycle < -0.75 && basculaStateRef.current.estagio === 'anteversao') {
            basculaStateRef.current.estagio = 'retroversao';
            setFaseExercicio('Recolhendo o quadril (retroversão suave)');
            setProgressoRepeticao(90);
          } else if (Math.abs(cycle) < 0.25 && basculaStateRef.current.estagio === 'retroversao') {
            basculaStateRef.current.estagio = 'neutro';
            setFaseExercicio('Repetição concluída com excelência!');
            setProgressoRepeticao(100);
            setRepeticoes((prev) => {
              const novo = prev + 1;
              falarInstrucao(`Excelente! Repetição ${novo} finalizada.`, true);
              criarParticulas(width / 2, baseHeadY + 185);
              return novo;
            });
            setTimeout(() => setProgressoRepeticao(0), 500);
          }

          desenharOverlayBiomedico(ctx, demoLandmarks, width, height, 96, 172, midShoulder, midHip);
        } else if (modo === 'respiracao') {
          const bCycle = (Math.sin(t * 0.9) + 1) / 2;
          if (bCycle > 0.5) {
            setFaseRespiracao('inspirando');
            setFaseExercicio('Inspire pelo nariz expandindo a barriga calmamente');
          } else {
            setFaseRespiracao('expirando');
            setFaseExercicio('Solte o ar suavemente pela boca relaxando os ombros');
          }

          desenharOverlayBiomedico(ctx, demoLandmarks, width, height, 98, 175, midShoulder, midHip);

          // Anel respiratório biomórfico
          ctx.beginPath();
          ctx.arc(centerX, baseHeadY + 120, 50 + bCycle * 40, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(194, 24, 91, ${0.08 + bCycle * 0.16})`;
          ctx.fill();
          ctx.lineWidth = 3;
          ctx.strokeStyle = bCycle > 0.5 ? '#27AE60' : '#C2185B';
          ctx.shadowBlur = 16;
          ctx.shadowColor = '#C2185B';
          ctx.stroke();
          ctx.shadowBlur = 0;
        }

        // Overlay text
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.fillText('IA VISION • RASTREAMENTO CINEMÁTICO 60 FPS', 20, 30);
      } else {
        if (videoRef.current && poseDetectorRef.current && videoRef.current.readyState >= 2) {
          try {
            await poseDetectorRef.current.send({ image: videoRef.current });
          } catch (e) {}
        }
      }

      animFrameRef.current = requestAnimationFrame(loop);
    };

    animFrameRef.current = requestAnimationFrame(loop);
  };

  return (
    <div style={{ paddingBottom: '36px' }}>
      <BackButton onClick={onBack} label="Voltar para Início" />

      {/* Header com Controles de Voz & Visão */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-vinho)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <Eye size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--color-vinho)' }}>Visão Corporal & Postura IA</h2>
              <span className="badge-gold" style={{ fontSize: '0.68rem', padding: '2px 8px' }}>Tempo Real</span>
            </div>
            <p className="text-muted" style={{ fontSize: '0.8rem', margin: '2px 0 0 0' }}>
              Biofeedback postural, alívio lombar e exercícios guiados por visão computacional
            </p>
          </div>
        </div>

        {/* Controles de Áudio e Personalização da Voz */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={() => setModalVozAberta(true)}
            className="btn btn-outline"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 10px',
              fontSize: '0.75rem',
              borderRadius: 'var(--radius-full)',
              borderColor: 'var(--color-rosa)',
              color: 'var(--color-rosa)'
            }}
            title="Personalizar tom, velocidade e persona da voz da Nymphia"
          >
            <Sliders size={15} />
            <span>Voz IA</span>
          </button>

          <button
            onClick={() => {
              setVozAtiva(!vozAtiva);
              if (!vozAtiva) falarInstrucao('Voz da Nymphia ativada.', true);
              else stopNymphiaVoice();
            }}
            className="btn btn-outline"
            style={{ width: '38px', height: '38px', padding: 0, borderRadius: '50%' }}
            title={vozAtiva ? 'Silenciar voz' : 'Ativar voz'}
          >
            {vozAtiva ? <Volume2 size={18} color="var(--color-rosa)" /> : <VolumeX size={18} color="var(--color-text-muted)" />}
          </button>
        </div>
      </div>

      <TriageDisclaimer />

      {/* Seletor de Modo de Movimento / Exercício */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px', marginBottom: '14px' }}>
        {[
          { id: 'postura', label: '🧘 Alinhamento Lombar' },
          { id: 'bascula', label: '🤰 Báscula Pélvica' },
          { id: 'respiracao', label: '🌬️ Respiração & Diafragma' }
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => {
              setModo(item.id);
              setRepeticoes(0);
              setProgressoRepeticao(0);
              falarInstrucao(`Modo ${item.label.replace(/[^\w\s]/gi, '')} ativado.`);
            }}
            className={`btn ${modo === item.id ? 'btn-primary' : 'btn-outline'}`}
            style={{
              padding: '8px 16px',
              fontSize: '0.84rem',
              whiteSpace: 'nowrap',
              borderRadius: 'var(--radius-full)',
              fontWeight: modo === item.id ? 700 : 500
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Viewport Principal com Câmera e Canvas da IA */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '4 / 3',
          maxHeight: '440px',
          backgroundColor: '#160B10',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-md)',
          border: '2px solid var(--color-border)'
        }}
      >
        {/* Vídeo da Câmera Real */}
        <video
          ref={videoRef}
          playsInline
          muted
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: facingMode === 'user' ? 'scaleX(-1)' : 'none',
            display: cameraAtiva && !modoDemo ? 'block' : 'none'
          }}
        />

        {/* Canvas da Inteligência Artificial sobreposto */}
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            pointerEvents: 'none'
          }}
        />

        {/* Estado Desativado / Call to Action */}
        {!cameraAtiva && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
              textAlign: 'center',
              background: 'radial-gradient(circle at center, #2C141E 0%, #160B10 100%)',
              color: '#FFFFFF'
            }}
          >
            <div
              style={{
                width: '68px',
                height: '68px',
                borderRadius: '50%',
                backgroundColor: 'rgba(194, 24, 91, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '14px',
                border: '1.5px solid var(--color-rosa)',
                boxShadow: '0 0 20px rgba(194, 24, 91, 0.35)'
              }}
            >
              <Camera size={32} color="var(--color-rosa-claro)" />
            </div>

            <h3 style={{ fontSize: '1.2rem', color: '#FFFFFF', marginBottom: '6px' }}>
              Ative a Câmera ou Veja a Demonstração
            </h3>
            <p style={{ fontSize: '0.84rem', color: '#D4B2BB', maxWidth: '360px', lineHeight: 1.45, marginBottom: '20px' }}>
              A IA rastreia o alinhamento lombar, a báscula pélvica e a respiração em tempo real com alta precisão e sem tremores.
            </p>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
              <button
                onClick={() => iniciarCamera()}
                disabled={carregandoIA}
                className="btn btn-primary"
                style={{ padding: '10px 20px', fontSize: '0.88rem' }}
              >
                <Camera size={16} /> {carregandoIA ? 'Calibrando...' : 'Ligar Minha Câmera'}
              </button>

              <button
                onClick={iniciarDemo}
                className="btn btn-outline"
                style={{
                  padding: '10px 20px',
                  fontSize: '0.88rem',
                  borderColor: 'var(--color-dourado)',
                  color: 'var(--color-dourado)'
                }}
              >
                <Play size={16} /> Ver Demonstração Interativa
              </button>
            </div>

            {erroCamera && (
              <div
                style={{
                  marginTop: '14px',
                  padding: '8px 14px',
                  backgroundColor: 'rgba(192, 57, 43, 0.25)',
                  border: '1px solid var(--color-vermelho)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.78rem',
                  color: '#FFB8B8',
                  maxWidth: '400px'
                }}
              >
                {erroCamera}
              </div>
            )}
          </div>
        )}

        {/* HUD Superior quando Ativo */}
        {cameraAtiva && (
          <>
            <div
              style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                right: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                pointerEvents: 'none'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: 'rgba(22, 11, 16, 0.8)',
                  backdropFilter: 'blur(8px)',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#FFFFFF',
                  fontSize: '0.75rem',
                  fontWeight: 600
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: modoDemo ? '#C9A84C' : '#27AE60',
                    boxShadow: `0 0 10px ${modoDemo ? '#C9A84C' : '#27AE60'}`
                  }}
                />
                {modoDemo ? 'Modo Demonstração Interativo' : 'Rastreamento em Tempo Real'}
              </div>

              <div style={{ display: 'flex', gap: '6px', pointerEvents: 'auto' }}>
                {!modoDemo && (
                  <>
                    <button
                      onClick={alternarCamera}
                      className="btn btn-outline"
                      style={{
                        backgroundColor: 'rgba(22, 11, 16, 0.75)',
                        color: '#FFFFFF',
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        padding: '6px 10px',
                        fontSize: '0.72rem',
                        borderRadius: 'var(--radius-full)'
                      }}
                      title="Alternar entre câmera frontal e traseira"
                    >
                      <RefreshCw size={13} />
                    </button>

                    <button
                      onClick={calibrarPosturaBase}
                      className="btn btn-outline"
                      style={{
                        backgroundColor: 'rgba(22, 11, 16, 0.75)',
                        color: '#FFFFFF',
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        padding: '6px 10px',
                        fontSize: '0.72rem',
                        borderRadius: 'var(--radius-full)'
                      }}
                      title="Calibrar posição neutra da postura"
                    >
                      <RotateCcw size={13} /> Calibrar
                    </button>
                  </>
                )}

                <button
                  onClick={pararCamera}
                  className="btn btn-outline"
                  style={{
                    backgroundColor: 'rgba(22, 11, 16, 0.75)',
                    color: '#FFFFFF',
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    padding: '6px 12px',
                    fontSize: '0.72rem',
                    borderRadius: 'var(--radius-full)'
                  }}
                >
                  <Pause size={13} /> Pausar
                </button>
              </div>
            </div>

            {/* HUD Inferior com Métricas de Alta Precisão */}
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                left: '12px',
                right: '12px',
                backgroundColor: 'rgba(22, 11, 16, 0.85)',
                backdropFilter: 'blur(12px)',
                padding: '10px 16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid rgba(255, 255, 255, 0.16)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px'
              }}
            >
              <div>
                <span style={{ fontSize: '0.68rem', color: '#D4B2BB', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {modo === 'postura' && 'Score de Alinhamento'}
                  {modo === 'bascula' && 'Repetições da Báscula'}
                  {modo === 'respiracao' && 'Fase da Respiração'}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF' }}>
                    {modo === 'postura' && `${posturaScore}%`}
                    {modo === 'bascula' && `${repeticoes} repetições`}
                    {modo === 'respiracao' && (faseRespiracao === 'inspirando' ? 'Inspire 🌿' : 'Solte o ar 💨')}
                  </span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor:
                        statusLombar === 'Segura'
                          ? 'rgba(39, 174, 96, 0.25)'
                          : statusLombar === 'Atenção'
                          ? 'rgba(201, 168, 76, 0.25)'
                          : 'rgba(192, 57, 43, 0.25)',
                      color:
                        statusLombar === 'Segura'
                          ? '#4EFA92'
                          : statusLombar === 'Atenção'
                          ? '#FFDD80'
                          : '#FF8888',
                      fontWeight: 600
                    }}
                  >
                    Lombar: {statusLombar}
                  </span>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.68rem', color: '#D4B2BB' }}>Ângulo Lombar</span>
                <p style={{ margin: '2px 0 0 0', fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-dourado)' }}>
                  {inclinacaoGraus}°
                </p>
                <span style={{ fontSize: '0.66rem', color: '#B09098' }}>Ombros: {simetriaOmbros}</span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Controles de Simulação Interativa (Visível em Modo Demo) */}
      {modoDemo && (
        <div className="card" style={{ marginTop: '12px', padding: '14px', backgroundColor: '#FFFDFD' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '6px' }}>
            <span style={{ fontWeight: 600, color: 'var(--color-vinho)' }}>
              Simular Curvatura do Tronco / Pelve:
            </span>
            <span style={{ color: 'var(--color-rosa)', fontWeight: 700 }}>{demoInclinacaoManual}°</span>
          </div>
          <input
            type="range"
            min="155"
            max="185"
            value={demoInclinacaoManual}
            onChange={(e) => setDemoInclinacaoManual(parseInt(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--color-rosa)' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            <span>Hiperlordose (&lt;160°)</span>
            <span>Alinhamento Ideal (170°-175°)</span>
            <span>Projeção Posterior (&gt;180°)</span>
          </div>
        </div>
      )}

      {/* Card Dinâmico de Instrução & Biofeedback */}
      <div
        className="card"
        style={{
          marginTop: '14px',
          borderLeft: `5px solid ${statusLombar === 'Segura' ? '#27AE60' : statusLombar === 'Atenção' ? 'var(--color-dourado)' : 'var(--color-rosa)'}`,
          backgroundColor: '#FFF9FA'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
          <Sparkles size={20} color="var(--color-rosa)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ margin: 0, fontSize: '0.92rem', color: 'var(--color-vinho)' }}>
              Biofeedback Nymphia em Tempo Real
            </h4>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--color-text-main)', lineHeight: 1.45 }}>
              {feedbackMensagem}
            </p>
            {faseExercicio && (
              <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--color-rosa)', fontWeight: 600 }}>
                  💡 {faseExercicio}
                </span>
                {progressoRepeticao > 0 && modo === 'bascula' && (
                  <span className="badge-gold" style={{ fontSize: '0.66rem', padding: '1px 6px' }}>
                    {progressoRepeticao}%
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Orientações Clínicas e Privacidade */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '10px', marginTop: '14px' }}>
        <div className="card" style={{ padding: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <ShieldCheck size={18} color="#27AE60" />
            <h4 style={{ margin: 0, fontSize: '0.88rem', color: 'var(--color-vinho)' }}>
              Privacidade Absoluta (LGPD & On-Device Processing)
            </h4>
          </div>
          <p className="text-muted" style={{ fontSize: '0.8rem', margin: 0, lineHeight: 1.45 }}>
            O processamento dos pontos do seu corpo é executado <strong>estritamente dentro da memória do seu navegador</strong> via WebAssembly e GPU local. Nenhuma gravação, foto ou fluxo de vídeo é enviado para a nuvem.
          </p>
        </div>

        <div className="card" style={{ padding: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Info size={18} color="var(--color-rosa)" />
            <h4 style={{ margin: 0, fontSize: '0.88rem', color: 'var(--color-vinho)' }}>
              Recomendações da FEBRASGO para Movimento na Gravidez
            </h4>
          </div>
          <p className="text-muted" style={{ fontSize: '0.8rem', margin: 0, lineHeight: 1.45 }}>
            • <strong>Báscula Pélvica</strong>: Alivia o nervo ciático e previne a rigidez da sínfise púbica. Realize de 8 a 12 repetições lentas.<br />
            • <strong>Respiração Diafragmática</strong>: O útero empurra o diafragma para cima; respirar expandindo a barriga aumenta a oxigenação fetal e relaxa a musculatura paravertebral.
          </p>
        </div>
      </div>

      {/* Modal de Configuração de Voz */}
      <VoiceSettingsModal
        isOpen={modalVozAberta}
        onClose={() => setModalVozAberta(false)}
        onSaved={() => falarInstrucao('Preferências de voz atualizadas com sucesso.', true)}
      />
    </div>
  );
}
