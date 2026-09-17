import React, { useState } from 'react';
import { Calendar, Heart, Shield, Plus, Trash2, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import TriageDisclaimer from '../../components/TriageDisclaimer';

export default function OnboardingClinico({ onCompleted }) {
  const { authHeaders } = useAuth();

  // REGRA SEÇÃO 13.1: Um ÚNICO objeto de estado para o formulário inteiro!
  // Nunca useState isolado por campo. Nunca defaultValue.
  const [formState, setFormState] = useState({
    // Etapa 1: Dados Pessoais e Obstétricos
    idade: 28,
    estado_civil: 'Casada / União Estável',
    escolaridade: 'Superior Completo',
    gestacoes_anteriores: 0,
    partos_normais: 0,
    partos_cesareos: 0,
    perdas_gestacionais: 0,

    // Etapa 2: DUM e DPP (Ambos sempre visíveis)
    dum: '',
    dpp: '',
    dpp_editada_manualmente: false,

    // Etapa 3: Histórico Familiar (Lista dinâmica)
    historico_familiar: [],
    novo_parente: 'mãe',
    nova_condicao: 'Hipertensão Arterial',

    // Etapa 4: Maternidade de Referência
    maternidade_nome: '',
    maternidade_endereco: '',
    maternidade_telefone: ''
  });

  const [etapa, setEtapa] = useState(1);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');

  // Atualização genérica de campo no estado único
  const updateField = (field, value) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  // Cálculo de DPP ao alterar DUM (Regra Seção 7.1 e 13.1)
  const handleDumChange = (e) => {
    const novaDum = e.target.value;
    let novaDpp = formState.dpp;

    // Se NÃO foi editada manualmente, calcula automaticamente DUM + 280 dias
    if (!formState.dpp_editada_manualmente && novaDum) {
      const d = new Date(novaDum + 'T12:00:00');
      if (!isNaN(d.getTime())) {
        d.setDate(d.getDate() + 280);
        novaDpp = d.toISOString().split('T')[0];
      }
    }

    setFormState((prev) => ({
      ...prev,
      dum: novaDum,
      dpp: novaDpp
    }));
  };

  // Edição manual da DPP
  const handleDppChange = (e) => {
    setFormState((prev) => ({
      ...prev,
      dpp: e.target.value,
      dpp_editada_manualmente: true // Trava edição manual para não ser sobrescrita por DUM
    }));
  };

  // Histórico familiar: adicionar item à lista
  const handleAdicionarHistorico = () => {
    if (!formState.nova_condicao.trim()) return;
    const novoItem = {
      parente: formState.novo_parente,
      condicao: formState.nova_condicao.trim()
    };
    setFormState((prev) => ({
      ...prev,
      historico_familiar: [...prev.historico_familiar, novoItem],
      nova_condicao: 'Hipertensão Arterial'
    }));
  };

  // Histórico familiar: remover item da lista
  const handleRemoverHistorico = (indexToRemove) => {
    setFormState((prev) => ({
      ...prev,
      historico_familiar: prev.historico_familiar.filter((_, idx) => idx !== indexToRemove)
    }));
  };

  const handleSubmitFinal = async () => {
    setErro('');
    if (!formState.dum || !formState.dpp) {
      setErro('Por favor, informe a data da última menstruação (DUM) e confirme a DPP.');
      setEtapa(2);
      return;
    }

    setCarregando(true);
    try {
      // 1. Salva perfil clínico
      const resPerfil = await fetch('/perfil-clinico', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          idade: Number(formState.idade),
          estado_civil: formState.estado_civil,
          escolaridade: formState.escolaridade,
          gestacoes_anteriores: Number(formState.gestacoes_anteriores),
          partos_normais: Number(formState.partos_normais),
          partos_cesareos: Number(formState.partos_cesareos),
          perdas_gestacionais: Number(formState.perdas_gestacionais),
          dum: formState.dum,
          dpp: formState.dpp,
          dpp_editada_manualmente: formState.dpp_editada_manualmente,
          maternidade_nome: formState.maternidade_nome || "Hospital da Mulher / Maternidade Geral",
          maternidade_endereco: formState.maternidade_endereco || "Centro",
          maternidade_telefone: formState.maternidade_telefone || "192"
        })
      });

      if (!resPerfil.ok && resPerfil.status !== 409) {
        const d = await resPerfil.json();
        throw new Error(d.detail || 'Erro ao registrar perfil clínico.');
      }

      // 2. Salva histórico familiar item por item
      for (const item of formState.historico_familiar) {
        await fetch('/historico-familiar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...authHeaders() },
          body: JSON.stringify(item)
        });
      }

      // Salva maternidade no cache local para resiliência offline
      localStorage.setItem('nymphia_maternidade_cache', JSON.stringify({
        nome: formState.maternidade_nome || "Hospital da Mulher / Maternidade Geral",
        endereco: formState.maternidade_endereco || "Centro",
        telefone: formState.maternidade_telefone || "192"
      }));

      onCompleted();
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div style={{ maxWidth: '520px', margin: '0 auto', padding: '16px' }}>
      {/* Indicador de Etapas */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-vinho)' }}>
            Etapa {etapa} de 4
          </span>
          <span className="badge-gold">Onboarding Clínico</span>
        </div>
        <div style={{ display: 'flex', gap: '6px', height: '6px' }}>
          {[1, 2, 3, 4].map((step) => (
            <div
              key={step}
              style={{
                flex: 1,
                borderRadius: '3px',
                backgroundColor: etapa >= step ? 'var(--color-rosa)' : 'var(--color-border)',
                transition: 'background-color 0.3s ease'
              }}
            />
          ))}
        </div>
      </div>

      {erro && (
        <div
          role="alert"
          style={{
            padding: '12px',
            backgroundColor: '#FDEEE9',
            color: '#8A2B1A',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            marginBottom: '16px',
            borderLeft: '4px solid #D9534F'
          }}
        >
          {erro}
        </div>
      )}

      {/* ETAPA 1: DADOS PESSOAIS E HISTÓRICO OBSTÉTRICO */}
      {etapa === 1 && (
        <div>
          <h2>Seu Histórico Obstétrico</h2>
          <p className="text-muted" style={{ marginBottom: '20px' }}>
            Essas informações calibram nossos modelos clínicos populacionais.
          </p>

          <div className="form-group">
            <label htmlFor="form-idade">Sua Idade</label>
            <input
              id="form-idade"
              type="number"
              className="form-control"
              min={12}
              max={60}
              value={formState.idade}
              onChange={(e) => updateField('idade', e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label htmlFor="form-gest">Gestações Anteriores</label>
              <input
                id="form-gest"
                type="number"
                className="form-control"
                min={0}
                value={formState.gestacoes_anteriores}
                onChange={(e) => updateField('gestacoes_anteriores', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="form-perdas">Perdas Gestacionais</label>
              <input
                id="form-perdas"
                type="number"
                className="form-control"
                min={0}
                value={formState.perdas_gestacionais}
                onChange={(e) => updateField('perdas_gestacionais', e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label htmlFor="form-normais">Partos Normais</label>
              <input
                id="form-normais"
                type="number"
                className="form-control"
                min={0}
                value={formState.partos_normais}
                onChange={(e) => updateField('partos_normais', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="form-cesareas">Cesáreas Prévias</label>
              <input
                id="form-cesareas"
                type="number"
                className="form-control"
                min={0}
                value={formState.partos_cesareos}
                onChange={(e) => updateField('partos_cesareos', e.target.value)}
              />
            </div>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            style={{ width: '100%', minHeight: '48px', marginTop: '16px' }}
            onClick={() => setEtapa(2)}
          >
            Avançar para DUM e DPP
            <ArrowRight size={18} />
          </button>
        </div>
      )}

      {/* ETAPA 2: DUM E DPP (AMBOS VISÍVEIS COM TRAVA MANUAL) */}
      {etapa === 2 && (
        <div>
          <h2>Data da Gestação</h2>
          <p className="text-muted" style={{ marginBottom: '16px' }}>
            Ambos os campos permanecem sempre visíveis para conferência com ultrassom.
          </p>

          <div className="form-group">
            <label htmlFor="form-dum">
              Data da Última Menstruação (DUM)
            </label>
            <input
              id="form-dum"
              type="date"
              className="form-control"
              value={formState.dum}
              onChange={handleDumChange}
              required
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
              Ao preencher a DUM, a DPP calcula automaticamente (+280 dias).
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="form-dpp">
              Data Provável do Parto (DPP)
              {formState.dpp_editada_manualmente && (
                <span className="badge-gold" style={{ marginLeft: '8px' }}>
                  Ajustada Manualmente
                </span>
              )}
            </label>
            <input
              id="form-dpp"
              type="date"
              className="form-control"
              value={formState.dpp}
              onChange={handleDppChange}
              required
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
              Médicos frequentemente ajustam a DPP por ultrassom de 1º trimestre. Se você editar este campo manualmente, alterações na DUM não irão sobrescrever sua escolha.
            </span>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => setEtapa(1)}
            >
              <ArrowLeft size={18} /> Voltar
            </button>
            <button
              type="button"
              className="btn btn-primary"
              style={{ flex: 1.5 }}
              onClick={() => {
                if (!formState.dum) {
                  setErro('Por favor, informe a DUM.');
                  return;
                }
                setErro('');
                setEtapa(3);
              }}
            >
              Avançar para Histórico <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* ETAPA 3: HISTÓRICO FAMILIAR DINÂMICO */}
      {etapa === 3 && (
        <div>
          <h2>Histórico Clínico Familiar</h2>
          <p className="text-muted" style={{ marginBottom: '16px' }}>
            O grau de parentesco altera o peso do risco genético obstétrico.
          </p>

          <div className="card" style={{ backgroundColor: '#FFFFFF', border: '1.5px dashed var(--color-border)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '8px', marginBottom: '12px' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label htmlFor="hist-parente">Parente</label>
                <select
                  id="hist-parente"
                  className="form-control"
                  value={formState.novo_parente}
                  onChange={(e) => updateField('novo_parente', e.target.value)}
                >
                  <option value="mãe">Mãe</option>
                  <option value="pai">Pai</option>
                  <option value="irmã">Irmã</option>
                  <option value="irmão">Irmão</option>
                  <option value="avó materna">Avó Materna</option>
                  <option value="avó paterna">Avó Paterna</option>
                  <option value="avô materno">Avô Materno</option>
                  <option value="avô paterno">Avô Paterno</option>
                </select>
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label htmlFor="hist-condicao">Condição Clínica</label>
                <select
                  id="hist-condicao"
                  className="form-control"
                  value={formState.nova_condicao}
                  onChange={(e) => updateField('nova_condicao', e.target.value)}
                >
                  <option value="Hipertensão Arterial">Hipertensão Arterial</option>
                  <option value="Pré-eclâmpsia">Pré-eclâmpsia</option>
                  <option value="Eclâmpsia">Eclâmpsia</option>
                  <option value="Diabetes Mellitus">Diabetes Mellitus</option>
                  <option value="Doença Cardíaca">Doença Cardíaca</option>
                  <option value="Trombose / Trombofilia">Trombose / Trombofilia</option>
                  <option value="Hipotireoidismo">Hipotireoidismo</option>
                </select>
              </div>
            </div>

            <button
              type="button"
              className="btn btn-outline"
              style={{ width: '100%', borderColor: 'var(--color-rosa)', color: 'var(--color-rosa)' }}
              onClick={handleAdicionarHistorico}
            >
              <Plus size={18} /> Adicionar ao Histórico
            </button>
          </div>

          {/* Lista de Condições Adicionadas */}
          <div style={{ marginTop: '16px', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '8px' }}>Condições Registradas:</h3>
            {formState.historico_familiar.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                Nenhuma condição adicionada até o momento. Se não houver histórico conhecido, você pode avançar.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {formState.historico_familiar.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      backgroundColor: 'var(--color-rosa-claro)',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border)'
                    }}
                  >
                    <div>
                      <strong style={{ color: 'var(--color-vinho)', textTransform: 'capitalize' }}>
                        {item.parente}:
                      </strong>{' '}
                      <span style={{ color: 'var(--color-text-main)' }}>{item.condicao}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoverHistorico(idx)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--color-vermelho)',
                        padding: '4px',
                        cursor: 'pointer'
                      }}
                      aria-label={`Remover ${item.condicao} de ${item.parente}`}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => setEtapa(2)}
            >
              <ArrowLeft size={18} /> Voltar
            </button>
            <button
              type="button"
              className="btn btn-primary"
              style={{ flex: 1.5 }}
              onClick={() => setEtapa(4)}
            >
              Avançar para Maternidade <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* ETAPA 4: MATERNIDADE DE REFERÊNCIA */}
      {etapa === 4 && (
        <div>
          <h2>Maternidade de Referência</h2>
          <p className="text-muted" style={{ marginBottom: '16px' }}>
            Usada pela tela de emergência com discagem direta e rota de trânsito em um toque.
          </p>

          <div className="form-group">
            <label htmlFor="mat-nome">Nome da Maternidade ou Hospital</label>
            <input
              id="mat-nome"
              type="text"
              className="form-control"
              placeholder="Ex: Maternidade Municipal Santa Maria"
              value={formState.maternidade_nome}
              onChange={(e) => updateField('maternidade_nome', e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="mat-end">Endereço Completo</label>
            <input
              id="mat-end"
              type="text"
              className="form-control"
              placeholder="Rua, número, bairro e cidade"
              value={formState.maternidade_endereco}
              onChange={(e) => updateField('maternidade_endereco', e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="mat-tel">Telefone de Emergência da Maternidade</label>
            <input
              id="mat-tel"
              type="tel"
              className="form-control"
              placeholder="Ex: 1133334444"
              value={formState.maternidade_telefone}
              onChange={(e) => updateField('maternidade_telefone', e.target.value)}
            />
          </div>

          <TriageDisclaimer />

          <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => setEtapa(3)}
            >
              <ArrowLeft size={18} /> Voltar
            </button>
            <button
              type="button"
              className="btn btn-primary"
              style={{ flex: 1.5 }}
              onClick={handleSubmitFinal}
              disabled={carregando}
            >
              {carregando ? 'Salvando Perfil...' : 'Concluir Onboarding'}
              <CheckCircle2 size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
