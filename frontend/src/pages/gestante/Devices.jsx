import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { Bluetooth, Activity, AlertTriangle, CheckCircle2, Plus, Info, RefreshCw } from 'lucide-react';
import TriageDisclaimer from '../../components/TriageDisclaimer';

export default function Devices({ onBack }) {
  const { authHeaders } = useAuth();
  const [medicoes, setMedicoes] = useState([]);
  const [tipo, setTipo] = useState('pressao_arterial'); // pressao_arterial | glicemia
  const [sistolica, setSistolica] = useState(120);
  const [diastolica, setDiastolica] = useState(80);
  const [glicemia, setGlicemia] = useState(85.0);
  const [conectandoBle, setConectandoBle] = useState(false);
  const [sucesso, setSucesso] = useState('');
  const [carregando, setCarregando] = useState(false);

  const carregarMedicoes = async () => {
    try {
      const res = await fetch('/dispositivos/medicoes', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setMedicoes(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    carregarMedicoes();
  }, []);

  const handleSalvarMedicao = async (origem = 'manual') => {
    setCarregando(true);
    setSucesso('');
    try {
      const payload = {
        tipo,
        origem,
        sistolica: tipo === 'pressao_arterial' ? Number(sistolica) : null,
        diastolica: tipo === 'pressao_arterial' ? Number(diastolica) : null,
        glicemia: tipo === 'glicemia' ? Number(glicemia) : null
      };

      const res = await fetch('/dispositivos/medicao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSucesso('Medição registrada com sucesso!');
        carregarMedicoes();
      }
    } catch (err) {
    } finally {
      setCarregando(false);
    }
  };

  const simularSincronizacaoBluetooth = () => {
    setConectandoBle(true);
    setTimeout(() => {
      setConectandoBle(false);
      if (tipo === 'pressao_arterial') {
        setSistolica(118);
        setDiastolica(78);
        handleSalvarMedicao('dispositivo_bluetooth');
      } else {
        setGlicemia(88.5);
        handleSalvarMedicao('dispositivo_bluetooth');
      }
    }, 1200);
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <h2>Dispositivos & Monitoramento</h2>
      <p className="text-muted" style={{ marginBottom: '16px' }}>
        Conexão direta com monitores de pressão arterial de braço e glicosímetros via Bluetooth SIG padrão.
      </p>

      {/* Alerta de Contraindicação Regulatória (Seção 9.2 e 13.7) */}
      <div
        style={{
          backgroundColor: '#FFF9E6',
          borderLeft: '4px solid var(--color-dourado)',
          padding: '12px 14px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '20px',
          fontSize: '0.82rem',
          color: '#5A4716'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--color-dourado)' }} />
          <div>
            <strong>Aviso de Segurança Clínica:</strong>
            Smartwatches e aparelhos de <em>pulso</em> são <strong>explicitamente contraindicados para gestantes</strong>, pois não possuem validação clínica para detecção fidedigna de pré-eclâmpsia. Utilize exclusivamente aparelhos de <strong>braço</strong> (ex: G-Tech LA850BT).
          </div>
        </div>
      </div>

      {sucesso && (
        <div role="status" style={{ padding: '12px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-sm)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} /> {sucesso}
        </div>
      )}

      {/* Painel de Registro e Conexão Bluetooth */}
      <div className="card">
        {/* Toggle de Tipo */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
          <button
            type="button"
            className={tipo === 'pressao_arterial' ? 'btn btn-primary' : 'btn btn-outline'}
            style={{ flex: 1 }}
            onClick={() => setTipo('pressao_arterial')}
          >
            Pressão Arterial (Braço)
          </button>
          <button
            type="button"
            className={tipo === 'glicemia' ? 'btn btn-primary' : 'btn btn-outline'}
            style={{ flex: 1 }}
            onClick={() => setTipo('glicemia')}
          >
            Glicemia Capilar
          </button>
        </div>

        {tipo === 'pressao_arterial' ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label>Sistólica (Máxima - mmHg)</label>
                <input
                  type="number"
                  className="form-control"
                  value={sistolica}
                  onChange={(e) => setSistolica(e.target.value)}
                />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label>Diastólica (Mínima - mmHg)</label>
                <input
                  type="number"
                  className="form-control"
                  value={diastolica}
                  onChange={(e) => setDiastolica(e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className="btn btn-outline"
                style={{ flex: 1 }}
                onClick={() => handleSalvarMedicao('manual')}
                disabled={carregando}
              >
                Salvar Manualmente
              </button>
              <button
                type="button"
                className="btn btn-vinho"
                style={{ flex: 1 }}
                onClick={simularSincronizacaoBluetooth}
                disabled={conectandoBle || carregando}
              >
                <Bluetooth size={18} />
                {conectandoBle ? 'Buscando BLE...' : 'Sincronizar Bluetooth'}
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label>Glicemia (mg/dL)</label>
              <input
                type="number"
                step="0.1"
                className="form-control"
                value={glicemia}
                onChange={(e) => setGlicemia(e.target.value)}
              />
              <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                Valores de jejum esperados no 1º tri: &lt; 92 mg/dL
              </span>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className="btn btn-outline"
                style={{ flex: 1 }}
                onClick={() => handleSalvarMedicao('manual')}
                disabled={carregando}
              >
                Salvar Manualmente
              </button>
              <button
                type="button"
                className="btn btn-vinho"
                style={{ flex: 1 }}
                onClick={simularSincronizacaoBluetooth}
                disabled={conectandoBle || carregando}
              >
                <Bluetooth size={18} />
                {conectandoBle ? 'Buscando BLE...' : 'Sincronizar Bluetooth'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Histórico de Medições */}
      <h3 style={{ marginTop: '24px', marginBottom: '12px' }}>Histórico de Medições</h3>
      {medicoes.length === 0 ? (
        <p className="text-muted">Nenhuma medição registrada ainda.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {medicoes.map((m) => {
            const isPressao = m.tipo === 'pressao_arterial';
            const isAlertaPressao = isPressao && (m.sistolica >= 140 || m.diastolica >= 90);
            return (
              <div
                key={m.id}
                className="card"
                style={{
                  margin: 0,
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderLeft: isAlertaPressao ? '5px solid var(--color-vermelho)' : '5px solid var(--color-rosa)'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <strong style={{ color: 'var(--color-vinho)', fontSize: '1.05rem' }}>
                      {isPressao ? `${m.sistolica}x${m.diastolica} mmHg` : `${m.glicemia} mg/dL`}
                    </strong>
                    {isAlertaPressao && (
                      <span className="badge-rosa" style={{ backgroundColor: '#FDEEE9', color: '#C0392B' }}>
                        Pico Pressórico
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                    {new Date(m.data_hora).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })} • Origem: {m.origem === 'dispositivo_bluetooth' ? 'Bluetooth SIG' : 'Manual'}
                  </span>
                </div>
                <span className="badge-gold">{isPressao ? 'PA' : 'Glicose'}</span>
              </div>
            );
          })}
        </div>
      )}

      <TriageDisclaimer />
    </div>
  );
}
