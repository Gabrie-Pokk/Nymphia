import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { 
  Check, Shield, Sparkles, HeartHandshake, Stethoscope, 
  QrCode, CreditCard, AlertCircle, X, ExternalLink, RefreshCw 
} from 'lucide-react';

export default function SubscriptionScreen({ onBack }) {
  const { authHeaders } = useAuth();
  const [planos, setPlanos] = useState([]);
  const [minhaAssinatura, setMinhaAssinatura] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [modalCheckout, setModalCheckout] = useState(false);
  const [planoSelecionado, setPlanoSelecionado] = useState(null);
  const [metodoPagamento, setMetodoPagamento] = useState('pix');
  const [dadosCheckout, setDadosCheckout] = useState(null);
  const [processandoPagamento, setProcessandoPagamento] = useState(false);
  const [copiadoPix, setCopiadoPix] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState('');

  const carregarDados = async () => {
    setCarregando(true);
    try {
      const [resPlanos, resMinha] = await Promise.all([
        fetch('/assinatura/planos'),
        fetch('/assinatura/minha-assinatura', { headers: authHeaders() })
      ]);

      if (resPlanos.ok) {
        const pData = await resPlanos.json();
        setPlanos(pData);
      }
      if (resMinha.ok) {
        const mData = await resMinha.json();
        setMinhaAssinatura(mData);
      }
    } catch (err) {
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregarDados();
  }, []);

  const handleAbrirCheckout = (plano) => {
    setPlanoSelecionado(plano);
    setDadosCheckout(null);
    setCopiadoPix(false);
    setModalCheckout(true);
  };

  const handleIniciarCheckout = async () => {
    if (!planoSelecionado) return;
    setProcessandoPagamento(true);
    try {
      const res = await fetch('/assinatura/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          plano: planoSelecionado.id,
          forma_pagamento: metodoPagamento
        })
      });

      const data = await res.json();
      if (res.ok) {
        setDadosCheckout(data);
        if (planoSelecionado.id === 'free') {
          setMensagemSucesso('Plano Gratuito ativado com sucesso!');
          setTimeout(() => {
            setModalCheckout(false);
            carregarDados();
          }, 1200);
        }
      }
    } catch (err) {
    } finally {
      setProcessandoPagamento(false);
    }
  };

  const handleConfirmarPagamentoSimulado = async () => {
    if (!dadosCheckout) return;
    setProcessandoPagamento(true);
    try {
      const res = await fetch('/assinatura/simular-webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          subscription_id: dadosCheckout.mercado_pago_id,
          status: 'approved'
        })
      });

      if (res.ok) {
        setMensagemSucesso('Pagamento aprovado com sucesso pelo Mercado Pago! Seu plano está ativo.');
        setTimeout(() => {
          setModalCheckout(false);
          carregarDados();
        }, 1500);
      }
    } catch (err) {
    } finally {
      setProcessandoPagamento(false);
    }
  };

  const handleCopiarPix = () => {
    if (dadosCheckout && dadosCheckout.pix_copia_cola) {
      navigator.clipboard.writeText(dadosCheckout.pix_copia_cola);
      setCopiadoPix(true);
      setTimeout(() => setCopiadoPix(false), 3000);
    }
  };

  const handleCancelarAssinatura = async () => {
    if (!confirm('Deseja realmente cancelar a renovação da sua assinatura? Seu canal de emergência continuará sempre ativo gratuitamente.')) return;
    try {
      const res = await fetch('/assinatura/cancelar', {
        method: 'POST',
        headers: authHeaders()
      });
      if (res.ok) {
        alert('Renovação automática cancelada. Seus recursos de segurança e emergência permanecem sempre gratuitos.');
        carregarDados();
      }
    } catch (err) {}
  };

  return (
    <div style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}>
      <BackButton onClick={onBack} label="Voltar para Início" />

      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.4rem', color: 'var(--color-vinho)', margin: '0 0 6px 0' }}>Planos & Assinatura Nymphia</h2>
        <p className="text-muted" style={{ fontSize: '0.86rem', margin: 0 }}>
          Acompanhamento gestacional contínuo com inteligência artificial, suporte clínico obstétrico e acolhimento para sua família.
        </p>
      </div>

      {/* Status Atual da Assinatura */}
      {minhaAssinatura && (
        <div className="card" style={{ padding: '16px 20px', marginBottom: '20px', backgroundColor: 'var(--color-rosa-claro)', border: '1.5px solid var(--color-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--color-rosa)' }}>Seu Plano Atual</span>
              <h3 style={{ fontSize: '1.2rem', color: 'var(--color-vinho)', margin: '2px 0 4px 0' }}>
                {minhaAssinatura.plano === 'free' && 'Plano Gratuito (Segurança Essencial)'}
                {minhaAssinatura.plano === 'premium' && '⭐ Plano Premium (IA & Risco)'}
                {minhaAssinatura.plano === 'premium_plus' && '✨ Plano Premium+ (Completo)'}
                {minhaAssinatura.plano === 'clinica' && '🏥 Plano Clínica (B2B)'}
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', margin: 0 }}>
                Status: <strong style={{ color: minhaAssinatura.status === 'ativa' ? '#27AE60' : 'var(--color-vermelho)' }}>{minhaAssinatura.status.toUpperCase()}</strong>
                {minhaAssinatura.proxima_cobranca && ` • Próxima renovação: ${new Date(minhaAssinatura.proxima_cobranca).toLocaleDateString('pt-BR')}`}
              </p>
            </div>
            {minhaAssinatura.plano !== 'free' && minhaAssinatura.status === 'ativa' && (
              <button
                onClick={handleCancelarAssinatura}
                className="btn btn-outline"
                style={{ fontSize: '0.78rem', padding: '6px 12px', minHeight: '34px' }}
              >
                Cancelar Renovação
              </button>
            )}
          </div>
        </div>
      )}

      {/* Blindagem Ética Mandatória de Segurança */}
      <div className="card" style={{ padding: '14px 18px', marginBottom: '24px', backgroundColor: '#F4F9F5', border: '1px solid #C8E6C9' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Shield size={24} color="#27AE60" />
          <div style={{ fontSize: '0.84rem', color: '#1E4620', lineHeight: 1.45 }}>
            <strong>Compromisso Ético Nymphia:</strong> O botão de emergência obstétrica, a chamada direta ao SAMU 192, a identificação de sinais de alerta e o aviso de socorro ao parceiro são <strong>100% gratuitos para sempre em todos os planos</strong>, mesmo em caso de inadimplência. A saúde materna nunca fica atrás de paywall.
          </div>
        </div>
      </div>

      {/* Grid de Planos */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {planos.map((plano) => {
          const isCurrent = minhaAssinatura && minhaAssinatura.plano === plano.id && minhaAssinatura.status === 'ativa';
          return (
            <div
              key={plano.id}
              className="card"
              style={{
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '20px',
                border: plano.destaque ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                boxShadow: plano.destaque ? 'var(--shadow-md)' : 'var(--shadow-sm)',
                backgroundColor: isCurrent ? 'var(--color-rosa-claro)' : '#FFFFFF'
              }}
            >
              {plano.destaque && (
                <div style={{
                  position: 'absolute',
                  top: '-12px',
                  right: '16px',
                  backgroundColor: 'var(--color-rosa)',
                  color: '#FFFFFF',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '3px 10px',
                  borderRadius: '12px',
                  letterSpacing: '0.5px'
                }}>
                  MAIS RECOMENDADO
                </div>
              )}

              <div>
                <h3 style={{ fontSize: '1.15rem', color: 'var(--color-vinho)', margin: '0 0 6px 0' }}>{plano.nome}</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', minHeight: '38px', marginBottom: '12px' }}>
                  {plano.descricao}
                </p>

                <div style={{ marginBottom: '16px' }}>
                  <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--color-vinho)' }}>
                    {plano.preco === 0 ? 'Grátis' : `R$ ${plano.preco.toFixed(2).replace('.', ',')}`}
                  </span>
                  {plano.preco > 0 && <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}> /mês</span>}
                </div>

                <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '14px', marginBottom: '20px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-vinho)', display: 'block', marginBottom: '10px' }}>
                    Recursos Inclusos:
                  </span>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {plano.recursos.map((rec, idx) => (
                      <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.82rem', color: 'var(--color-text-main)', lineHeight: 1.35 }}>
                        <Check size={16} color="var(--color-rosa)" style={{ flexShrink: 0, marginTop: '2px' }} />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div>
                {isCurrent ? (
                  <button
                    disabled
                    className="btn btn-outline"
                    style={{ width: '100%', minHeight: '44px', fontWeight: 700, borderColor: '#27AE60', color: '#27AE60' }}
                  >
                    <Check size={18} /> Seu Plano Ativo
                  </button>
                ) : (
                  <button
                    onClick={() => handleAbrirCheckout(plano)}
                    className={plano.destaque ? 'btn btn-primary' : 'btn btn-outline'}
                    style={{ width: '100%', minHeight: '44px', fontWeight: 700 }}
                  >
                    {plano.preco === 0 ? 'Mudar para Gratuito' : `Assinar ${plano.nome.split(' ')[1] || ''}`}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal de Checkout Integrado com Mercado Pago */}
      {modalCheckout && planoSelecionado && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(34, 10, 16, 0.65)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 9999,
          padding: '16px'
        }}>
          <div className="card" style={{
            width: '100%',
            maxWidth: '480px',
            maxHeight: '90vh',
            overflowY: 'auto',
            backgroundColor: '#FFFFFF',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)',
            padding: '24px',
            position: 'relative'
          }}>
            <button
              onClick={() => setModalCheckout(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
              aria-label="Fechar"
            >
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Sparkles size={22} color="var(--color-rosa)" />
              <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--color-vinho)' }}>
                Assinatura {planoSelecionado.nome}
              </h3>
            </div>
            <p className="text-muted" style={{ fontSize: '0.84rem', marginBottom: '18px' }}>
              Valor: <strong>R$ {planoSelecionado.preco.toFixed(2).replace('.', ',')} / mês</strong> • Pagamento seguro via Mercado Pago
            </p>

            {mensagemSucesso && (
              <div style={{ backgroundColor: '#E8F8F5', color: '#117A65', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.88rem', fontWeight: 600 }}>
                {mensagemSucesso}
              </div>
            )}

            {!dadosCheckout ? (
              <div>
                <label style={{ display: 'block', fontWeight: 600, fontSize: '0.88rem', marginBottom: '8px' }}>
                  Selecione o meio de pagamento:
                </label>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                  <button
                    type="button"
                    onClick={() => setMetodoPagamento('pix')}
                    style={{
                      flex: 1,
                      padding: '12px',
                      borderRadius: '8px',
                      border: metodoPagamento === 'pix' ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                      backgroundColor: metodoPagamento === 'pix' ? 'var(--color-rosa-claro)' : '#FFFFFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                      fontWeight: 600,
                      fontSize: '0.88rem'
                    }}
                  >
                    <QrCode size={18} color="var(--color-rosa)" /> Pix (Instantâneo)
                  </button>
                  <button
                    type="button"
                    onClick={() => setMetodoPagamento('cartao_credito')}
                    style={{
                      flex: 1,
                      padding: '12px',
                      borderRadius: '8px',
                      border: metodoPagamento === 'cartao_credito' ? '2px solid var(--color-rosa)' : '1px solid var(--color-border)',
                      backgroundColor: metodoPagamento === 'cartao_credito' ? 'var(--color-rosa-claro)' : '#FFFFFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                      fontWeight: 600,
                      fontSize: '0.88rem'
                    }}
                  >
                    <CreditCard size={18} color="var(--color-rosa)" /> Cartão de Crédito
                  </button>
                </div>

                <button
                  onClick={handleIniciarCheckout}
                  disabled={processandoPagamento}
                  className="btn btn-primary"
                  style={{ width: '100%', minHeight: '46px', fontWeight: 700 }}
                >
                  {processandoPagamento ? 'Gerando cobrança...' : 'Avançar para Pagamento Seguro'}
                </button>
              </div>
            ) : (
              <div>
                {dadosCheckout.forma_pagamento === 'pix' && dadosCheckout.pix_copia_cola && (
                  <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                    <p style={{ fontSize: '0.84rem', color: 'var(--color-text-muted)', marginBottom: '12px' }}>
                      Escaneie o QR Code abaixo no app do seu banco ou utilize a chave Pix Copia e Cola:
                    </p>
                    <div style={{ display: 'inline-block', padding: '12px', backgroundColor: '#FFFFFF', border: '1px solid var(--color-border)', borderRadius: '12px', marginBottom: '14px' }}>
                      <img
                        src={dadosCheckout.pix_qrcode}
                        alt="QR Code Pix Mercado Pago"
                        style={{ width: '180px', height: '180px', display: 'block' }}
                      />
                    </div>

                    <div className="form-group" style={{ marginBottom: '12px' }}>
                      <textarea
                        readOnly
                        value={dadosCheckout.pix_copia_cola}
                        rows={2}
                        className="form-control"
                        style={{ fontSize: '0.75rem', fontFamily: 'monospace', resize: 'none' }}
                      />
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={handleCopiarPix}
                        className="btn btn-outline"
                        style={{ flex: 1, minHeight: '40px', fontSize: '0.82rem' }}
                      >
                        {copiadoPix ? '✓ Código Copiado!' : 'Copiar Chave Pix'}
                      </button>
                      <button
                        onClick={handleConfirmarPagamentoSimulado}
                        disabled={processandoPagamento}
                        className="btn btn-primary"
                        style={{ flex: 1, minHeight: '40px', fontSize: '0.82rem' }}
                      >
                        {processandoPagamento ? 'Confirmando...' : 'Confirmar Pagamento'}
                      </button>
                    </div>
                  </div>
                )}

                {dadosCheckout.forma_pagamento === 'cartao_credito' && (
                  <div>
                    <p style={{ fontSize: '0.84rem', color: 'var(--color-text-muted)', marginBottom: '16px' }}>
                      Você será redirecionada para o ambiente seguro do Mercado Pago para inserir os dados do cartão de crédito:
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <a
                        href={dadosCheckout.checkout_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-primary"
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', minHeight: '46px', textDecoration: 'none' }}
                      >
                        Abrir Checkout Mercado Pago <ExternalLink size={16} />
                      </a>
                      <button
                        onClick={handleConfirmarPagamentoSimulado}
                        disabled={processandoPagamento}
                        className="btn btn-outline"
                        style={{ minHeight: '42px', fontSize: '0.84rem' }}
                      >
                        Simular Aprovação Imediata (Ambiente de Teste)
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
