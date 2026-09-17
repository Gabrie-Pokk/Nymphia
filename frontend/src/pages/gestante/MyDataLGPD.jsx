import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { Download, Shield, Eye, Trash2, CheckCircle2, AlertTriangle, FileText, Code } from 'lucide-react';

export default function MyDataLGPD({ onBack }) {
  const { user, updateUser, logout, authHeaders } = useAuth();
  const [logs, setLogs] = useState([]);
  const [recusaIa, setRecusaIa] = useState(user?.recusa_ia || false);
  const [carregando, setCarregando] = useState(false);
  const [sucesso, setSucesso] = useState('');
  const [erro, setErro] = useState('');

  useEffect(() => {
    fetch('/meus-dados/log-acesso', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setLogs(data))
      .catch(() => {});
  }, []);

  const handleToggleConsentimentoIA = async (e) => {
    const novoValor = e.target.checked;
    setRecusaIa(novoValor);
    try {
      const res = await fetch(`/meus-dados/consentimento-ia?recusa_ia=${novoValor}`, {
        method: 'PUT',
        headers: authHeaders()
      });
      if (res.ok) {
        updateUser({ recusa_ia: novoValor });
        setSucesso('Preferência de consentimento de IA atualizada.');
      }
    } catch (err) {}
  };

  const handleExportarJSON = async () => {
    try {
      const res = await fetch('/meus-dados/exportar?formato=json', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nymphia_dados_${user?.id?.slice(0, 8)}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {}
  };

  const handleExportarPDF = async () => {
    try {
      const res = await fetch('/meus-dados/exportar?formato=pdf', { headers: authHeaders() });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nymphia_prontuario_${user?.id?.slice(0, 8)}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {}
  };

  const handleExcluirConta = async () => {
    const confirmacao = window.prompt(
      'Atenção: Esta ação é definitiva e irreversível (Art. 18, LGPD). Todos os seus check-ins, exames, registros e dados serão apagados permanentemente. Digite "EXCLUIR" para confirmar:'
    );

    if (confirmacao !== 'EXCLUIR') {
      return;
    }

    try {
      const res = await fetch('/minha-conta', {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.ok) {
        alert('Sua conta e todos os dados associados foram completamente removidos.');
        logout();
      }
    } catch (err) {}
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <h2>Privacidade & Direitos LGPD</h2>
      <p className="text-muted" style={{ marginBottom: '20px' }}>
        Transparência, controle total e portabilidade dos seus dados clínicos sensíveis (Lei 13.709/2018).
      </p>

      {sucesso && (
        <div role="status" style={{ padding: '12px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-sm)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} /> {sucesso}
        </div>
      )}

      {/* 1. Portabilidade de Dados */}
      <div className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Portabilidade dos seus Dados (Art. 18, V)</h3>
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '16px' }}>
          Baixe uma cópia completa de todo o seu histórico clínico em formato PDF para impressão ou JSON estruturado.
        </p>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleExportarPDF}
            className="btn btn-vinho"
            style={{ flex: 1 }}
          >
            <FileText size={18} />
            Baixar em PDF
          </button>
          <button
            onClick={handleExportarJSON}
            className="btn btn-outline"
            style={{ flex: 1 }}
          >
            <Code size={18} />
            Baixar em JSON
          </button>
        </div>
      </div>

      {/* 2. Consentimento de IA e Direito de Recusa (CFM 2.454/2026) */}
      <div className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Uso de Inteligência Artificial (CFM 2.454/2026)</h3>
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '12px' }}>
          Você tem o direito de utilizar a plataforma recusando a análise automatizada por inteligência artificial.
        </p>

        <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', fontSize: '0.88rem' }}>
          <input
            type="checkbox"
            checked={recusaIa}
            onChange={handleToggleConsentimentoIA}
            style={{ marginTop: '3px', width: '18px', height: '18px', accentColor: 'var(--color-rosa)' }}
          />
          <span>
            <strong>Recusar análises de IA:</strong> Se marcado, o sistema operará estritamente através das regras determinísticas baseadas em protocolos do Ministério da Saúde, desativando modelos de linguagem na conversa.
          </span>
        </label>
      </div>

      {/* 3. Log de Acesso a Dados Sensíveis */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Eye size={18} color="var(--color-vinho)" />
          <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Quem acessou meus dados?</h3>
        </div>
        <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '12px' }}>
          Auditoria completa de todos os acessos realizados pelo seu médico ou parceiro.
        </p>

        {logs.length === 0 ? (
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
            Nenhum terceiro acessou seus dados até o momento.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {logs.map((log) => (
              <div
                key={log.id}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#FFFFFF',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  fontSize: '0.82rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <strong style={{ color: 'var(--color-vinho)', textTransform: 'capitalize' }}>
                    {log.acessado_por_tipo}
                  </strong>
                  <span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '0.75rem' }}>
                    Recurso: {log.recurso}
                  </span>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  {new Date(log.data_hora).toLocaleString('pt-BR')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. Exclusão Definitiva de Conta */}
      <div className="card" style={{ border: '1px solid #D9534F', backgroundColor: '#FDF7F7' }}>
        <h3 style={{ fontSize: '1.05rem', color: '#8A2B1A', marginBottom: '6px' }}>
          Eliminação de Dados (Art. 18, VI da LGPD)
        </h3>
        <p style={{ fontSize: '0.82rem', color: '#8A2B1A', marginBottom: '14px' }}>
          Exclua permanentemente sua conta, check-ins, exames e todos os vínculos médicos associados.
        </p>

        <button
          onClick={handleExcluirConta}
          className="btn btn-outline"
          style={{ borderColor: '#D9534F', color: '#8A2B1A', width: '100%' }}
        >
          <Trash2 size={16} />
          Excluir Minha Conta e Todos os Dados
        </button>
      </div>
    </div>
  );
}
