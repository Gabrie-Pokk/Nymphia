import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import { Heart, Activity, Radio, Play, Square, Volume2, VolumeX, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function CintaNymphia({ onBack, onNavigateEmergency }) {
  const { authHeaders } = useAuth();
  const [monitorando, setMonitorando] = useState(true);
  const [bpmAtual, setBpmAtual] = useState(138);
  const [statusFhr, setStatusFhr] = useState('normal'); // normal | bradicardia | taquicardia
  const [historicoBpm, setHistoricoBpm] = useState([136, 138, 140, 137, 139, 142, 138, 135, 138, 141, 139, 138]);
  const [somHabilitado, setSomHabilitado] = useState(false);
  const audioContextRef = useRef(null);

  // Efeito de Telemetria Contínua Doppler (Simulador V3 2027)
  useEffect(() => {
    let interval;
    if (monitorando) {
      interval = setInterval(async () => {
        try {
          const res = await fetch('/cinta/simulador');
          if (res.ok) {
            const data = await res.json();
            setBpmAtual(data.bpm);
            setStatusFhr(data.status);
            setHistoricoBpm((prev) => [...prev.slice(-24), data.bpm]);

            // Grava leitura contínua no backend
            fetch('/cinta/telemetria', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', ...authHeaders() },
              body: JSON.stringify({ bpm: data.bpm })
            }).catch(() => {});

            // Emite som de batimento Doppler se ativado
            if (somHabilitado) {
              playDopplerBeat();
            }
          }
        } catch (e) {}
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [monitorando, somHabilitado]);

  const playDopplerBeat = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(140, ctx.currentTime);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } catch (e) {}
  };

  const isAnormal = statusFhr !== 'normal';

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2>Cinta Nymphia — Monitor Doppler</h2>
          <p className="text-muted" style={{ fontSize: '0.82rem' }}>
            Transdutores contínuos de batimento cardíaco fetal (FHR) • Roadmap 2027
          </p>
        </div>
        <span className="badge-gold">V3 Wearable</span>
      </div>

      {/* Cartão de Leitura Contínua */}
      <div
        className="card card-vinho"
        style={{
          textAlign: 'center',
          padding: '24px 16px',
          borderLeft: isAnormal ? '6px solid var(--color-vermelho)' : '6px solid var(--color-dourado)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--color-rosa-claro)' }}>
            <Radio size={16} className={monitorando ? 'animate-pulse' : ''} />
            <span>Sinal do Transdutor: <strong>Excelente (4/4)</strong></span>
          </div>
          <span
            style={{
              backgroundColor: isAnormal ? 'var(--color-vermelho)' : 'rgba(255, 255, 255, 0.2)',
              color: '#FFFFFF',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase'
            }}
          >
            {statusFhr}
          </span>
        </div>

        {/* Mostrador Principal do FHR */}
        <div style={{ margin: '16px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
            <Heart
              size={48}
              color="var(--color-rosa)"
              style={{
                animation: monitorando ? 'heartbeat 0.8s infinite ease-in-out' : 'none'
              }}
            />
            <span style={{ fontSize: '3.6rem', fontWeight: 900, lineHeight: 1, letterSpacing: '-0.02em' }}>
              {bpmAtual}
            </span>
            <span style={{ fontSize: '1.2rem', color: 'var(--color-rosa-claro)', fontWeight: 600 }}>bpm</span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--color-rosa-claro)', marginTop: '6px' }}>
            Faixa fisiológica de referência: 110 a 160 bpm
          </p>
        </div>

        {/* Gráfico do Traçado Cardiotocográfico (SVG Waveform) */}
        <div
          style={{
            backgroundColor: 'rgba(0, 0, 0, 0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 8px',
            marginTop: '16px',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--color-rosa-claro)', marginBottom: '4px' }}>
            <span>160 bpm (Limite Superior)</span>
            <span>Variabilidade Batimento a Batimento</span>
            <span>110 bpm (Limite Inferior)</span>
          </div>
          <svg viewBox="0 0 240 60" style={{ width: '100%', height: '60px', overflow: 'visible' }}>
            {/* Linhas de referência superior e inferior */}
            <line x1="0" y1="12" x2="240" y2="12" stroke="rgba(255, 255, 255, 0.3)" strokeDasharray="3 3" />
            <line x1="0" y1="48" x2="240" y2="48" stroke="rgba(255, 255, 255, 0.3)" strokeDasharray="3 3" />

            {/* Linha do traçado em tempo real */}
            <polyline
              fill="none"
              stroke="var(--color-dourado)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={historicoBpm
                .map((val, idx) => {
                  const x = (idx / (historicoBpm.length - 1)) * 240;
                  // Mapeia 100-170 bpm para 55-5 y
                  const y = 55 - ((val - 100) / 70) * 50;
                  return `${x},${y}`;
                })
                .join(' ')}
            />
          </svg>
        </div>

        {/* Controles do Monitor */}
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button
            className="btn"
            style={{
              flex: 1,
              backgroundColor: monitorando ? 'rgba(255, 255, 255, 0.15)' : 'var(--color-rosa)',
              color: '#FFFFFF'
            }}
            onClick={() => setMonitorando(!monitorando)}
          >
            {monitorando ? <Square size={16} /> : <Play size={16} />}
            {monitorando ? 'Pausar Telemetria' : 'Iniciar Monitor'}
          </button>

          <button
            className="btn btn-outline"
            style={{ color: '#FFFFFF', borderColor: 'rgba(255, 255, 255, 0.3)' }}
            onClick={() => setSomHabilitado(!somHabilitado)}
            aria-label={somHabilitado ? 'Desativar áudio Doppler' : 'Ativar áudio Doppler'}
          >
            {somHabilitado ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
        </div>
      </div>

      {/* Alerta por Padrão Anormal */}
      {isAnormal && (
        <div
          role="alert"
          style={{
            padding: '16px',
            backgroundColor: '#FDEDEC',
            border: '2px solid var(--color-vermelho)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '20px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-vermelho)', marginBottom: '6px' }}>
            <AlertTriangle size={20} />
            <strong style={{ fontSize: '1rem' }}>Padrão Fetal Atípico Detectado ({statusFhr})</strong>
          </div>
          <p style={{ fontSize: '0.88rem', color: 'var(--color-text-main)', marginBottom: '12px' }}>
            A frequência cardíaca fetal sustentada fora da faixa de 110-160 bpm requer avaliação clínica imediata.
          </p>
          <button
            className="btn"
            style={{ backgroundColor: 'var(--color-vermelho)', color: '#FFFFFF', width: '100%' }}
            onClick={onNavigateEmergency}
          >
            Abrir Canal de Emergência SAMU 192
          </button>
        </div>
      )}

      {/* Explicação Técnica do Wearable */}
      <div className="card">
        <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Sobre a Tecnologia da Cinta Nymphia</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
          A Cinta Nymphia utiliza microtransdutores de ultrassom Doppler contínuo integrados a um tecido elástico biomédico hipoalergênico. O sinal é processado por algoritmos de filtragem de ruído materno e transmitido via Bluetooth Low Energy (BLE) com criptografia ponta-a-ponta.
        </p>
      </div>

      <TriageDisclaimer />

      <style>{`
        @keyframes heartbeat {
          0% { transform: scale(1); }
          15% { transform: scale(1.15); }
          30% { transform: scale(1); }
          45% { transform: scale(1.1); }
          60% { transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
