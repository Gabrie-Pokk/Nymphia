import React, { useState } from 'react';
import { Calendar, Heart, Shield, Plus, Trash2, ArrowRight, ArrowLeft, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import TriageDisclaimer from '../../components/TriageDisclaimer';

const TELEFONE_REGEX = /^(?:19[0-9]|\(?\d{2}\)?\s?\d{4,5}-?\d{4})$/;

export default function OnboardingClinico({ onCompleted }) {
  const { authHeaders } = useAuth();

  // REGRA SEÇÃO 13.1: Um ÚNICO objeto de estado para o formulário inteiro!
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

  const hoje = new Date().toISOString().split('T')[0];
  const limitePassadoDum = new Date(Date.now() - 320 * 86400000).toISOString().split('T')[0];

  // Cálculo da consistência obstétrica
  const totalDesfechos = Number(formState.partos_normais || 0) + Number(formState.partos_cesareos || 0) + Number(formState.perdas_gestacionais || 0);
  const totalGestacoes = Number(formState.gestacoes_anteriores || 0);
  const isInconsistenteObstetrico = totalDesfechos > totalGestacoes;

  const updateField = (field, value) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  const handleDumChange = (e) => {
    const novaDum = e.target.value;
    let novaDpp = formState.dpp;

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

  const handleDppChange = (e) => {
    setFormState((prev) => ({
      ...prev,
      dpp: e.target.value,
      dpp_editada_manualmente: true
    }));
  };

  const handleAddHistorico = () => {
    if (!formState.nova_condicao.trim()) return;
    const novoItem = {
      parente: formState.novo_parente,
      condicao: formState.nova_condicao.trim().slice(0, 100)
    };
    setFormState((prev) => ({
      ...prev,
      historico_familiar: [...prev.historico_familiar, novoItem],
      nova_condicao: ''
    }));
  };

  const handleRemoveHistorico = (index) => {
    setFormState((prev) => ({
      ...prev,
      historico_familiar: prev.historico_familiar.filter((_, i) => i !== index)
    }));
  };

  const avancarEtapa = () => {
    setErro('');
    if (etapa === 1) {
      if (formState.idade < 10 || formState.idade > 65) {
        setErro('Idade materna deve estar entre 10 e 65 anos.');
        return;
      }
      if (isInconsistenteObstetrico) {
        setErro(`Inconsistência obstétrica: A soma de partos (${formState.partos_normais + formState.partos_cesareos}) e perdas (${formState.perdas_gestacionais}) totaliza ${totalDesfechos}, o que não pode ser maior que o total de gestações anteriores (${totalGestacoes}).`);
        return;
      }
    }

    if (etapa === 2) {
      if (!formState.dum) {
        setErro('Por favor, informe a Data da Última Menstruação (DUM).');
        return;
      }
      if (formState.dum > hoje) {
        setErro('A DUM não pode ser uma data futura.');
        return;
      }
      if (formState.dum < limitePassadoDum) {
        setErro('A DUM não pode ser anterior a 320 dias (~45 semanas).');
        return;
      }
      if (!formState.dpp) {
        setErro('Por favor, defina a Data Provável do Parto (DPP).');
        return;
      }
      if (formState.dpp < formState.dum) {
        setErro('A DPP não pode ser anterior à DUM.');
        return;
      }
    }

    setEtapa((prev) => prev + 1);
  };

  const handleFinalizar = async (e) => {
    e.preventDefault();
    setErro('');

    if (formState.maternidade_telefone && formState.maternidade_telefone.trim()) {
      const tel = formState.maternidade_telefone.trim();
      if (!TELEFONE_REGEX.test(tel)) {
        setErro('Telefone da maternidade inválido. Digite um telefone com DDD ou número de emergência (ex: 192 ou (11) 98888-7777).');
        return;
      }
    }

    setCarregando(true);
    try {
      const perfilPayload = {
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
        maternidade_nome: formState.maternidade_nome.trim().slice(0, 120),
        maternidade_endereco: formState.maternidade_endereco.trim().slice(0, 200),
        maternidade_telefone: formState.maternidade_telefone.trim().slice(0, 25)
      };

      const resPerfil = await fetch('/perfil-clinico', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders()
        },
        body: JSON.stringify(perfilPayload)
      });

      if (!resPerfil.ok) {
        const d = await resPerfil.json();
        throw new Error(d.detail || 'Falha ao salvar dados obstétricos.');
      }

      for (const item of formState.historico_familiar) {
        await fetch('/historico-familiar', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...authHeaders()
          },
          body: JSON.stringify(item)
        });
      }

      if (formState.maternidade_nome) {
        localStorage.setItem('nymphia_maternidade_cache', JSON.stringify({
          nome: formState.maternidade_nome,
          endereco: formState.maternidade_endereco,
          telefone: formState.maternidade_telefone,
          latitude: formState.maternidade_latitude,
          longitude: formState.maternidade_longitude
        }));
      }

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
            Essas informações calibram nossos modelos clínicos populacionais com limites médicos reais.
          </p>

          <div className="form-group">
            <label htmlFor="form-idade">Sua Idade (10 a 65 anos)</label>
            <input
              id="form-idade"
              type="number"
              className="form-control"
              min={10}
              max={65}
              value={formState.idade}
              onChange={(e) => updateField('idade', Number(e.target.value))}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label htmlFor="form-gest">Gestações Anteriores (máx. 20)</label>
              <input
                id="form-gest"
                type="number"
                className="form-control"
                min={0}
                max={20}
                value={formState.gestacoes_anteriores}
                onChange={(e) => updateField('gestacoes_anteriores', Number(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="form-perdas">Perdas / Abortos (máx. 15)</label>
              <input
                id="form-perdas"
                type="number"
                className="form-control"
                min={0}
                max={15}
                value={formState.perdas_gestacionais}
                onChange={(e) => updateField('perdas_gestacionais', Number(e.target.value))}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label htmlFor="form-partos-normais">Partos Normais (máx. 20)</label>
              <input
                id="form-partos-normais"
                type="number"
                className="form-control"
                min={0}
                max={20}
                value={formState.partos_normais}
                onChange={(e) => updateField('partos_normais', Number(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="form-partos-cesareas">Cesáreas (máx. 10)</label>
              <input
                id="form-partos-cesareas"
                type="number"
                className="form-control"
                min={0}
                max={10}
                value={formState.partos_cesareos}
                onChange={(e) => updateField('partos_cesareos', Number(e.target.value))}
              />
            </div>
          </div>

          {/* Alerta de consistência obstétrica em tempo real */}
          {isInconsistenteObstetrico && (
            <div
              style={{
                backgroundColor: '#FDEEE9',
                color: '#8A2B1A',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                marginBottom: '16px',
                fontSize: '0.84rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <AlertTriangle size={20} />
              <span>
                <strong>Atenção Obstétrica:</strong> A soma de partos ({totalDesfechos - formState.perdas_gestacionais}) e perdas ({formState.perdas_gestacionais}) = {totalDesfechos}, não pode ser maior do que as gestações anteriores informadas ({totalGestacoes}).
              </span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="form-est-civ">Estado Civil</label>
            <select
              id="form-est-civ"
              className="form-control"
              value={formState.estado_civil}
              onChange={(e) => updateField('estado_civil', e.target.value)}
            >
              <option value="Solteira">Solteira</option>
              <option value="Casada / União Estável">Casada / União Estável</option>
              <option value="Divorciada / Separada">Divorciada / Separada</option>
              <option value="Viúva">Viúva</option>
              <option value="Outro">Outro</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="form-esc">Escolaridade</label>
            <select
              id="form-esc"
              className="form-control"
              value={formState.escolaridade}
              onChange={(e) => updateField('escolaridade', e.target.value)}
            >
              <option value="Fundamental Incompleto">Fundamental Incompleto</option>
              <option value="Fundamental Completo">Fundamental Completo</option>
              <option value="Médio Incompleto">Médio Incompleto</option>
              <option value="Médio Completo">Médio Completo</option>
              <option value="Superior Incompleto">Superior Incompleto</option>
              <option value="Superior Completo">Superior Completo</option>
              <option value="Pós-Graduação">Pós-Graduação</option>
            </select>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            style={{ width: '100%', minHeight: '48px', marginTop: '16px' }}
            onClick={avancarEtapa}
            disabled={isInconsistenteObstetrico}
          >
            Avançar para DUM e DPP
            <ArrowRight size={18} />
          </button>
        </div>
      )}

      {/* ETAPA 2: DUM E DPP */}
      {etapa === 2 && (
        <div>
          <h2>Datas Importantes</h2>
          <p className="text-muted" style={{ marginBottom: '20px' }}>
            A DUM calcula automaticamente sua Data Provável do Parto (DPP). Ambas são ajustáveis com segurança.
          </p>

          <div className="form-group">
            <label htmlFor="form-dum">
              DUM — Data da Última Menstruação <span style={{ color: 'var(--color-rosa)' }}>*</span>
            </label>
            <input
              id="form-dum"
              type="date"
              className="form-control"
              value={formState.dum}
              max={hoje}
              min={limitePassadoDum}
              onChange={handleDumChange}
              required
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '4px', display: 'block' }}>
              Deve estar nos últimos 320 dias e não pode ser futura.
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="form-dpp">
              DPP — Data Provável do Parto {formState.dpp_editada_manualmente ? '(Ajustada manualmente)' : '(Calculada: DUM + 40 semanas)'}
            </label>
            <input
              id="form-dpp"
              type="date"
              className="form-control"
              value={formState.dpp}
              min={formState.dum || hoje}
              onChange={handleDppChange}
              required
            />
            {formState.dpp_editada_manualmente && (
              <span style={{ fontSize: '0.78rem', color: 'var(--color-dourado)', marginTop: '4px', display: 'block' }}>
                ✓ Trava manual ativada: esta data prevalecerá para sua rotina clínica.
              </span>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '24px' }}>
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
              style={{ flex: 1 }}
              onClick={avancarEtapa}
            >
              Avançar para Histórico
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* ETAPA 3: HISTÓRICO FAMILIAR */}
      {etapa === 3 && (
        <div>
          <h2>Histórico Clínico Familiar</h2>
          <p className="text-muted" style={{ marginBottom: '20px' }}>
            Condições crônicas na família (especialmente hipertensão, diabetes e pré-eclâmpsia) auxiliam os algoritmos de prevenção.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr auto', gap: '8px', marginBottom: '16px' }}>
            <select
              className="form-control"
              value={formState.novo_parente}
              onChange={(e) => updateField('novo_parente', e.target.value)}
            >
              <option value="mãe">Mãe</option>
              <option value="pai">Pai</option>
              <option value="irmã">Irmã</option>
              <option value="irmão">Irmão</option>
              <option value="avó materna">Avó Materna</option>
              <option value="avô materno">Avô Materno</option>
              <option value="avó paterna">Avó Paterna</option>
              <option value="avô paterno">Avô Paterno</option>
              <option value="filho anterior">Filho Anterior</option>
            </select>

            <input
              type="text"
              className="form-control"
              placeholder="Ex: Pré-eclâmpsia, Diabetes..."
              value={formState.nova_condicao}
              maxLength={100}
              onChange={(e) => updateField('nova_condicao', e.target.value)}
            />

            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleAddHistorico}
              style={{ minHeight: '44px', padding: '0 16px' }}
            >
              <Plus size={18} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
            {formState.historico_familiar.map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 14px',
                  backgroundColor: '#FFFFFF',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border)'
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{item.parente}:</span>{' '}
                  <span>{item.condicao}</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveHistorico(idx)}
                  style={{ background: 'transparent', border: 'none', color: '#D9534F', cursor: 'pointer', padding: '4px' }}
                  title="Remover"
                  aria-label="Remover histórico familiar"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '24px' }}>
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
              style={{ flex: 1 }}
              onClick={() => setEtapa(4)}
            >
              Avançar para Maternidade
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* ETAPA 4: MATERNIDADE DE REFERÊNCIA */}
      {etapa === 4 && (
        <form onSubmit={handleFinalizar}>
          <h2>Maternidade de Referência</h2>
          <p className="text-muted" style={{ marginBottom: '20px' }}>
            O hospital ou maternidade vinculado ao seu plano ou SUS. Salvo localmente para abrir no botão de emergência mesmo sem internet.
          </p>

          
          {/* Busca e Mapeamento de Maternidade (Google Maps Assistido) */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.85rem', color: 'var(--color-vinho)', marginBottom: '6px' }}>
              📍 Seleção Rápida de Maternidades de Referência:
            </label>
            <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '6px' }}>
              {[
                { nome: 'Hospital e Maternidade Santa Joana', endereco: 'Rua Dr. Eduardo Amaro, 225 - Paraíso, São Paulo - SP', tel: '1150806000', lat: -23.5786, lng: -46.6433 },
                { nome: 'Hospital Maternidade Pro Matre Paulista', endereco: 'Al. Joaquim Eugênio de Lima, 383 - Bela Vista, São Paulo - SP', tel: '1132692233', lat: -23.5672, lng: -46.6508 },
                { nome: 'Maternidade Leonor Mendes de Barros (SUS)', endereco: 'Av. Celso Garcia, 2477 - Belenzinho, São Paulo - SP', tel: '1126948000', lat: -23.5385, lng: -46.5927 },
                { nome: 'Hospital das Clínicas da FMUSP (SUS)', endereco: 'Av. Dr. Enéas Carvalho de Aguiar, 255 - Cerqueira César, SP', tel: '1126610000', lat: -23.5574, lng: -46.6713 },
                { nome: 'Maternidade Darcy Vargas (SUS)', endereco: 'Rua São José Operário, 305 - Joinville - SC', tel: '4734615700', lat: -26.3045, lng: -48.8487 }
              ].map((m, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="btn btn-outline"
                  style={{ fontSize: '0.76rem', whiteSpace: 'nowrap', padding: '6px 10px', minHeight: '32px' }}
                  onClick={() => {
                    updateField('maternidade_nome', m.nome);
                    updateField('maternidade_endereco', m.endereco);
                    updateField('maternidade_telefone', m.tel);
                    updateField('maternidade_latitude', m.lat);
                    updateField('maternidade_longitude', m.lng);
                  }}
                >
                  📍 {m.nome.split(' ')[0]} {m.nome.split(' ')[1] || ''}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="form-mat-nome">Nome da Maternidade ou Hospital</label>
            <input
              id="form-mat-nome"
              type="text"
              className="form-control"
              placeholder="Ex: Maternidade Leonor Mendes de Barros"
              value={formState.maternidade_nome}
              maxLength={120}
              onChange={(e) => updateField('maternidade_nome', e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="form-mat-end">Endereço Completo</label>
            <input
              id="form-mat-end"
              type="text"
              className="form-control"
              placeholder="Av. Celso Garcia, 2477 - Belenzinho"
              value={formState.maternidade_endereco}
              maxLength={200}
              onChange={(e) => updateField('maternidade_endereco', e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="form-mat-tel">Telefone da Maternidade ou Pronto-Socorro</label>
            <input
              id="form-mat-tel"
              type="tel"
              className="form-control"
              placeholder="Ex: (11) 2694-8000 ou 192"
              value={formState.maternidade_telefone}
              maxLength={20}
              onChange={(e) => updateField('maternidade_telefone', e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '28px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => setEtapa(3)}
            >
              <ArrowLeft size={18} /> Voltar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ flex: 1 }}
              disabled={carregando}
            >
              {carregando ? 'Gravando Dados...' : 'Concluir Onboarding'}
              <CheckCircle2 size={18} />
            </button>
          </div>
        </form>
      )}

      <TriageDisclaimer />
    </div>
  );
}
