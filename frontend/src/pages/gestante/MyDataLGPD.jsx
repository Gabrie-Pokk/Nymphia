import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import LegalModal from '../../components/LegalModal';
import {
  Download,
  Shield,
  Eye,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Code,
  Scale,
  Send,
  HelpCircle,
  Clock
} from 'lucide-react';

export default function MyDataLGPD({ onBack }) {
  const { user, updateUser, logout, authHeaders } = useAuth();
  const [logs, setLogs] = useState([]);
  const [dpoInfo, setDpoInfo] = useState(null);
  const [revisoes, setRevisoes] = useState([]);
  const [recusaIa, setRecusaIa] = useState(user?.recusa_ia || false);
  const [carregando, setCarregando] = useState(false);
  const [sucesso, setSucesso] = useState('');
  const [erro, setErro] = useState('');

  // Modal & Form de Revisão Humana (Art. 20 LGPD)
  const [formRevisaoAberto, setFormRevisaoAberto] = useState(false);
  const [decisaoRef, setDecisaoRef] = useState('');
  const [justificativa, setJustificativa] = useState('');
  const [enviandoRevisao, setEnviandoRevisao] = useState(false);

  // Modal de Documentos Legais
  const [modalLegalAberto, setModalLegalAberto] = useState(false);
  const [abaLegalInicial, setAbaLegalInicial] = useState('politica');

  const abrirLegal = (aba) => {
    setAbaLegalInicial(aba);
    setModalLegalAberto(true);
  };

  useEffect(() => {
    // Buscar Logs de Acesso
    fetch('/meus-dados/log-acesso', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setLogs(data))
      .catch(() => {});

    // Buscar Informações do DPO
    fetch('/meus-dados/dpo')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setDpoInfo(data);
      })
      .catch(() => {});

    // Buscar Revisões de IA Solicitadas
    carregarRevisoes();
  }, []);

  const carregarRevisoes = () => {
    fetch('/meus-dados/minhas-revisoes', { headers: authHeaders() })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setRevisoes(data))
      .catch(() => {});
  };

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

  const handleSolicitarRevisaoIA = async (e) => {
    e.preventDefault();
    if (!decisaoRef.trim() || !justificativa.trim()) {
      setErro('Por favor, preencha todos os campos da solicitação.');
      return;
    }

    setEnviandoRevisao(true);
    setErro('');
    try {
      const res = await fetch('/meus-dados/solicitar-revisao-ia', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          decisao_referencia: decisaoRef.trim(),
          justificativa_gestante: justificativa.trim()
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao enviar solicitação.');
      }
      setSucesso('Solicitação de revisão humana protocolada com sucesso (Art. 20 da LGPD).');
      setDecisaoRef('');
      setJustificativa('');
      setFormRevisaoAberto(false);
      carregarRevisoes();
    } catch (err) {
      setErro(err.message);
    } finally {
      setEnviandoRevisao(false);
    }
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
      'Atenção: Esta ação é definitiva para os seus dados cadastrais (Art. 18, LGPD). Observação: Anotações médicas emitidas por profissionais são mantidas em arquivo legal por 20 anos (CFM 1.821/2007). Digite "EXCLUIR" para confirmar:'
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
        alert('Sua conta foi excluída e seus dados pessoais expurgados conforme a LGPD.');
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

        <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer', fontSize: '0.88rem' }}>
          <input
            type="checkbox"
            checked={recusaIa}
            onChange={handleToggleConsentimentoIA}
            style={{ marginTop: '3px', width: '20px', height: '20px', flexShrink: 0, accentColor: 'var(--color-rosa)' }}
          />
          <span style={{ flex: 1, color: 'var(--color-text-main)', lineHeight: 1.45 }}>
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

      {/* 4. Revisão Humana de Decisões Automatizadas (Art. 20 da LGPD) */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Scale size={20} color="var(--color-vinho)" />
          <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Revisão Humana de Decisões de IA (Art. 20, LGPD)</h3>
        </div>
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '12px', lineHeight: 1.45 }}>
          Você tem o direito legal de solicitar a revisão, por um profissional de saúde qualificado, de qualquer decisão, triagem, alerta ou recomendação gerada exclusivamente por algoritmos e inteligência artificial.
        </p>

        {revisoes.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--color-vinho)', marginBottom: '8px' }}>Minhas Solicitações Anteriores</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {revisoes.map((rev) => (
                <div
                  key={rev.id}
                  style={{
                    padding: '10px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: '#F9F9F9',
                    border: '1px solid var(--color-border)',
                    fontSize: '0.82rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <strong>Ref: {rev.decisao_referencia}</strong>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        backgroundColor:
                          rev.status === 'CONCLUIDA'
                            ? '#E8F8F0'
                            : rev.status === 'INDEFERIDA'
                            ? '#FDEEE9'
                            : '#FFF8E1',
                        color:
                          rev.status === 'CONCLUIDA'
                            ? '#1E7E34'
                            : rev.status === 'INDEFERIDA'
                            ? '#D9534F'
                            : '#B78103'
                      }}
                    >
                      {rev.status}
                    </span>
                  </div>
                  <p style={{ margin: '4px 0', color: 'var(--color-text-muted)' }}>{rev.justificativa_gestante}</p>
                  {rev.parecer_humano && (
                    <div style={{ marginTop: '6px', padding: '8px', backgroundColor: '#FFFFFF', borderRadius: '4px', borderLeft: '3px solid var(--color-vinho)' }}>
                      <strong>Parecer do Especialista:</strong> {rev.parecer_humano}
                      {rev.revisado_por_nome && (
                        <span style={{ display: 'block', fontSize: '0.72rem', color: '#666', marginTop: '2px' }}>
                          Avaliador: {rev.revisado_por_nome} ({rev.revisado_por_crm})
                        </span>
                      )}
                    </div>
                  )}
                  <span style={{ fontSize: '0.72rem', color: '#999', display: 'block', marginTop: '4px' }}>
                    Solicitado em: {new Date(rev.criado_em).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {!formRevisaoAberto ? (
          <button
            onClick={() => setFormRevisaoAberto(true)}
            className="btn btn-outline"
            style={{ width: '100%', fontSize: '0.85rem' }}
          >
            <Send size={16} />
            Solicitar Revisão de uma Recomendação de IA
          </button>
        ) : (
          <form
            onSubmit={handleSolicitarRevisaoIA}
            style={{
              padding: '14px',
              backgroundColor: '#FAFAFA',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid #E0E0E0'
            }}
          >
            <h4 style={{ fontSize: '0.9rem', marginBottom: '10px' }}>Nova Solicitação de Revisão</h4>
            
            <div className="form-group" style={{ marginBottom: '10px' }}>
              <label style={{ fontSize: '0.82rem' }}>Qual recomendação ou alerta deseja revisar?</label>
              <input
                type="text"
                className="form-control"
                placeholder="Ex: Alerta de ganho ponderal da Semana 22 ou Orientação do Chatbot"
                value={decisaoRef}
                onChange={(e) => setDecisaoRef(e.target.value)}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '12px' }}>
              <label style={{ fontSize: '0.82rem' }}>Por que você deseja a revisão humana?</label>
              <textarea
                className="form-control"
                rows={3}
                placeholder="Descreva seus sintomas reais ou o motivo pelo qual você discorda ou deseja reavaliação médica..."
                value={justificativa}
                onChange={(e) => setJustificativa(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                className="btn btn-outline"
                style={{ flex: 1 }}
                onClick={() => setFormRevisaoAberto(false)}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ flex: 1 }}
                disabled={enviandoRevisao}
              >
                {enviandoRevisao ? 'Enviando...' : 'Protocolar Revisão'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* 5. Canal do DPO / Encarregado de Dados (Art. 41 LGPD) */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Shield size={20} color="var(--color-vinho)" />
          <h3 style={{ fontSize: '1.05rem', margin: 0 }}>Encarregado de Dados (DPO - Art. 41)</h3>
        </div>
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '12px', lineHeight: 1.45 }}>
          Nosso Encarregado pelo Tratamento de Dados Pessoais está à disposição para esclarecer dúvidas, receber reclamações e atender aos seus direitos sob a LGPD.
        </p>

        <div
          style={{
            padding: '12px',
            backgroundColor: '#FAFAFA',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid #E0E0E0',
            fontSize: '0.85rem',
            marginBottom: '12px'
          }}
        >
          <div><strong>Encarregado(a):</strong> {dpoInfo?.encarregado || 'Dra. Camila Vasconcellos, DPO'}</div>
          <div style={{ marginTop: '4px' }}>
            <strong>Canal Oficial:</strong>{' '}
            <a
              href={`mailto:${dpoInfo?.email || 'privacidade@nymphia.com.br'}`}
              style={{ color: 'var(--color-primary, #5C1A2A)', fontWeight: 600, textDecoration: 'underline' }}
            >
              {dpoInfo?.email || 'privacidade@nymphia.com.br'}
            </a>
          </div>
          <div style={{ marginTop: '4px', color: '#666', fontSize: '0.78rem' }}>
            Prazo de resposta para requisições formais: até 15 dias corridos (Art. 19, II, LGPD).
          </div>
        </div>

        <a
          href={`mailto:${dpoInfo?.email || 'privacidade@nymphia.com.br'}?subject=Requisicao%20LGPD%20-%20Nymphia`}
          className="btn btn-outline"
          style={{ width: '100%', fontSize: '0.85rem' }}
        >
          Enviar Mensagem ao Encarregado
        </a>
      </div>

      {/* 6. Consulta a Termos e Políticas */}
      <div className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>Documentos Legais da Plataforma</h3>
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '14px' }}>
          Consulte a versão vigente e integral dos nossos termos contratuais e governança de privacidade a qualquer instante.
        </p>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => abrirLegal('politica')}
            className="btn btn-outline"
            style={{ flex: 1, fontSize: '0.85rem' }}
          >
            <FileText size={16} />
            Política de Privacidade
          </button>
          <button
            onClick={() => abrirLegal('termos')}
            className="btn btn-outline"
            style={{ flex: 1, fontSize: '0.85rem' }}
          >
            <FileText size={16} />
            Termos de Uso
          </button>
        </div>
      </div>

      {/* 7. Exclusão Definitiva de Conta & Guarda CFM */}
      <div className="card" style={{ border: '1px solid #D9534F', backgroundColor: '#FDF7F7' }}>
        <h3 style={{ fontSize: '1.05rem', color: '#8A2B1A', marginBottom: '6px' }}>
          Eliminação de Dados Pessoais (Art. 18, VI da LGPD)
        </h3>
        <p style={{ fontSize: '0.82rem', color: '#8A2B1A', marginBottom: '10px', lineHeight: 1.45 }}>
          A exclusão de sua conta expurga seus dados cadastrais, credenciais de acesso e dados de navegação imediatamente.
        </p>
        <p style={{ fontSize: '0.78rem', color: '#666', marginBottom: '14px', lineHeight: 1.45, backgroundColor: '#FFF', padding: '8px', borderRadius: '4px', border: '1px solid #E0E0E0' }}>
          <strong>Aviso de Guarda Legal (CFM 1.821/2007 e Art. 16, I da LGPD):</strong> Conforme a legislação médica federal brasileira, evoluções clínicas, pareceres e anotações emitidas por profissionais de saúde registrados devem permanecer em arquivo de custódia inativa e confidencial por 20 anos, não sendo passíveis de exclusão arbitrária.
        </p>

        <button
          onClick={handleExcluirConta}
          className="btn btn-outline"
          style={{ borderColor: '#D9534F', color: '#8A2B1A', width: '100%' }}
        >
          <Trash2 size={16} />
          Excluir Minha Conta e Expurgo de Dados LGPD
        </button>
      </div>

      {/* Modal Institucional de Termos e LGPD */}
      <LegalModal
        isOpen={modalLegalAberto}
        onClose={() => setModalLegalAberto(false)}
        initialTab={abaLegalInicial}
      />
    </div>
  );
}
