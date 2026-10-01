import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import {
  Scale,
  TrendingUp,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Plus,
  Trash2,
  Info,
  Calendar,
  Heart,
  Sparkles,
  BookOpen,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  ShieldCheck
} from 'lucide-react';

export default function Antropometria({ onBack }) {
  const { authHeaders, logout } = useAuth();
  const [painel, setPainel] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [sessaoExpirada, setSessaoExpirada] = useState(false);
  const [sucessoMsg, setSucessoMsg] = useState('');

  // Modais e formulários
  const [modalRegistroAberto, setModalRegistroAberto] = useState(false);
  const [modalBaseAberto, setModalBaseAberto] = useState(false);
  const [secaoAberta, setSecaoAberta] = useState('atalah'); // atalah | guia | historico

  // Form novo registro
  const [novoPeso, setNovoPeso] = useState('');
  const [novaSemana, setNovaSemana] = useState(24);
  const [novaAU, setNovaAU] = useState('');
  const [novaCircunferencia, setNovaCircunferencia] = useState('');
  const [novaPressao, setNovaPressao] = useState('');
  const [novoEdema, setNovoEdema] = useState('ausente');
  const [novaObs, setNovaObs] = useState('');
  const [salvandoRegistro, setSalvandoRegistro] = useState(false);

  // Form dados base
  const [formAltura, setFormAltura] = useState('');
  const [formPesoPre, setFormPesoPre] = useState('');
  const [salvandoBase, setSalvandoBase] = useState(false);

  const carregarDados = async () => {
    setCarregando(true);
    setErro('');
    setSessaoExpirada(false);
    try {
      const headers = authHeaders ? authHeaders() : {};
      const res = await fetch('/antropometria/painel', { headers });
      if (res.status === 401) {
        setSessaoExpirada(true);
        setErro('Sua sessão expirou ou não está autenticada. Por favor, faça login novamente para visualizar seus dados.');
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setPainel(data);
        if (data.semana_gestacional_atual) {
          setNovaSemana(data.semana_gestacional_atual);
        }
        if (data.altura_cm) setFormAltura(data.altura_cm);
        if (data.peso_pre_gestacional) setFormPesoPre(data.peso_pre_gestacional);
      } else {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Não foi possível carregar os dados de antropometria.');
      }
    } catch (err) {
      setErro(err.message || 'Erro de conexão ao carregar painel antropométrico.');
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregarDados();
  }, []);

  const handleSalvarBase = async (e) => {
    e.preventDefault();
    setSalvandoBase(true);
    setErro('');
    try {
      const res = await fetch('/antropometria/perfil-base', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          altura_cm: parseFloat(formAltura),
          peso_pre_gestacional: parseFloat(formPesoPre)
        })
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Erro ao atualizar dados base.');
      }
      setModalBaseAberto(false);
      setSucessoMsg('Dados pré-gestacionais atualizados com sucesso!');
      setTimeout(() => setSucessoMsg(''), 4000);
      await carregarDados();
    } catch (err) {
      setErro(err.message);
    } finally {
      setSalvandoBase(false);
    }
  };

  const handleSalvarRegistro = async (e) => {
    e.preventDefault();
    setSalvandoRegistro(true);
    setErro('');
    try {
      const payload = {
        peso_atual_kg: parseFloat(novoPeso),
        semana_gestacional: parseInt(novaSemana, 10),
        altura_uterina_cm: novaAU ? parseFloat(novaAU) : null,
        circunferencia_abdominal_cm: novaCircunferencia ? parseFloat(novaCircunferencia) : null,
        pressao_arterial: novaPressao.trim() || null,
        edema: novoEdema,
        observacoes: novaObs.trim() || null
      };

      const res = await fetch('/antropometria/registro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Erro ao registrar medição.');
      }

      setModalRegistroAberto(false);
      setNovoPeso('');
      setNovaAU('');
      setNovaCircunferencia('');
      setNovaPressao('');
      setNovaObs('');
      setSucessoMsg('Nova pesagem registrada com sucesso!');
      setTimeout(() => setSucessoMsg(''), 4000);
      await carregarDados();
    } catch (err) {
      setErro(err.message);
    } finally {
      setSalvandoRegistro(false);
    }
  };

  const handleExcluirRegistro = async (id) => {
    if (!window.confirm('Deseja realmente remover este registro de pesagem?')) return;
    try {
      const res = await fetch(`/antropometria/registro/${id}`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.ok) {
        setSucessoMsg('Registro removido.');
        setTimeout(() => setSucessoMsg(''), 3000);
        await carregarDados();
      }
    } catch (e) {}
  };

  if (carregando && !painel) {
    return (
      <div style={{ padding: '32px 16px', textAlign: 'center' }}>
        <p>Carregando painel antropométrico gestacional...</p>
      </div>
    );
  }

  const altura = painel?.altura_cm;
  const pesoPre = painel?.peso_pre_gestacional;
  const imcPre = painel?.imc_pre_gestacional;
  const classPre = painel?.classificacao_pre_gestacional;
  const pesoAtual = painel?.peso_atual_kg;
  const ganhoAcumulado = painel?.ganho_peso_acumulado_kg;
  const imcAtual = painel?.imc_atual;
  const atalah = painel?.avaliacao_atalah;
  const au = painel?.avaliacao_altura_uterina;
  const guia = painel?.guia_educativo;
  const historico = painel?.historico_registros || [];

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      {/* Cabeçalho */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.4rem' }}>Antropometria Gestacional</h2>
          <p className="text-muted" style={{ fontSize: '0.82rem', margin: '4px 0 0 0' }}>
            Curva de Atalah, Ganho Ponderal & Altura Uterina (Padrão MS / FEBRASGO)
          </p>
        </div>
        <span className="badge-gold">Oficial MS</span>
      </div>

      <TriageDisclaimer />

      {erro && (
        <div className="card" style={{ backgroundColor: '#FDEDEC', border: '1px solid #E74C3C', color: '#922B21', marginBottom: '16px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <AlertTriangle size={20} style={{ flexShrink: 0 }} />
              <span style={{ fontSize: '0.88rem' }}>{erro}</span>
            </div>
            {sessaoExpirada ? (
              <button
                onClick={() => { if (logout) logout(); window.location.href = '/login'; }}
                className="btn btn-primary"
                style={{ fontSize: '0.82rem', padding: '6px 14px', whiteSpace: 'nowrap' }}
              >
                Fazer Login Novamente
              </button>
            ) : (
              <button
                onClick={carregarDados}
                className="btn"
                style={{ fontSize: '0.82rem', padding: '4px 12px', border: '1px solid #E74C3C', color: '#922B21', backgroundColor: '#FFFFFF', cursor: 'pointer', borderRadius: 'var(--radius-sm)' }}
              >
                Tentar Novamente
              </button>
            )}
          </div>
        </div>
      )}

      {sucessoMsg && (
        <div className="card" style={{ backgroundColor: '#E8F8F0', border: '1px solid #27AE60', color: '#145A32', marginBottom: '16px' }}>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <CheckCircle2 size={20} />
            <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>{sucessoMsg}</span>
          </div>
        </div>
      )}

      {/* Alerta de Ganho Rápido / Suspeita de Edema */}
      {painel?.alerta_ganho_subito && (
        <div
          className="card"
          style={{
            backgroundColor: '#FFF9F0',
            border: '2px solid #E67E22',
            color: '#7E3C00',
            marginBottom: '16px'
          }}
        >
          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <AlertTriangle size={24} color="#E67E22" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong style={{ display: 'block', fontSize: '0.92rem', marginBottom: '4px' }}>
                Atenção ao Ganho Ponderal Recente
              </strong>
              <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.4' }}>
                {painel.mensagem_alerta}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Resumo de Antropometria Base (Altura e Peso Inicial) */}
      <div className="card" style={{ border: '1.5px solid var(--color-rosa)', marginBottom: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Scale size={20} color="var(--color-vinho)" />
            <h3 style={{ margin: 0, fontSize: '1.02rem', color: 'var(--color-vinho)' }}>Dados Pré-Gestacionais</h3>
          </div>
          <button
            onClick={() => setModalBaseAberto(true)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-rosa)',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            {altura && pesoPre ? 'Editar' : 'Preencher Dados'}
          </button>
        </div>

        {altura && pesoPre ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', textAlign: 'center' }}>
            <div style={{ backgroundColor: 'var(--color-rosa-claro)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'block' }}>Altura</span>
              <strong style={{ fontSize: '1.1rem', color: 'var(--color-vinho)' }}>{altura} cm</strong>
            </div>
            <div style={{ backgroundColor: 'var(--color-rosa-claro)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'block' }}>Peso Inicial</span>
              <strong style={{ fontSize: '1.1rem', color: 'var(--color-vinho)' }}>{pesoPre} kg</strong>
            </div>
            <div style={{ backgroundColor: 'var(--color-rosa-claro)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'block' }}>IMC Inicial</span>
              <strong style={{ fontSize: '1.1rem', color: 'var(--color-vinho)' }}>{imcPre}</strong>
              <span style={{ fontSize: '0.68rem', display: 'block', color: 'var(--color-rosa)', fontWeight: 600 }}>
                {classPre?.categoria}
              </span>
            </div>
          </div>
        ) : (
          <div style={{ padding: '12px', textAlign: 'center', backgroundColor: '#FFF5F7', borderRadius: 'var(--radius-md)' }}>
            <p style={{ margin: '0 0 8px 0', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
              Informe sua altura e peso de antes da gravidez para calcularmos sua Curva de Atalah personalizada.
            </p>
            <button
              onClick={() => setModalBaseAberto(true)}
              className="btn btn-primary"
              style={{ fontSize: '0.85rem', padding: '6px 16px' }}
            >
              Cadastrar Altura e Peso Inicial
            </button>
          </div>
        )}

        {classPre && (
          <div style={{ marginTop: '12px', padding: '10px', backgroundColor: '#FDFBFC', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--color-gold)' }}>
            <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--color-text)' }}>
              🎯 <strong>Meta de Ganho Total:</strong> {classPre.meta_descricao}
            </p>
          </div>
        )}
      </div>

      {/* Card de Ganho Atual & Última Pesagem */}
      <div className="card" style={{ marginBottom: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color="var(--color-vinho)" />
            <h3 style={{ margin: 0, fontSize: '1.02rem', color: 'var(--color-vinho)' }}>
              Evolução {painel?.semana_gestacional_atual ? `na ${painel.semana_gestacional_atual}ª Semana` : 'Gestacional'}
            </h3>
          </div>
          <button
            onClick={() => setModalRegistroAberto(true)}
            className="btn btn-primary"
            style={{ fontSize: '0.82rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            <Plus size={16} /> Nova Pesagem
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
          <div style={{ padding: '12px', backgroundColor: '#FAF6F7', borderRadius: 'var(--radius-md)', border: '1px solid #F0E6E8' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', display: 'block' }}>Último Peso Medido</span>
            <strong style={{ fontSize: '1.35rem', color: 'var(--color-vinho)' }}>
              {typeof pesoAtual === 'number' ? `${pesoAtual.toFixed(1)} kg` : (pesoAtual ? `${pesoAtual} kg` : 'Sem registros')}
            </strong>
            {imcAtual && (
              <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                IMC atual: <strong>{imcAtual}</strong>
              </span>
            )}
          </div>

          <div style={{ padding: '12px', backgroundColor: '#FAF6F7', borderRadius: 'var(--radius-md)', border: '1px solid #F0E6E8' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', display: 'block' }}>Ganho de Peso Total</span>
            <strong style={{ fontSize: '1.35rem', color: (typeof ganhoAcumulado === 'number' && ganhoAcumulado >= 0) ? '#27AE60' : '#E67E22' }}>
              {(typeof ganhoAcumulado === 'number' && !isNaN(ganhoAcumulado))
                ? `${ganhoAcumulado > 0 ? '+' : ''}${ganhoAcumulado.toFixed(1)} kg`
                : '--'}
            </strong>
            {classPre && typeof ganhoAcumulado === 'number' && !isNaN(ganhoAcumulado) && (
              <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                Meta: {classPre.ganho_total_min} a {classPre.ganho_total_max} kg
              </span>
            )}
          </div>
        </div>

        {/* Diagnóstico da Curva de Atalah Atual */}
        {atalah && (
          <div
            style={{
              padding: '12px',
              borderRadius: 'var(--radius-md)',
              borderLeft: `4px solid ${atalah.cor}`,
              backgroundColor: '#FFFFFF',
              border: `1px solid ${atalah.cor}33`,
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontWeight: 700, fontSize: '0.92rem', color: atalah.cor }}>
                Classificação Atalah: {atalah.diagnostico}
              </span>
              <span className="badge-gold" style={{ fontSize: '0.7rem' }}>Semana {atalah.semana}</span>
            </div>
            <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--color-text)', lineHeight: '1.4' }}>
              {atalah.orientacao}
            </p>

            {/* Barra Visual dos Limites de Atalah */}
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                <span>Baixo Peso (&lt;{atalah.limite_baixo})</span>
                <span style={{ color: '#27AE60', fontWeight: 600 }}>Adequado ({atalah.limite_baixo}-{atalah.limite_adequado})</span>
                <span>Sobrepeso ({atalah.limite_adequado}-{atalah.limite_sobrepeso})</span>
                <span>Obesidade (&ge;{atalah.limite_sobrepeso})</span>
              </div>
              <div style={{ height: '8px', borderRadius: '4px', backgroundColor: '#E0E0E0', display: 'flex', overflow: 'hidden' }}>
                <div style={{ flex: 1, backgroundColor: '#E67E22' }} title="Baixo Peso" />
                <div style={{ flex: 2, backgroundColor: '#27AE60' }} title="Adequado" />
                <div style={{ flex: 1.5, backgroundColor: '#F39C12' }} title="Sobrepeso" />
                <div style={{ flex: 1, backgroundColor: '#C0392B' }} title="Obesidade" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Avaliação da Altura Uterina */}
      {au && (
        <div className="card" style={{ marginBottom: '14px', borderLeft: `4px solid ${au.cor}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--color-vinho)' }}>
              Altura Uterina: {au.altura_uterina_cm} cm
            </h4>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: au.cor }}>
              {au.status}
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: '1.4' }}>
            {au.detalhe}
          </p>
          <span style={{ display: 'block', fontSize: '0.74rem', color: 'var(--color-text-muted)', marginTop: '6px' }}>
            Faixa esperada P10 a P90 para a {au.semana}ª semana: de {au.p10} cm a {au.p90} cm.
          </span>
        </div>
      )}

      {/* Guias e Informações Interativas */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
        <button
          className={`btn ${secaoAberta === 'atalah' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, fontSize: '0.82rem', padding: '8px 4px' }}
          onClick={() => setSecaoAberta('atalah')}
        >
          <Activity size={16} style={{ marginRight: '4px' }} /> Curva & Tabela
        </button>
        <button
          className={`btn ${secaoAberta === 'guia' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, fontSize: '0.82rem', padding: '8px 4px' }}
          onClick={() => setSecaoAberta('guia')}
        >
          <BookOpen size={16} style={{ marginRight: '4px' }} /> Guia Nutricional
        </button>
        <button
          className={`btn ${secaoAberta === 'historico' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, fontSize: '0.82rem', padding: '8px 4px' }}
          onClick={() => setSecaoAberta('historico')}
        >
          <Calendar size={16} style={{ marginRight: '4px' }} /> Histórico ({historico.length})
        </button>
      </div>

      {/* SEÇÃO 1: Curva de Atalah Explicada */}
      {secaoAberta === 'atalah' && (
        <div className="card">
          <h3 style={{ fontSize: '1rem', color: 'var(--color-vinho)', marginBottom: '8px' }}>
            O que é a Curva de Atalah?
          </h3>
          <p style={{ fontSize: '0.85rem', lineHeight: '1.45', color: 'var(--color-text)' }}>
            A Curva de Atalah é o instrumento oficial padronizado pelo <strong>Ministério da Saúde do Brasil</strong> e pela <strong>FEBRASGO</strong> para acompanhar o estado nutricional da gestante a cada consulta.
          </p>
          <p style={{ fontSize: '0.85rem', lineHeight: '1.45', color: 'var(--color-text)' }}>
            Diferente do IMC tradicional de adultos (que é fixo), o IMC gestacional evolui semana a semana para respeitar o crescimento normal do bebê, da placenta e o acúmulo de líquido amniótico.
          </p>

          <div style={{ marginTop: '12px', padding: '10px', backgroundColor: '#FAF6F7', borderRadius: 'var(--radius-md)' }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '0.88rem', color: 'var(--color-vinho)' }}>
              Faixas de Ganho Ponderal Recomendadas (IOM / OMS):
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '6px', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #EEE' }}>
                <span><strong>Baixo Peso Inicial</strong> (IMC &lt; 18,5):</span>
                <span style={{ color: '#E67E22', fontWeight: 600 }}>12,5 a 18,0 kg</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #EEE' }}>
                <span><strong>Adequado Inicial</strong> (IMC 18,5 a 24,9):</span>
                <span style={{ color: '#27AE60', fontWeight: 600 }}>11,5 a 16,0 kg</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #EEE' }}>
                <span><strong>Sobrepeso Inicial</strong> (IMC 25,0 a 29,9):</span>
                <span style={{ color: '#F39C12', fontWeight: 600 }}>7,0 a 11,5 kg</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                <span><strong>Obesidade Inicial</strong> (IMC &ge; 30,0):</span>
                <span style={{ color: '#C0392B', fontWeight: 600 }}>5,0 a 9,0 kg</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SEÇÃO 2: Guia Nutricional Rico */}
      {secaoAberta === 'guia' && guia && (
        <div>
          {/* Mitos e Verdades */}
          <div className="card" style={{ marginBottom: '14px' }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--color-vinho)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={18} color="var(--color-gold)" /> Mitos & Fatos sobre o Peso na Gravidez
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {guia.mitos_e_verdades.map((mv, idx) => (
                <div key={idx} style={{ padding: '10px', backgroundColor: '#FAF6F7', borderRadius: 'var(--radius-sm)' }}>
                  <strong style={{ fontSize: '0.85rem', color: 'var(--color-vinho)', display: 'block', marginBottom: '2px' }}>
                    ❌ {mv.mito}
                  </strong>
                  <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: '1.4' }}>
                    ✅ {mv.fato}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Para Onde Vai o Peso? */}
          <div className="card" style={{ marginBottom: '14px' }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--color-vinho)', marginBottom: '10px' }}>
              Para onde vai o peso da gravidez?
            </h3>
            <p className="text-muted" style={{ fontSize: '0.8rem', margin: '0 0 10px 0' }}>
              Você não está acumulando apenas gordura. Veja a distribuição anatômica média ao final dos 9 meses:
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '6px' }}>
              {guia.distribuicao_peso_fetal.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px 10px',
                    backgroundColor: idx % 2 === 0 ? '#FFFFFF' : '#FFF9FA',
                    borderRadius: '4px',
                    border: '1px solid #F5EAEB'
                  }}
                >
                  <div>
                    <strong style={{ fontSize: '0.85rem', color: 'var(--color-vinho)' }}>{item.componente}</strong>
                    <span style={{ display: 'block', fontSize: '0.74rem', color: 'var(--color-text-muted)' }}>
                      {item.descricao}
                    </span>
                  </div>
                  <span className="badge-rosa" style={{ fontSize: '0.78rem', fontWeight: 700 }}>
                    {item.media_kg}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Micronutrientes Essenciais */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', color: 'var(--color-vinho)', marginBottom: '10px' }}>
              Micronutrientes Indispensáveis
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {guia.micronutrientes_essenciais.map((nutri, idx) => (
                <div key={idx} style={{ padding: '10px', backgroundColor: '#FDFBFC', border: '1px solid #F0E6E8', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <strong style={{ fontSize: '0.88rem', color: 'var(--color-vinho)' }}>{nutri.nutriente}</strong>
                    <Heart size={16} color="var(--color-rosa)" />
                  </div>
                  <p style={{ margin: '0 0 6px 0', fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: '1.35' }}>
                    {nutri.importancia}
                  </p>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    🥗 <strong>Fontes:</strong> {nutri.fontes_alimentos}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SEÇÃO 3: Histórico de Registros */}
      {secaoAberta === 'historico' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--color-vinho)', margin: 0 }}>Histórico de Pesagens</h3>
            <button
              onClick={() => setModalRegistroAberto(true)}
              className="btn btn-primary"
              style={{ fontSize: '0.78rem', padding: '4px 10px' }}
            >
              + Adicionar
            </button>
          </div>

          {historico.length === 0 ? (
            <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.85rem', margin: '20px 0' }}>
              Nenhuma pesagem registrada ainda. Toque em "Nova Pesagem" para começar o acompanhamento da curva!
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {historico.map((reg) => (
                <div
                  key={reg.id}
                  style={{
                    padding: '10px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: '#FAF6F7',
                    border: '1px solid #F0E6E8',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <strong style={{ fontSize: '0.98rem', color: 'var(--color-vinho)' }}>
                        {reg.peso_atual_kg} kg
                      </strong>
                      <span className="badge-rosa" style={{ fontSize: '0.7rem' }}>
                        {reg.semana_gestacional}ª semana
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'block' }}>
                      Data: {new Date(reg.data_registro + 'T12:00:00').toLocaleDateString('pt-BR')}
                      {reg.altura_uterina_cm ? ` • AU: ${reg.altura_uterina_cm} cm` : ''}
                      {reg.pressao_arterial ? ` • PA: ${reg.pressao_arterial}` : ''}
                      {reg.edema && reg.edema !== 'ausente' ? ` • Edema: ${reg.edema}` : ''}
                    </span>
                    {reg.observacoes && (
                      <span style={{ fontSize: '0.74rem', color: 'var(--color-text)', fontStyle: 'italic', display: 'block', marginTop: '2px' }}>
                        "{reg.observacoes}"
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => handleExcluirRegistro(reg.id)}
                    style={{ background: 'transparent', border: 'none', color: '#999', cursor: 'pointer', padding: '6px' }}
                    title="Excluir medição"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MODAL: Nova Pesagem / Medição */}
      {modalRegistroAberto && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '16px'
          }}
        >
          <div className="card" style={{ maxWidth: '440px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3 style={{ margin: '0 0 12px 0', color: 'var(--color-vinho)' }}>Registrar Pesagem & Medição</h3>

            <form onSubmit={handleSalvarRegistro}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Peso Atual (kg) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="30"
                    max="250"
                    required
                    value={novoPeso}
                    onChange={(e) => setNovoPeso(e.target.value)}
                    placeholder="Ex: 68.5"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Semana Gestacional *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="43"
                    required
                    value={novaSemana}
                    onChange={(e) => setNovaSemana(e.target.value)}
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Altura Uterina (cm)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="5"
                    max="50"
                    value={novaAU}
                    onChange={(e) => setNovaAU(e.target.value)}
                    placeholder="Ex: 24"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Circunf. Abdominal (cm)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={novaCircunferencia}
                    onChange={(e) => setNovaCircunferencia(e.target.value)}
                    placeholder="Ex: 92"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Pressão Arterial
                  </label>
                  <input
                    type="text"
                    value={novaPressao}
                    onChange={(e) => setNovaPressao(e.target.value)}
                    placeholder="Ex: 120x80"
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Inchaço / Edema
                  </label>
                  <select
                    value={novoEdema}
                    onChange={(e) => setNovoEdema(e.target.value)}
                    className="input"
                    style={{ width: '100%' }}
                  >
                    <option value="ausente">Ausente (Normal)</option>
                    <option value="+/4+">Leve (+/4+)</option>
                    <option value="++/4+">Moderado (++/4+)</option>
                    <option value="+++/4+">Intenso (+++/4+)</option>
                    <option value="++++/4+">Generalizado (++++/4+)</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Anotações / Observações da Consulta
                </label>
                <textarea
                  rows="2"
                  value={novaObs}
                  onChange={(e) => setNovaObs(e.target.value)}
                  placeholder="Ex: Medição feita na consulta com Dr. Ricardo; bebê ativo."
                  className="input"
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setModalRegistroAberto(false)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem' }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={salvandoRegistro}
                  className="btn btn-primary"
                  style={{ fontSize: '0.85rem' }}
                >
                  {salvandoRegistro ? 'Salvando...' : 'Salvar Medição'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Dados Pré-Gestacionais */}
      {modalBaseAberto && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '16px'
          }}
        >
          <div className="card" style={{ maxWidth: '400px', width: '100%' }}>
            <h3 style={{ margin: '0 0 8px 0', color: 'var(--color-vinho)' }}>Dados Pré-Gestacionais</h3>
            <p className="text-muted" style={{ fontSize: '0.82rem', margin: '0 0 14px 0' }}>
              Sua altura e o peso antes de engravidar são o ponto de partida para calcularmos o ganho saudável pela Curva de Atalah.
            </p>

            <form onSubmit={handleSalvarBase}>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Sua Altura em Centímetros (cm) *
                </label>
                <input
                  type="number"
                  step="1"
                  min="100"
                  max="220"
                  required
                  value={formAltura}
                  onChange={(e) => setFormAltura(e.target.value)}
                  placeholder="Ex: 165 (para 1,65 m)"
                  className="input"
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Peso Pré-Gestacional (kg) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="30"
                  max="220"
                  required
                  value={formPesoPre}
                  onChange={(e) => setFormPesoPre(e.target.value)}
                  placeholder="Ex: 62.0"
                  className="input"
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setModalBaseAberto(false)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem' }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={salvandoBase}
                  className="btn btn-primary"
                  style={{ fontSize: '0.85rem' }}
                >
                  {salvandoBase ? 'Salvando...' : 'Salvar Dados'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
