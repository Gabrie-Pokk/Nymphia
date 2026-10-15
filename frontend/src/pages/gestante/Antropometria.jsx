import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import TriageDisclaimer from '../../components/TriageDisclaimer';
import { apiFetch } from '../../utils/api';
import FullScreenSuccessModal from '../../components/FullScreenSuccessModal';
import GraficoGanhoPeso from '../../components/GraficoGanhoPeso';
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
  ShieldCheck,
  Sliders,
  Phone
} from 'lucide-react';

const hojeIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

const dataCurta = (iso) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('pt-BR') : '');

// Cores por gravidade dos alertas de pressão, inchaço e ganho rápido
const ESTILO_ALERTA = {
  urgente: { fundo: '#FDEDEC', borda: '#C0392B', texto: '#7B241C', rotulo: 'Urgente' },
  atencao: { fundo: '#FFF9F0', borda: '#E67E22', texto: '#7E3C00', rotulo: 'Atenção' }
};

// Números em kg no formato brasileiro (4,2 em vez de 4.23)
const formatarKg = (valor) =>
  valor === null || valor === undefined || Number.isNaN(Number(valor))
    ? '-'
    : Number(valor).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export default function Antropometria({ onBack }) {
  const { authHeaders, logout } = useAuth();
  const [painel, setPainel] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [sessaoExpirada, setSessaoExpirada] = useState(false);
  const [sucessoMsg, setSucessoMsg] = useState('');
  const [modalSucessoAberto, setModalSucessoAberto] = useState(false);
  const [modalSucessoDados, setModalSucessoDados] = useState(null);

  // Modais e formulários
  const [modalRegistroAberto, setModalRegistroAberto] = useState(false);
  const [modalBaseAberto, setModalBaseAberto] = useState(false);
  const [secaoAberta, setSecaoAberta] = useState('atalah'); // atalah | guia | historico

  // Guia Nutricional Personalizado por Exames
  const [mostrarSimuladorExames, setMostrarSimuladorExames] = useState(false);
  const [examesInterativos, setExamesInterativos] = useState({
    hemoglobina: '',
    ferritina: '',
    glicemia: '',
    vitamina_d: '',
    tsh: ''
  });

  // Form novo registro
  const [novoPeso, setNovoPeso] = useState('');
  // Sem semana padrão: antes vinha 24 e muita gente salvava assim
  const [novaSemana, setNovaSemana] = useState('');
  const [novaData, setNovaData] = useState(hojeIso());
  const [alertaRegistro, setAlertaRegistro] = useState(null);
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
      const data = await apiFetch('/antropometria/painel');
      setPainel(data);
      setNovaSemana(data.semana_gestacional_atual ?? '');
      if (data.altura_cm) setFormAltura(data.altura_cm);
      if (data.peso_pre_gestacional) setFormPesoPre(data.peso_pre_gestacional);

      // Pré-preenche exames interativos com valores registrados, se houver (não há leitura automática de laudo)
      const ident = data?.guia_educativo?.nutricao_personalizada_exames?.valores_identificados;
      if (ident) {
        setExamesInterativos((prev) => ({
          ...prev,
          hemoglobina: ident.hemoglobina ?? prev.hemoglobina,
          ferritina: ident.ferritina ?? prev.ferritina,
          glicemia: ident.glicemia ?? prev.glicemia,
          vitamina_d: ident.vitamina_d ?? prev.vitamina_d,
          tsh: ident.tsh ?? prev.tsh
        }));
      }
    } catch (err) {
      if (err.status === 401) {
        setSessaoExpirada(true);
        setErro('Sua sessão expirou ou não está autenticada. Por favor, faça login novamente para visualizar seus dados.');
      } else {
        setErro(err.message || 'Erro de conexão ao carregar painel antropométrico.');
      }
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
      await apiFetch('/antropometria/perfil-base', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          altura_cm: parseFloat(formAltura),
          peso_pre_gestacional: parseFloat(formPesoPre)
        })
      });
      setModalBaseAberto(false);
      setSucessoMsg('Dados pré-gestacionais atualizados com sucesso!');
      setModalSucessoDados({
        title: 'Dados Pré-Gestacionais Salvos! 📏',
        subtitle: 'Sua altura e peso pré-gestacional foram atualizados e calibraram o cálculo de IMC e ganho ponderal esperado.',
        highlightText: `Altura: ${formAltura} cm • Peso Inicial: ${formPesoPre} kg`,
        confirmButtonText: 'Ver Curvas Atualizadas'
      });
      setModalSucessoAberto(true);
      setTimeout(() => setSucessoMsg(''), 4000);
      await carregarDados();
    } catch (err) {
      setErro(err.message || 'Erro ao atualizar dados pré-gestacionais.');
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
        // Com DUM o servidor calcula a semana pela data; o número daqui só vale sem DUM
        semana_gestacional: parseInt(novaSemana, 10) || 1,
        data_registro: novaData || null,
        altura_uterina_cm: novaAU ? parseFloat(novaAU) : null,
        circunferencia_abdominal_cm: novaCircunferencia ? parseFloat(novaCircunferencia) : null,
        pressao_arterial: novaPressao.trim() || null,
        edema: novoEdema,
        observacoes: novaObs.trim() || null
      };

      const salvo = await apiFetch('/antropometria/registro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      setModalRegistroAberto(false);
      const alertas = salvo?.alertas || [];
      const urgente = alertas.find((a) => a.nivel === 'urgente');
      if (urgente) {
        // Pressão alta não pode ficar escondida atrás de um "salvo com sucesso"
        setAlertaRegistro(urgente);
      } else {
        setSucessoMsg('Nova pesagem registrada com sucesso!');
        setModalSucessoDados({
          title: 'Pesagem registrada',
          subtitle: alertas.length
            ? alertas.map((a) => a.titulo).join(' • ')
            : 'Sua pesagem foi comparada com a recomendação brasileira de ganho de peso (FEBRASGO 2023).',
          highlightText: `Semana ${salvo?.semana_gestacional ?? novaSemana} • ${novoPeso} kg ${novaAU ? '• Altura Uterina: ' + novaAU + ' cm' : ''}`,
          confirmButtonText: 'Continuar no Painel'
        });
        setModalSucessoAberto(true);
      }
      setNovaData(hojeIso());

      setNovoPeso('');
      setNovaAU('');
      setNovaCircunferencia('');
      setNovaPressao('');
      setNovaObs('');
      setTimeout(() => setSucessoMsg(''), 4000);
      await carregarDados();
    } catch (err) {
      setErro(err.message || 'Erro ao registrar medição.');
    } finally {
      setSalvandoRegistro(false);
    }
  };

  const handleExcluirRegistro = async (id) => {
    if (!window.confirm('Deseja realmente remover este registro de pesagem?')) return;
    try {
      await apiFetch(`/antropometria/registro/${id}`, {
        method: 'DELETE'
      });
      setSucessoMsg('Registro removido.');
      setTimeout(() => setSucessoMsg(''), 3000);
      await carregarDados();
    } catch (e) {
      setErro(e.message || 'Erro ao remover medição.');
    }
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
  const ganhoUFRJ = painel?.avaliacao_ganho_ufrj || painel?.avaliacao_atalah;
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
            Ganho de peso pela referência brasileira & Altura Uterina (P10-P90)
          </p>
        </div>
        <span className="badge-gold">Padrão MS 2022</span>
      </div>

      <TriageDisclaimer />

      {/* Aviso Clínico de Limitação de Escopo (Gestante Adolescente ou Gestação Múltipla) */}
      {ganhoUFRJ?.fora_do_escopo && (
        <div
          className="card"
          style={{
            backgroundColor: '#FFFBEB',
            border: '1px solid #FCD34D',
            borderLeft: '4px solid #D97706',
            color: '#78350F',
            marginBottom: '16px'
          }}
        >
          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <AlertTriangle size={20} color="#D97706" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong style={{ fontSize: '0.88rem', display: 'block', marginBottom: '2px' }}>
                Aviso Clínico de Escopo (Conformidade MS / FEBRASGO)
              </strong>
              <span style={{ fontSize: '0.82rem', lineHeight: '1.45', display: 'block' }}>
                {ganhoUFRJ.aviso_escopo}
              </span>
            </div>
          </div>
        </div>
      )}

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

      {/* Alertas: pressão alta, inchaço intenso e ganho rápido (do mais grave para o mais leve) */}
      {(painel?.alertas || []).map((alerta, i) => {
        const estilo = ESTILO_ALERTA[alerta.nivel] || ESTILO_ALERTA.atencao;
        return (
          <div
            key={`${alerta.tipo}-${i}`}
            className="card"
            role="alert"
            style={{ backgroundColor: estilo.fundo, border: `2px solid ${estilo.borda}`, color: estilo.texto, marginBottom: '16px' }}
          >
            <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
              <AlertTriangle size={24} color={estilo.borda} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ display: 'block', fontSize: '0.92rem', marginBottom: '4px' }}>
                  {estilo.rotulo}: {alerta.titulo}
                </strong>
                <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.4' }}>{alerta.orientacao}</p>
                {alerta.nivel === 'urgente' && (
                  <a
                    href="tel:192"
                    className="btn"
                    style={{ marginTop: '8px', display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: estilo.borda, color: '#FFFFFF', fontSize: '0.82rem', padding: '6px 12px', borderRadius: 'var(--radius-sm)', textDecoration: 'none' }}
                  >
                    <Phone size={14} /> Ligar para o SAMU (192)
                  </a>
                )}
              </div>
            </div>
          </div>
        );
      })}

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
              Informe sua altura e peso de antes da gravidez para calcularmos sua faixa de ganho de peso.
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

        {/* Avaliação do ganho de peso pela referência brasileira (FEBRASGO 2023) */}
        {ganhoUFRJ && (
          <div
            style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              borderLeft: `4px solid ${ganhoUFRJ.cor}`,
              backgroundColor: '#FFFFFF',
              border: `1px solid ${ganhoUFRJ.cor}33`,
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontWeight: 700, fontSize: '0.92rem', color: ganhoUFRJ.cor }}>
                Ganho de peso (referência brasileira): {ganhoUFRJ.diagnostico}
              </span>
              <span className="badge-gold" style={{ fontSize: '0.7rem' }}>
                Semana {ganhoUFRJ.semana}{ganhoUFRJ.data_pesagem ? ` • pesagem de ${dataCurta(ganhoUFRJ.data_pesagem)}` : ''}
              </span>
            </div>
            
            <p style={{ margin: '0 0 10px 0', fontSize: '0.84rem', color: 'var(--color-text)', lineHeight: '1.45' }}>
              {ganhoUFRJ.orientacao}
            </p>

            <div style={{ padding: '8px 10px', backgroundColor: '#F8F9FA', borderRadius: '6px', fontSize: '0.78rem', color: '#555', marginBottom: '8px' }}>
              <div><strong>Faixa recomendada para esta semana:</strong> {formatarKg(ganhoUFRJ.ganho_esperado_min_kg ?? ganhoUFRJ.limite_baixo)} a {formatarKg(ganhoUFRJ.ganho_esperado_max_kg ?? ganhoUFRJ.limite_adequado)} kg</div>
              {ganhoUFRJ.ganho_semanal_referencia && (
                <div style={{ marginTop: '2px' }}><strong>Ritmo semanal de referência:</strong> {ganhoUFRJ.ganho_semanal_referencia}</div>
              )}
            </div>

            {/* Barra Visual de Ganho Ponderal */}
            <div style={{ marginTop: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                <span>Abaixo (&lt;{formatarKg(ganhoUFRJ.ganho_esperado_min_kg ?? ganhoUFRJ.limite_baixo)} kg)</span>
                <span style={{ color: '#27AE60', fontWeight: 600 }}>Faixa Esperada ({formatarKg(ganhoUFRJ.ganho_esperado_min_kg ?? ganhoUFRJ.limite_baixo)} a {formatarKg(ganhoUFRJ.ganho_esperado_max_kg ?? ganhoUFRJ.limite_adequado)} kg)</span>
                <span>Acima (&gt;{formatarKg(ganhoUFRJ.ganho_esperado_max_kg ?? ganhoUFRJ.limite_adequado)} kg)</span>
              </div>
              <div style={{ height: '8px', borderRadius: '4px', backgroundColor: '#E0E0E0', display: 'flex', overflow: 'hidden' }}>
                <div style={{ flex: 1.2, backgroundColor: '#E67E22' }} title="Abaixo da Faixa" />
                <div style={{ flex: 2.2, backgroundColor: '#27AE60' }} title="Faixa Esperada" />
                <div style={{ flex: 1.2, backgroundColor: '#C0392B' }} title="Acima da Faixa" />
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
            {au.p10 != null
              ? `Faixa esperada (P10 a P90) para a ${au.semana_referencia ?? au.semana}ª semana: de ${String(au.p10).replace('.', ',')} cm a ${String(au.p90).replace('.', ',')} cm.`
              : ''}
            {au.data_medida ? ` Medida em ${dataCurta(au.data_medida)}.` : ''}
            {au.observacao ? ` ${au.observacao}` : ''}
          </span>
          {au.referencia && (
            <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
              Referência: {au.referencia}.
            </span>
          )}
        </div>
      )}

      {/* Guias e Informações Interativas */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
        <button
          className={`btn ${secaoAberta === 'ufrj' || secaoAberta === 'atalah' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, fontSize: '0.82rem', padding: '8px 4px' }}
          onClick={() => setSecaoAberta('ufrj')}
        >
          <Activity size={16} style={{ marginRight: '4px' }} /> Curva de ganho
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

      {/* SEÇÃO 1: Curva UFRJ / MS 2022 Explicada */}
      {(secaoAberta === 'ufrj' || secaoAberta === 'atalah') && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--color-vinho)', margin: 0 }}>
              Curvas brasileiras de ganho de peso (Ministério da Saúde 2022 / FEBRASGO 2023)
            </h3>
            <span className="badge-gold" style={{ fontSize: '0.7rem' }}>Vigente no Brasil</span>
          </div>
          
          {painel?.curva_ganho_recomendada ? (
            <div style={{ marginBottom: '14px' }}>
              <h4 style={{ margin: '0 0 2px 0', fontSize: '0.92rem', color: 'var(--color-vinho)' }}>Seu ganho de peso</h4>
              <p className="text-muted" style={{ fontSize: '0.76rem', margin: '0 0 8px 0' }}>
                Faixa recomendada para quem começou a gestação com IMC {classPre?.categoria?.toLowerCase() || ''} (FEBRASGO 2023).
                {(painel?.pontos_ganho || []).length === 0 ? ' Registre uma pesagem para ver seu ponto no gráfico.' : ' Toque num ponto para ver o valor.'}
              </p>
              <GraficoGanhoPeso curva={painel.curva_ganho_recomendada} pontos={painel.pontos_ganho || []} />
            </div>
          ) : (
            <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '12px' }}>
              Informe altura e peso de antes da gravidez para ver o gráfico do seu ganho de peso.
            </p>
          )}

          <p style={{ fontSize: '0.85rem', lineHeight: '1.45', color: 'var(--color-text)', marginBottom: '8px' }}>
            Em 2022 o <strong>Ministério da Saúde</strong> passou a usar, na Caderneta da Gestante, as <strong>curvas brasileiras de ganho de peso</strong> criadas pelo Consórcio Brasileiro de Nutrição Materno-Infantil (coordenado na UFRJ) a partir de gestantes brasileiras. Em 2023 a <strong>FEBRASGO</strong> publicou as faixas recomendadas abaixo.
          </p>
          <p style={{ fontSize: '0.82rem', lineHeight: '1.45', color: '#666', marginBottom: '12px' }}>
            Os valores são o ganho <strong>acumulado</strong> desde antes da gravidez. No 1º trimestre é normal ganhar pouco ou até perder um pouco de peso. Entre os marcos de 13, 27 e 40 semanas o app calcula a faixa em linha reta, que é uma aproximação das curvas oficiais.
          </p>

          <div style={{ padding: '12px', backgroundColor: '#FAF6F7', borderRadius: 'var(--radius-md)' }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.88rem', color: 'var(--color-vinho)' }}>
              Ganho de peso recomendado (FEBRASGO 2023):
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', fontSize: '0.8rem' }}>
              <div style={{ padding: '6px 0', borderBottom: '1px solid #EEE' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Baixo peso</strong>
                  <span style={{ color: '#E67E22', fontWeight: 700, fontSize: '0.9rem' }}>9,7 a 12,2 kg até 40 sem.</span>
                </div>
                <span style={{ display: 'block', fontSize: '0.72rem', color: '#666' }}>
                  IMC antes da gestação menor que 18,5 • até 13 sem.: 0,2 a 1,2 kg • até 27 sem.: 5,6 a 7,2 kg
                </span>
              </div>
              <div style={{ padding: '6px 0', borderBottom: '1px solid #EEE' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Adequado</strong>
                  <span style={{ color: '#27AE60', fontWeight: 700, fontSize: '0.9rem' }}>8,0 a 12,0 kg até 40 sem.</span>
                </div>
                <span style={{ display: 'block', fontSize: '0.72rem', color: '#666' }}>
                  IMC de 18,5 a menos de 25 • até 13 sem.: -1,8 a 0,7 kg • até 27 sem.: 3,1 a 6,3 kg
                </span>
              </div>
              <div style={{ padding: '6px 0', borderBottom: '1px solid #EEE' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Sobrepeso</strong>
                  <span style={{ color: '#F39C12', fontWeight: 700, fontSize: '0.9rem' }}>7,0 a 9,0 kg até 40 sem.</span>
                </div>
                <span style={{ display: 'block', fontSize: '0.72rem', color: '#666' }}>
                  IMC de 25 a menos de 30 • até 13 sem.: -1,6 a -0,05 kg • até 27 sem.: 2,3 a 3,7 kg
                </span>
              </div>
              <div style={{ padding: '6px 0',  }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Obesidade</strong>
                  <span style={{ color: '#C0392B', fontWeight: 700, fontSize: '0.9rem' }}>5,0 a 7,2 kg até 40 sem.</span>
                </div>
                <span style={{ display: 'block', fontSize: '0.72rem', color: '#666' }}>
                  IMC de 30 ou mais • até 13 sem.: -1,6 a -0,05 kg • até 27 sem.: 1,1 a 2,7 kg
                </span>
              </div>
            </div>
            <p style={{ fontSize: '0.7rem', color: '#888', margin: '10px 0 0' }}>
              Fonte: Surita FG et al., Rev Bras Ginecol Obstet 2023;45(2):104-108, com base em Kac G et al., Am J Clin Nutr 2021. Vale para gestante adulta com um bebê só.
            </p>
          </div>
        </div>
      )}

      {/* SEÇÃO 2: Guia Nutricional Rico Personalizado por Exames */}
      {secaoAberta === 'guia' && guia && (
        <div>
          {/* Recomendações Nutricionais Personalizadas Baseadas nos Exames */}
          <div className="card" style={{ marginBottom: '14px', borderLeft: '5px solid var(--color-rosa)', backgroundColor: '#FFFDFE' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={20} color="var(--color-rosa)" />
                <div>
                  <h3 style={{ fontSize: '1.05rem', color: 'var(--color-vinho)', margin: 0 }}>
                    Guia Nutricional Personalizado por Exames
                  </h3>
                  <span style={{ fontSize: '0.74rem', color: 'var(--color-text-muted)' }}>
                    FEBRASGO & Ministério da Saúde • Ferro, Hormônios, Vitaminas e Glicemia
                  </span>
                </div>
              </div>

              <button
                onClick={() => setMostrarSimuladorExames(!mostrarSimuladorExames)}
                className="btn btn-outline"
                style={{
                  fontSize: '0.74rem',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  borderColor: 'var(--color-dourado)',
                  color: 'var(--color-vinho)'
                }}
                title="Informar ou simular valores dos seus exames laboratoriais"
              >
                <Sliders size={13} style={{ marginRight: '4px' }} />
                {mostrarSimuladorExames ? 'Ocultar Valores' : 'Digitar Meus Exames'}
              </button>
            </div>

            {/* Formulário Rápido de Valores de Exames */}
            {mostrarSimuladorExames && (
              <div style={{ marginBottom: '14px', padding: '12px', backgroundColor: '#FAF6F7', borderRadius: 'var(--radius-md)', border: '1px solid #F0E6E8' }}>
                <p style={{ margin: '0 0 10px 0', fontSize: '0.8rem', color: 'var(--color-vinho)', fontWeight: 600 }}>
                  🧪 Digite os valores do seu último exame de sangue para calibrar seu plano alimentar:
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
                  <div>
                    <label style={{ fontSize: '0.74rem', display: 'block', marginBottom: '2px', fontWeight: 600 }}>Hemoglobina (g/dL)</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Ex: 11.8"
                      value={examesInterativos.hemoglobina}
                      onChange={(e) => setExamesInterativos({ ...examesInterativos, hemoglobina: e.target.value })}
                      className="input-field"
                      style={{ width: '100%', fontSize: '0.82rem', padding: '6px 8px' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.74rem', display: 'block', marginBottom: '2px', fontWeight: 600 }}>Ferritina (ng/mL)</label>
                    <input
                      type="number"
                      step="1"
                      placeholder="Ex: 35"
                      value={examesInterativos.ferritina}
                      onChange={(e) => setExamesInterativos({ ...examesInterativos, ferritina: e.target.value })}
                      className="input-field"
                      style={{ width: '100%', fontSize: '0.82rem', padding: '6px 8px' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.74rem', display: 'block', marginBottom: '2px', fontWeight: 600 }}>Glicemia Jejum (mg/dL)</label>
                    <input
                      type="number"
                      step="1"
                      placeholder="Ex: 84"
                      value={examesInterativos.glicemia}
                      onChange={(e) => setExamesInterativos({ ...examesInterativos, glicemia: e.target.value })}
                      className="input-field"
                      style={{ width: '100%', fontSize: '0.82rem', padding: '6px 8px' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.74rem', display: 'block', marginBottom: '2px', fontWeight: 600 }}>Vitamina D (ng/mL)</label>
                    <input
                      type="number"
                      step="1"
                      placeholder="Ex: 32"
                      value={examesInterativos.vitamina_d}
                      onChange={(e) => setExamesInterativos({ ...examesInterativos, vitamina_d: e.target.value })}
                      className="input-field"
                      style={{ width: '100%', fontSize: '0.82rem', padding: '6px 8px' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.74rem', display: 'block', marginBottom: '2px', fontWeight: 600 }}>TSH Tireoide (mUI/L)</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Ex: 2.1"
                      value={examesInterativos.tsh}
                      onChange={(e) => setExamesInterativos({ ...examesInterativos, tsh: e.target.value })}
                      className="input-field"
                      style={{ width: '100%', fontSize: '0.82rem', padding: '6px 8px' }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Lista de Biomarcadores com Recomendações Clínicas */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(guia?.nutricao_personalizada_exames?.biomarcadores || []).map((bio) => {
                let statusAtual = bio.status;
                let corAtual = bio.cor;
                let detalheAtual = bio.valor_detectado;

                // Mesmos critérios do servidor (anthropometry_service.processar_nutricao_baseada_em_exames)
                if (bio.id === 'ferro_hemoglobina' && (examesInterativos.hemoglobina || examesInterativos.ferritina)) {
                  const hb = parseFloat(examesInterativos.hemoglobina);
                  const ferr = parseFloat(examesInterativos.ferritina);
                  // Anemia é hemoglobina abaixo de 11; ferritina baixa sozinha é estoque baixo
                  const temAnemia = !isNaN(hb) && hb < 11.0;
                  const estoqueBaixo = !isNaN(ferr) && ferr < 30.0;
                  statusAtual = temAnemia
                    ? 'Atenção: hemoglobina abaixo de 11 g/dL, compatível com anemia. Converse com sua equipe.'
                    : estoqueBaixo
                      ? 'Atenção: estoque de ferro baixo (ferritina abaixo de 30). Converse com sua equipe.'
                      : 'Hemoglobina e ferro dentro do esperado';
                  corAtual = temAnemia ? '#C0392B' : estoqueBaixo ? '#E67E22' : '#27AE60';
                  detalheAtual = `Informado: ${!isNaN(hb) ? `Hb: ${hb} g/dL` : ''} ${!isNaN(ferr) ? `(Ferritina: ${ferr} ng/mL)` : ''}`.trim();
                } else if (bio.id === 'glicemia' && examesInterativos.glicemia) {
                  const glic = parseFloat(examesInterativos.glicemia);
                  if (!isNaN(glic)) {
                    if (glic >= 126) {
                      statusAtual = 'Atenção: jejum de 126 mg/dL ou mais. Mostre este exame para sua equipe o quanto antes.';
                      corAtual = '#C0392B';
                    } else if (glic >= 92) {
                      statusAtual = 'Atenção: jejum entre 92 e 125 mg/dL, faixa usada no critério de diabetes gestacional. Mostre para sua equipe.';
                      corAtual = '#E67E22';
                    } else {
                      statusAtual = 'Glicemia de jejum abaixo de 92 mg/dL';
                      corAtual = '#27AE60';
                    }
                    detalheAtual = `Informado: ${glic} mg/dL`;
                  }
                } else if (bio.id === 'vitamina_d' && examesInterativos.vitamina_d) {
                  const vit = parseFloat(examesInterativos.vitamina_d);
                  if (!isNaN(vit)) {
                    if (vit < 20) {
                      statusAtual = 'Atenção: vitamina D abaixo de 20 ng/mL (deficiência). Mostre para sua equipe.';
                      corAtual = '#E67E22';
                    } else if (vit < 30) {
                      statusAtual = 'Vitamina D abaixo de 30 ng/mL, valor recomendado para gestantes. Converse com sua equipe.';
                      corAtual = '#F39C12';
                    } else {
                      statusAtual = 'Vitamina D dentro do recomendado para gestantes (30 ng/mL ou mais)';
                      corAtual = '#27AE60';
                    }
                    detalheAtual = `Informado: ${vit} ng/mL`;
                  }
                } else if (bio.id === 'tsh_tireoide' && examesInterativos.tsh) {
                  const tsh = parseFloat(examesInterativos.tsh);
                  if (!isNaN(tsh)) {
                    // A faixa de TSH na gestação depende do trimestre e do laboratório: quem interpreta é a equipe
                    statusAtual = `TSH: ${tsh} mUI/L. Sua equipe interpreta pelo trimestre e pela referência do laboratório.`;
                    corAtual = '#C9A84C';
                    detalheAtual = `Informado: ${tsh} mUI/L`;
                  }
                }

                return (
                  <div
                    key={bio.id}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: '#FFFFFF',
                      border: `1.5px solid ${corAtual}`,
                      boxShadow: 'var(--shadow-xs)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap', gap: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '1.2rem' }}>{bio.icone}</span>
                        <strong style={{ fontSize: '0.92rem', color: 'var(--color-vinho)' }}>{bio.nome}</strong>
                      </div>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: 'var(--radius-full)',
                          backgroundColor: `${corAtual}18`,
                          color: corAtual,
                          border: `1px solid ${corAtual}40`
                        }}
                      >
                        {statusAtual}
                      </span>
                    </div>

                    {detalheAtual && (
                      <p style={{ margin: '0 0 6px 0', fontSize: '0.76rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                        {detalheAtual}
                      </p>
                    )}

                    <div style={{ fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.45 }}>
                      <strong style={{ color: 'var(--color-vinho)', display: 'block', marginBottom: '4px' }}>
                        🥗 Alimentos Estratégicos Recomendados:
                      </strong>
                      <ul style={{ margin: '0 0 6px 0', paddingLeft: '18px' }}>
                        {bio.alimentos_recomendados.map((ali, i) => (
                          <li key={i}>{ali}</li>
                        ))}
                      </ul>

                      {bio.sinergia_absorcao && (
                        <div style={{ padding: '6px 8px', backgroundColor: '#F0FAF4', borderRadius: '4px', border: '1px solid #D4EDDA', color: '#155724', fontSize: '0.78rem', marginBottom: '4px' }}>
                          {bio.sinergia_absorcao}
                        </div>
                      )}

                      {bio.inibidores_evitar && (
                        <div style={{ padding: '6px 8px', backgroundColor: '#FFF5F5', borderRadius: '4px', border: '1px solid #FFD1D8', color: '#7E1D2D', fontSize: '0.78rem' }}>
                          {bio.inibidores_evitar}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

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
                    Data da medida *
                  </label>
                  <input
                    type="date"
                    required
                    max={hojeIso()}
                    value={novaData}
                    onChange={(e) => setNovaData(e.target.value)}
                    className="input"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              {painel?.semana_pela_dum ? (
                <p className="text-muted" style={{ fontSize: '0.76rem', margin: '-4px 0 12px 0' }}>
                  A semana de gestação é calculada pela data da medida e pela sua DUM.
                </p>
              ) : (
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Semana de gestação no dia da medida *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="43"
                    required
                    value={novaSemana}
                    onChange={(e) => setNovaSemana(e.target.value)}
                    placeholder="Ex: 26"
                    className="input"
                    style={{ width: '100%' }}
                  />
                  <span className="text-muted" style={{ fontSize: '0.72rem' }}>
                    Para o app calcular sozinho, informe a data da última menstruação no cadastro clínico.
                  </span>
                </div>
              )}

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
                    placeholder="Ex: 120/80 ou 12 por 8"
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
              Sua altura e o peso antes de engravidar são o ponto de partida para calcularmos o ganho saudável pelas Curvas UFRJ / Ministério da Saúde (2022).
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

      {/* Pressão alta na pesagem que acabou de ser salva */}
      {alertaRegistro && (
        <div
          role="alertdialog"
          aria-modal="true"
          style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100, padding: '16px' }}
        >
          <div className="card" style={{ maxWidth: '420px', width: '100%', border: '2px solid #C0392B', backgroundColor: '#FFFFFF' }}>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
              <AlertTriangle size={28} color="#C0392B" style={{ flexShrink: 0 }} />
              <div>
                <h3 style={{ margin: '0 0 6px 0', color: '#7B241C', fontSize: '1.05rem' }}>{alertaRegistro.titulo}</h3>
                <p style={{ margin: '0 0 12px 0', fontSize: '0.88rem', lineHeight: '1.45', color: '#4A2020' }}>
                  {alertaRegistro.orientacao}
                </p>
                <p style={{ margin: '0 0 12px 0', fontSize: '0.78rem', color: '#7B241C' }}>A medida foi salva.</p>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <a href="tel:192" className="btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: '#C0392B', color: '#FFFFFF', textDecoration: 'none', padding: '8px 14px', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
                    <Phone size={16} /> Ligar para o SAMU (192)
                  </a>
                  <button type="button" className="btn btn-secondary" style={{ fontSize: '0.85rem' }} onClick={() => setAlertaRegistro(null)}>
                    Entendi
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmação de Salvamento em Tela Inteira */}
      <FullScreenSuccessModal
        isOpen={modalSucessoAberto}
        onClose={() => setModalSucessoAberto(false)}
        title={modalSucessoDados?.title || 'Salvo com Sucesso! 🌸'}
        subtitle={modalSucessoDados?.subtitle}
        highlightText={modalSucessoDados?.highlightText}
        confirmButtonText={modalSucessoDados?.confirmButtonText || 'Continuar'}
      />
    </div>
  );
}
