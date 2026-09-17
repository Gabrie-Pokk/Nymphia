import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import { Send, Share2, Check, AlertTriangle, ShieldCheck } from 'lucide-react';
import LotusLogo from '../../components/LotusLogo';

export default function AiChat({ onBack }) {
  const { authHeaders } = useAuth();
  const [mensagens, setMensagens] = useState([]);
  const [inputTexto, setInputTexto] = useState('');
  const [carregando, setCarregando] = useState(false);
  const messagesEndRef = useRef(null);

  const carregarHistorico = async () => {
    try {
      const res = await fetch('/conversa/historico', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setMensagens(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    carregarHistorico();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensagens]);

  const handleEnviar = async (e) => {
    e.preventDefault();
    if (!inputTexto.trim() || carregando) return;

    const texto = inputTexto.trim();
    setInputTexto('');

    // Mensagem otimista temporária
    const tempMsg = {
      id: Date.now(),
      papel: 'gestante',
      conteudo: texto,
      data_hora: new Date().toISOString(),
      alerta_emergencia: false,
      autorizado_compartilhar: false
    };
    setMensagens((prev) => [...prev, tempMsg]);
    setCarregando(true);

    try {
      const res = await fetch('/conversa/enviar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ texto })
      });
      const data = await res.json();
      if (res.ok) {
        setMensagens((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            papel: 'ia',
            conteudo: data.resposta,
            data_hora: new Date().toISOString(),
            alerta_emergencia: data.alerta_emergencia,
            autorizado_compartilhar: false
          }
        ]);
      }
    } catch (err) {
    } finally {
      setCarregando(false);
    }
  };

  const handleCompartilhar = async (id) => {
    try {
      const res = await fetch(`/conversa/${id}/autorizar-compartilhamento`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (res.ok) {
        setMensagens((prev) =>
          prev.map((m) => (m.id === id ? { ...m, autorizado_compartilhar: true } : m))
        );
      }
    } catch (err) {}
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      <BackButton onClick={onBack} label="Voltar para Início" />

      {/* Header do Chat */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingBottom: '12px', borderBottom: '1px solid var(--color-border)' }}>
        <LotusLogo size={32} color="var(--color-rosa)" />
        <div>
          <h2 style={{ fontSize: '1.15rem', margin: 0 }}>Assistente Clínica Nymphia</h2>
          <p className="text-muted" style={{ fontSize: '0.78rem' }}>
            Apoio contínuo baseado em protocolos FEBRASGO e Ministério da Saúde
          </p>
        </div>
      </div>

      <TriageDisclaimer />

      {/* Área de Mensagens com Rolagem */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 0',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}
      >
        {mensagens.length === 0 ? (
          <div style={{ textAlign: 'center', margin: 'auto 0', padding: '24px' }}>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
              Olá! Pergunte sobre sua rotina gestacional, prevenção de infecções (como toxoplasmose), vacinas, alimentação ou compartilhe seus sintomas.
            </p>
          </div>
        ) : (
          mensagens.map((msg) => {
            const isGestante = msg.papel === 'gestante';
            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isGestante ? 'flex-end' : 'flex-start'
                }}
              >
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '12px 16px',
                    borderRadius: isGestante ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                    backgroundColor: isGestante
                      ? 'var(--color-rosa)'
                      : msg.alerta_emergencia
                      ? '#FDEDEC'
                      : 'var(--color-rosa-claro)',
                    color: isGestante ? '#FFFFFF' : '#2C181E',
                    border: msg.alerta_emergencia ? '2px solid var(--color-vermelho)' : '1px solid var(--color-border)',
                    boxShadow: 'var(--shadow-sm)',
                    fontSize: '0.92rem',
                    lineHeight: 1.45,
                    position: 'relative'
                  }}
                >
                  {msg.alerta_emergencia && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--color-vermelho)', marginBottom: '6px' }}>
                      <AlertTriangle size={16} /> ALERTA DE EMERGÊNCIA DISPARADO
                    </div>
                  )}
                  {msg.conteudo}
                </div>

                {/* Ações da Mensagem: Autorizar compartilhamento com o médico */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                  <span>{new Date(msg.data_hora).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</span>
                  {msg.autorizado_compartilhar ? (
                    <span style={{ color: '#27AE60', display: 'flex', alignItems: 'center', gap: '2px' }}>
                      <Check size={12} /> Compartilhado com médico
                    </span>
                  ) : (
                    <button
                      onClick={() => handleCompartilhar(msg.id)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--color-rosa)',
                        padding: 0,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.72rem',
                        minHeight: '24px'
                      }}
                      title="Autorizar o médico vinculado a visualizar este trecho"
                    >
                      <Share2 size={12} /> Autorizar compartilhamento
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input de Mensagem */}
      <form onSubmit={handleEnviar} style={{ display: 'flex', gap: '8px', paddingTop: '10px' }}>
        <input
          type="text"
          className="form-control"
          placeholder="Tire dúvidas sobre sintomas, exames ou alimentação..."
          value={inputTexto}
          onChange={(e) => setInputTexto(e.target.value)}
          disabled={carregando}
          style={{ flex: 1 }}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={carregando || !inputTexto.trim()}
          style={{ minWidth: '48px', minHeight: '48px', padding: '0 16px' }}
          aria-label="Enviar mensagem"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
