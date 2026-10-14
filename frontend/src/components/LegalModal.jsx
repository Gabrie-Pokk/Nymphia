import React, { useState, useEffect } from 'react';
import { ShieldCheck, FileText, X, Download, ExternalLink, CheckCircle2, Lock, AlertCircle } from 'lucide-react';
import { apiFetch } from '../utils/api';

export default function LegalModal({ isOpen, onClose, initialTab = 'privacidade' }) {
  const [aba, setAba] = useState(initialTab); // 'privacidade' | 'termos'
  const [politica, setPolitica] = useState(null);
  const [termos, setTermos] = useState(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    if (initialTab) setAba(initialTab);
  }, [initialTab]);

  useEffect(() => {
    if (!isOpen) return;
    setCarregando(true);
    Promise.all([
      apiFetch('/politica-privacidade', { skipAuth: true }).catch(() => null),
      apiFetch('/termos-de-uso', { skipAuth: true }).catch(() => null)
    ])
      .then(([pol, ter]) => {
        if (pol) setPolitica(pol);
        if (ter) setTermos(ter);
      })
      .finally(() => setCarregando(false));
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(44, 24, 30, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: 'var(--radius-lg)',
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
          overflow: 'hidden'
        }}
      >
        {/* Header do Modal */}
        <div
          style={{
            backgroundColor: 'var(--color-vinho)',
            color: '#FFFFFF',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldCheck size={24} color="var(--color-dourado)" />
            <div>
              <h2 style={{ fontSize: '1.15rem', margin: 0, color: '#FFFFFF', fontWeight: 800 }}>
                Conformidade Legal & LGPD
              </h2>
              <span style={{ fontSize: '0.75rem', opacity: 0.9 }}>
                Versão 1.0 (11 de outubro de 2026) • Nymphia Saúde Digital
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#FFFFFF',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '50%'
            }}
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        {/* Abas */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-rosa-claro)'
          }}
        >
          <button
            type="button"
            onClick={() => setAba('privacidade')}
            style={{
              flex: 1,
              padding: '12px 16px',
              border: 'none',
              borderBottom: aba === 'privacidade' ? '3px solid var(--color-vinho)' : '3px solid transparent',
              backgroundColor: aba === 'privacidade' ? '#FFFFFF' : 'transparent',
              color: aba === 'privacidade' ? 'var(--color-vinho)' : 'var(--color-text-muted)',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <Lock size={16} /> Política de Privacidade (LGPD)
          </button>
          <button
            type="button"
            onClick={() => setAba('termos')}
            style={{
              flex: 1,
              padding: '12px 16px',
              border: 'none',
              borderBottom: aba === 'termos' ? '3px solid var(--color-vinho)' : '3px solid transparent',
              backgroundColor: aba === 'termos' ? '#FFFFFF' : 'transparent',
              color: aba === 'termos' ? 'var(--color-vinho)' : 'var(--color-text-muted)',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <FileText size={16} /> Termos de Uso da Plataforma
          </button>
        </div>

        {/* Conteúdo com rolagem */}
        <div
          style={{
            padding: '20px',
            overflowY: 'auto',
            flex: 1,
            fontSize: '0.86rem',
            lineHeight: 1.55,
            color: 'var(--color-text-main)'
          }}
        >
          {aba === 'privacidade' && (
            <div>
              <div
                style={{
                  backgroundColor: '#F4F9F6',
                  borderLeft: '4px solid #27AE60',
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '16px'
                }}
              >
                <strong style={{ color: '#1E7E34', display: 'block', marginBottom: '4px' }}>
                  🛡️ Tratamento Ético e Responsável de Dados de Saúde
                </strong>
                {politica?.resumo ||
                  'A Nymphia trata dados pessoais sensíveis de saúde em conformidade rigorosa com a Lei 13.709/2018 (LGPD), Resoluções CFM 2.454/2026 e CFM 1.821/2007.'}
              </div>

              {/* DPO / Encarregado */}
              <div
                style={{
                  backgroundColor: '#FFFBF2',
                  border: '1px solid var(--color-dourado)',
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '16px'
                }}
              >
                <strong style={{ color: '#92400E', display: 'block', marginBottom: '4px' }}>
                  Canal do Encarregado de Proteção de Dados (DPO - Art. 41 LGPD):
                </strong>
                <p style={{ margin: '2px 0' }}>
                  <strong>Identificação:</strong> Comitê de Governança e Privacidade Nymphia
                </p>
                <p style={{ margin: '2px 0' }}>
                  <strong>Contato Direto:</strong>{' '}
                  <a href="mailto:privacidade@nymphia.com.br" style={{ color: 'var(--color-rosa)', fontWeight: 700 }}>
                    privacidade@nymphia.com.br
                  </a>
                </p>
                <p style={{ margin: '2px 0', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  Prazo de resposta para requisições de titulares: até 3 a 15 dias úteis (Resolução CD/ANPD nº 15/2024).
                </p>
              </div>

              <h4 style={{ color: 'var(--color-vinho)', marginTop: '16px', marginBottom: '8px' }}>
                1. Bases Legais Mapeadas (Arts. 7º e 11 da LGPD)
              </h4>
              <ul style={{ paddingLeft: '20px', margin: '0 0 16px 0' }}>
                <li>
                  <strong>Dados de Saúde (Sintomas, Histórico, DUM, Exames):</strong> Consentimento específico e destacado
                  (Art. 11, I da LGPD) e Tutela da Saúde (Art. 11, II, 'f').
                </li>
                <li>
                  <strong>Socorro e Emergência SAMU 192:</strong> Proteção da vida e integridade física (Art. 11, II, 'e').
                </li>
                <li>
                  <strong>Inteligência Artificial:</strong> Consentimento livre com direito incondicional de recusa informado
                  (Resolução CFM 2.454/2026).
                </li>
                <li>
                  <strong>Guarda de Prontuário Médico:</strong> Cumprimento de obrigação legal e regulatória (Art. 16, I c/c
                  Resolução CFM 1.821/2007).
                </li>
              </ul>

              <h4 style={{ color: 'var(--color-vinho)', marginTop: '16px', marginBottom: '8px' }}>
                2. Recorte Legal de Guarda de Prontuário vs. Eliminação de Conta
              </h4>
              <div
                style={{
                  backgroundColor: '#FDEEE9',
                  borderLeft: '4px solid #D9534F',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '16px'
                }}
              >
                <strong style={{ color: '#8A2B1A', display: 'block', marginBottom: '4px' }}>
                  Atenção Regulatória (CFM 1.821/2007 c/c Art. 16, I da LGPD):
                </strong>
                Caso você solicite a exclusão definitiva da sua conta, todos os seus dados cadastrais, diários de humor,
                mensagens e dados de navegação são completamente destruídos. Contudo, pareceres médicos, condutas e registros
                inseridos por obstetras vinculados são preservados sob guarda arquivística obrigatória da equipe de saúde
                pelo prazo regulamentar do CFM (guarda permanente ou 20 anos), não podendo ser apagados por determinação do
                Conselho Federal de Medicina.
              </div>

              <h4 style={{ color: 'var(--color-vinho)', marginTop: '16px', marginBottom: '8px' }}>
                3. Seus Direitos (Art. 18 e Art. 20 da LGPD)
              </h4>
              <p>
                Você tem o direito de exportar seu prontuário em PDF ou JSON a qualquer momento, revogar seu consentimento,
                recusar o processamento por IA e solicitar revisão humana de decisões algorítmicas diretamente na aba{' '}
                <strong>Meus Dados</strong>.
              </p>
            </div>
          )}

          {aba === 'termos' && (
            <div>
              <div
                style={{
                  backgroundColor: '#F4F9F6',
                  borderLeft: '4px solid var(--color-vinho)',
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '16px'
                }}
              >
                <strong style={{ color: 'var(--color-vinho)', display: 'block', marginBottom: '4px' }}>
                  Condições Gerais de Uso do Aplicativo
                </strong>
                {termos?.resumo ||
                  'A Nymphia é uma assistente digital de apoio educativo, organização de informações e suporte à triagem perinatal.'}
              </div>

              <h4 style={{ color: 'var(--color-vinho)', marginTop: '16px', marginBottom: '8px' }}>
                1. Natureza do Serviço e Limitações Médicas
              </h4>
              <ul style={{ paddingLeft: '20px', margin: '0 0 16px 0' }}>
                <li>
                  <strong>Apoio de Triagem, Não Diagnóstico:</strong> A Nymphia não realiza diagnósticos médicos nem prescreve
                  tratamentos. Todas as métricas populacionais são ferramentas informativas auxiliares (CFM 2.454/2026).
                </li>
                <li>
                  <strong>Autonomia Médica:</strong> A autoridade clínica pertence exclusivamente ao médico obstetra
                  responsável pelo pré-natal presencial.
                </li>
                <li>
                  <strong>Gratuidade Irrevogável de Emergência:</strong> O acionamento do SAMU 192, a rota para a maternidade
                  e o aviso ao parceiro são 100% gratuitos em qualquer plano, mesmo que a conta esteja inadimplente.
                </li>
              </ul>

              <h4 style={{ color: 'var(--color-vinho)', marginTop: '16px', marginBottom: '8px' }}>
                2. Regras de Segurança e Moderação Comunitária
              </h4>
              <ul style={{ paddingLeft: '20px', margin: '0 0 16px 0' }}>
                <li>
                  <strong>Proibição de Automedicação:</strong> É proibido indicar medicamentos, receitas caseiras nocivas ou
                  dosagens no feed da comunidade.
                </li>
                <li>
                  <strong>Acolhimento Perinatal:</strong> Usuárias em sofrimento psíquico grave são acolhidas com canais de
                  apoio imediato e suporte pelo Centro de Valorização da Vida (CVV - Disque 188).
                </li>
              </ul>

              <h4 style={{ color: 'var(--color-vinho)', marginTop: '16px', marginBottom: '8px' }}>
                3. Responsabilidade de Dados e Cancelamento
              </h4>
              <p>
                A assinatura de planos pagos confere direito de arrependimento em 7 dias (Art. 49 do Código de Defesa do
                Consumidor). O cancelamento pode ser feito a qualquer instante na área de assinaturas.
              </p>
            </div>
          )}
        </div>

        {/* Rodapé com botão de fechar */}
        <div
          style={{
            padding: '12px 20px',
            backgroundColor: '#FAFAFA',
            borderTop: '1px solid var(--color-border)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '10px'
          }}
        >
          <button type="button" onClick={onClose} className="btn btn-primary" style={{ minHeight: '40px', padding: '6px 20px' }}>
            Entendido e Ciente
          </button>
        </div>
      </div>
    </div>
  );
}
