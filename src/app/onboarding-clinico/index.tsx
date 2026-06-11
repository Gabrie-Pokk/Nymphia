import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import ProgressBar from '@/components/progress-bar';
import SelectableChip from '@/components/selectable-chip';

export const PERFIL_CLINICO_KEY = '@nymphia/perfil_clinico';

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  primaryLight: '#FCE4EC',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
  error: '#B71C1C',
};

const TOTAL_STEPS = 4;

const CONDICOES_SAUDE: string[] = [
  'Hipertensão',
  'Diabetes',
  'Tireoide',
  'Lúpus',
  'Trombofilia',
  'Asma',
  'Doença renal',
  'Cardiopatia',
  'Cirurgia uterina',
  'Nenhuma',
];

const CONDICOES_FAMILIAR: string[] = [
  'Hipertensão',
  'Diabetes',
  'Tireoide',
  'Lúpus',
  'Trombofilia',
  'Asma',
  'Doença renal',
  'Cardiopatia',
  'Cirurgia uterina',
  'Pré-eclâmpsia',
  'Nenhuma',
];

type TipoDada = 'dum' | 'dpp';

type PerfilClinico = {
  tipoDada: TipoDada;
  data: string;
  semanaGestacional: number | null;
  condicoesSaude: string[];
  medicamentos: string;
  alergias: string;
  historicoFamiliar: string[];
  primeiraGestacao: boolean;
  partosAnteriores: number;
  aborto: boolean;
  partoPrematuro: boolean;
  preEclampsiaAnterior: boolean;
};

const ESTADO_INICIAL: PerfilClinico = {
  tipoDada: 'dum',
  data: '',
  semanaGestacional: null,
  condicoesSaude: [],
  medicamentos: '',
  alergias: '',
  historicoFamiliar: [],
  primeiraGestacao: true,
  partosAnteriores: 0,
  aborto: false,
  partoPrematuro: false,
  preEclampsiaAnterior: false,
};

function formatarData(texto: string): string {
  const n = texto.replace(/\D/g, '').slice(0, 8);
  if (n.length <= 2) return n;
  if (n.length <= 4) return `${n.slice(0, 2)}/${n.slice(2)}`;
  return `${n.slice(0, 2)}/${n.slice(2, 4)}/${n.slice(4)}`;
}

function calcularSemana(data: string, tipo: TipoDada): number | null {
  if (data.length < 10) return null;
  const [diaStr, mesStr, anoStr] = data.split('/');
  const dia = Number(diaStr);
  const mes = Number(mesStr);
  const ano = Number(anoStr);
  if (!dia || !mes || !ano || ano < 2000) return null;

  const dataObj = new Date(ano, mes - 1, dia);
  if (isNaN(dataObj.getTime())) return null;

  const hoje = new Date();

  if (tipo === 'dum') {
    const diffDias = Math.floor(
      (hoje.getTime() - dataObj.getTime()) / (1000 * 60 * 60 * 24),
    );
    const semanas = Math.floor(diffDias / 7);
    if (semanas < 1 || semanas > 42) return null;
    return semanas;
  } else {
    const diffDias = Math.ceil(
      (dataObj.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24),
    );
    const semana = 40 - Math.ceil(diffDias / 7);
    if (semana < 1 || semana > 42) return null;
    return semana;
  }
}

function toggleItem(lista: string[], item: string): string[] {
  if (item === 'Nenhuma') {
    return lista.includes('Nenhuma') ? [] : ['Nenhuma'];
  }
  const semNenhuma = lista.filter((c) => c !== 'Nenhuma');
  return semNenhuma.includes(item)
    ? semNenhuma.filter((c) => c !== item)
    : [...semNenhuma, item];
}

type SimNaoProps = {
  valor: boolean;
  onChange: (v: boolean) => void;
};

function SimNao({ valor, onChange }: SimNaoProps) {
  return (
    <View style={styles.simNao}>
      <Pressable
        style={[styles.simNaoOpcao, valor && styles.simNaoAtivo]}
        onPress={() => onChange(true)}
        accessibilityRole="radio"
        accessibilityState={{ selected: valor }}>
        <Text style={[styles.simNaoTexto, valor && styles.simNaoTextoAtivo]}>Sim</Text>
      </Pressable>
      <Pressable
        style={[styles.simNaoOpcao, !valor && styles.simNaoAtivo]}
        onPress={() => onChange(false)}
        accessibilityRole="radio"
        accessibilityState={{ selected: !valor }}>
        <Text style={[styles.simNaoTexto, !valor && styles.simNaoTextoAtivo]}>Não</Text>
      </Pressable>
    </View>
  );
}

export default function OnboardingClinicoScreen() {
  const [step, setStep] = useState(1);
  const [perfil, setPerfil] = useState<PerfilClinico>(ESTADO_INICIAL);
  const [focado, setFocado] = useState<string | null>(null);
  const [erro, setErro] = useState('');

  const set = <K extends keyof PerfilClinico>(campo: K, valor: PerfilClinico[K]) =>
    setPerfil((prev) => ({ ...prev, [campo]: valor }));

  const semanaCalculada = calcularSemana(perfil.data, perfil.tipoDada);

  const validarEtapa = (): boolean => {
    if (step === 1) {
      if (perfil.data.length < 10) {
        setErro('Digite uma data válida no formato DD/MM/AAAA.');
        return false;
      }
      if (semanaCalculada === null) {
        setErro('Data fora do período gestacional. Verifique e tente novamente.');
        return false;
      }
    }
    setErro('');
    return true;
  };

  const avancar = () => {
    if (!validarEtapa()) return;
    if (step < TOTAL_STEPS) {
      setStep(step + 1);
    } else {
      concluir();
    }
  };

  const voltar = () => {
    setErro('');
    setStep(step - 1);
  };

  const concluir = async () => {
    const dados: PerfilClinico = { ...perfil, semanaGestacional: semanaCalculada };
    await AsyncStorage.setItem(PERFIL_CLINICO_KEY, JSON.stringify(dados));
    router.replace('/(main)');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ProgressBar currentStep={step} totalSteps={TOTAL_STEPS} />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}>

          {/* ── ETAPA 1: DUM / DPP ── */}
          {step === 1 && (
            <View>
              <Text style={styles.titulo}>Quando é seu bebê?</Text>
              <Text style={styles.subtitulo}>
                Isso nos ajuda a calcular sua semana gestacional com precisão.
              </Text>

              <View style={styles.toggle}>
                <Pressable
                  style={[styles.toggleOpcao, perfil.tipoDada === 'dum' && styles.toggleAtivo]}
                  onPress={() => {
                    set('tipoDada', 'dum');
                    set('data', '');
                  }}>
                  <Text
                    style={[
                      styles.toggleSigla,
                      perfil.tipoDada === 'dum' && styles.toggleTextoAtivo,
                    ]}>
                    DUM
                  </Text>
                  <Text
                    style={[
                      styles.toggleDescricao,
                      perfil.tipoDada === 'dum' && styles.toggleTextoAtivo,
                    ]}>
                    Última menstruação
                  </Text>
                </Pressable>
                <Pressable
                  style={[styles.toggleOpcao, perfil.tipoDada === 'dpp' && styles.toggleAtivo]}
                  onPress={() => {
                    set('tipoDada', 'dpp');
                    set('data', '');
                  }}>
                  <Text
                    style={[
                      styles.toggleSigla,
                      perfil.tipoDada === 'dpp' && styles.toggleTextoAtivo,
                    ]}>
                    DPP
                  </Text>
                  <Text
                    style={[
                      styles.toggleDescricao,
                      perfil.tipoDada === 'dpp' && styles.toggleTextoAtivo,
                    ]}>
                    Data provável do parto
                  </Text>
                </Pressable>
              </View>

              <Text style={styles.label}>
                {perfil.tipoDada === 'dum'
                  ? 'Data da última menstruação'
                  : 'Data provável do parto'}
              </Text>
              <TextInput
                style={[styles.input, focado === 'data' && styles.inputFocado]}
                value={perfil.data}
                onChangeText={(t) => set('data', formatarData(t))}
                placeholder="DD/MM/AAAA"
                placeholderTextColor="#AAAAAA"
                keyboardType="numeric"
                maxLength={10}
                onFocus={() => setFocado('data')}
                onBlur={() => setFocado(null)}
              />

              {semanaCalculada !== null && (
                <View style={styles.semanaCard}>
                  <Text style={styles.semanaNumero}>{semanaCalculada}</Text>
                  <Text style={styles.semanaTexto}>semanas de gestação</Text>
                </View>
              )}
            </View>
          )}

          {/* ── ETAPA 2: Saúde ── */}
          {step === 2 && (
            <View>
              <Text style={styles.titulo}>Sua saúde</Text>
              <Text style={styles.subtitulo}>
                Selecione as condições que você tem ou já teve.
              </Text>

              <View style={styles.chips}>
                {CONDICOES_SAUDE.map((cond) => (
                  <SelectableChip
                    key={cond}
                    label={cond}
                    selected={perfil.condicoesSaude.includes(cond)}
                    onPress={() =>
                      set('condicoesSaude', toggleItem(perfil.condicoesSaude, cond))
                    }
                  />
                ))}
              </View>

              <Text style={styles.label}>Medicamentos em uso</Text>
              <TextInput
                style={[
                  styles.input,
                  styles.inputMultiline,
                  focado === 'medicamentos' && styles.inputFocado,
                ]}
                value={perfil.medicamentos}
                onChangeText={(t) => set('medicamentos', t)}
                placeholder="Ex: metformina 500mg, levotiroxina 50mcg"
                placeholderTextColor="#AAAAAA"
                multiline
                numberOfLines={3}
                textAlignVertical="top"
                onFocus={() => setFocado('medicamentos')}
                onBlur={() => setFocado(null)}
              />

              <Text style={styles.label}>Alergias</Text>
              <TextInput
                style={[
                  styles.input,
                  styles.inputMultiline,
                  focado === 'alergias' && styles.inputFocado,
                ]}
                value={perfil.alergias}
                onChangeText={(t) => set('alergias', t)}
                placeholder="Ex: penicilina, dipirona"
                placeholderTextColor="#AAAAAA"
                multiline
                numberOfLines={3}
                textAlignVertical="top"
                onFocus={() => setFocado('alergias')}
                onBlur={() => setFocado(null)}
              />
            </View>
          )}

          {/* ── ETAPA 3: Histórico familiar ── */}
          {step === 3 && (
            <View>
              <Text style={styles.titulo}>Histórico da família</Text>
              <Text style={styles.subtitulo}>
                Selecione condições que ocorrem na sua família (pais, irmãos, avós).
              </Text>

              <View style={styles.chips}>
                {CONDICOES_FAMILIAR.map((cond) => (
                  <SelectableChip
                    key={cond}
                    label={cond}
                    selected={perfil.historicoFamiliar.includes(cond)}
                    onPress={() =>
                      set('historicoFamiliar', toggleItem(perfil.historicoFamiliar, cond))
                    }
                  />
                ))}
              </View>
            </View>
          )}

          {/* ── ETAPA 4: Histórico obstétrico ── */}
          {step === 4 && (
            <View>
              <Text style={styles.titulo}>Gestações anteriores</Text>
              <Text style={styles.subtitulo}>
                Essas informações ajudam a identificar riscos com mais precisão.
              </Text>

              <Text style={styles.label}>É sua primeira gestação?</Text>
              <SimNao
                valor={perfil.primeiraGestacao}
                onChange={(v) => set('primeiraGestacao', v)}
              />

              {!perfil.primeiraGestacao && (
                <View style={styles.secaoExtra}>
                  <Text style={styles.label}>Quantos partos anteriores?</Text>
                  <View style={styles.stepper}>
                    <Pressable
                      style={styles.stepperBotao}
                      onPress={() =>
                        set('partosAnteriores', Math.max(0, perfil.partosAnteriores - 1))
                      }
                      accessibilityRole="button"
                      accessibilityLabel="Diminuir">
                      <Text style={styles.stepperSinal}>−</Text>
                    </Pressable>
                    <Text style={styles.stepperValor}>{perfil.partosAnteriores}</Text>
                    <Pressable
                      style={styles.stepperBotao}
                      onPress={() => set('partosAnteriores', perfil.partosAnteriores + 1)}
                      accessibilityRole="button"
                      accessibilityLabel="Aumentar">
                      <Text style={styles.stepperSinal}>+</Text>
                    </Pressable>
                  </View>

                  <Text style={styles.label}>Aborto anterior?</Text>
                  <SimNao valor={perfil.aborto} onChange={(v) => set('aborto', v)} />

                  <Text style={styles.label}>Parto prematuro anterior?</Text>
                  <SimNao
                    valor={perfil.partoPrematuro}
                    onChange={(v) => set('partoPrematuro', v)}
                  />

                  <Text style={styles.label}>Pré-eclâmpsia em gestação anterior?</Text>
                  <SimNao
                    valor={perfil.preEclampsiaAnterior}
                    onChange={(v) => set('preEclampsiaAnterior', v)}
                  />
                </View>
              )}
            </View>
          )}

          {erro !== '' && <Text style={styles.erro}>{erro}</Text>}
        </ScrollView>
      </KeyboardAvoidingView>

      <View style={styles.footer}>
        {step > 1 && (
          <Pressable style={styles.botaoVoltar} onPress={voltar} accessibilityRole="button">
            <Text style={styles.botaoVoltarTexto}>Voltar</Text>
          </Pressable>
        )}
        <Pressable
          style={[styles.botao, step === 1 && styles.botaoFull]}
          onPress={avancar}
          accessibilityRole="button">
          <Text style={styles.botaoTexto}>
            {step === TOTAL_STEPS ? 'Concluir' : 'Próximo'}
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  flex: {
    flex: 1,
  },
  scroll: {
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 32,
  },
  titulo: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.title,
  },
  subtitulo: {
    marginTop: 8,
    fontSize: 15,
    lineHeight: 22,
    color: COLORS.body,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.title,
    marginTop: 20,
    marginBottom: 10,
  },
  input: {
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: COLORS.title,
    backgroundColor: COLORS.background,
  },
  inputFocado: {
    borderColor: COLORS.primary,
  },
  inputMultiline: {
    height: 90,
  },
  toggle: {
    flexDirection: 'row',
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    marginTop: 24,
    overflow: 'hidden',
  },
  toggleOpcao: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    gap: 2,
  },
  toggleAtivo: {
    backgroundColor: COLORS.primary,
  },
  toggleSigla: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.body,
  },
  toggleDescricao: {
    fontSize: 11,
    color: COLORS.body,
  },
  toggleTextoAtivo: {
    color: COLORS.background,
  },
  semanaCard: {
    marginTop: 24,
    backgroundColor: COLORS.primaryLight,
    borderRadius: 16,
    paddingVertical: 28,
    alignItems: 'center',
  },
  semanaNumero: {
    fontSize: 56,
    fontWeight: '700',
    color: COLORS.primary,
    lineHeight: 64,
  },
  semanaTexto: {
    fontSize: 15,
    color: COLORS.primary,
    marginTop: 4,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
  },
  simNao: {
    flexDirection: 'row',
    gap: 12,
  },
  simNaoOpcao: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  simNaoAtivo: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  simNaoTexto: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.body,
  },
  simNaoTextoAtivo: {
    color: COLORS.background,
  },
  secaoExtra: {
    marginTop: 4,
  },
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 24,
  },
  stepperBotao: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperSinal: {
    fontSize: 24,
    color: COLORS.primary,
    fontWeight: '600',
    lineHeight: 28,
  },
  stepperValor: {
    fontSize: 26,
    fontWeight: '700',
    color: COLORS.title,
    minWidth: 32,
    textAlign: 'center',
  },
  footer: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 24,
    paddingBottom: 32,
    paddingTop: 12,
  },
  botao: {
    flex: 1,
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  botaoFull: {
    flex: 1,
  },
  botaoTexto: {
    color: COLORS.background,
    fontSize: 18,
    fontWeight: '600',
  },
  botaoVoltar: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  botaoVoltarTexto: {
    color: COLORS.body,
    fontSize: 18,
    fontWeight: '600',
  },
  erro: {
    marginTop: 16,
    color: COLORS.error,
    fontSize: 14,
  },
});
