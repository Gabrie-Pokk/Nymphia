import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { useState } from 'react';
import {
  Alert,
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

import SelectableChip from '@/components/selectable-chip';

export const CHECKINS_KEY = '@nymphia/checkins';

// ── Endereço do backend de IA ──
// Em desenvolvimento local, aponta pro seu computador na mesma rede Wi-Fi
// (não use "localhost" -- o celular não entende isso, precisa do IP).
// Troque pelo endereço real quando o backend estiver publicado.
const BACKEND_URL = 'http://192.168.0.114:8000';

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  primaryLight: '#FCE4EC',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
  alerta: '#C0392B',
};

const HUMORES = [
  { valor: 1, emoji: '😣', rotulo: 'Muito mal' },
  { valor: 2, emoji: '😔', rotulo: 'Mal' },
  { valor: 3, emoji: '😐', rotulo: 'Regular' },
  { valor: 4, emoji: '🙂', rotulo: 'Bem' },
  { valor: 5, emoji: '😊', rotulo: 'Muito bem' },
] as const;

const SINTOMAS: string[] = [
  'Dor de cabeça',
  'Inchaço',
  'Visão turva',
  'Sangramento',
  'Dor abdominal',
  'Febre',
  'Enjoo',
  'Nenhum',
];

// Sintomas do checkbox que já são, por si só, motivo de alerta -- não
// depende do texto livre pra saber que isso é sério.
const SINTOMAS_DE_ALERTA = new Set(['Visão turva', 'Sangramento', 'Febre']);

type AnaliseCheckin = {
  categorias: { categoria: string; fonte: string }[];
  alerta_sintoma_fisico: string[];
  recomendacao: string;
};

type Checkin = {
  data: string;
  humor: number;
  descricao: string;
  sintomas: string[];
  movimentosBebe: number;
  analiseIA?: AnaliseCheckin | null;
};

function formatarDataPt(data: Date): string {
  const dias = [
    'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
    'Quinta-feira', 'Sexta-feira', 'Sábado',
  ];
  const meses = [
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
  ];
  return `${dias[data.getDay()]}, ${data.getDate()} de ${meses[data.getMonth()]}`;
}

function toggleSintoma(lista: string[], item: string): string[] {
  if (item === 'Nenhum') {
    return lista.includes('Nenhum') ? [] : ['Nenhum'];
  }
  const semNenhum = lista.filter((s) => s !== 'Nenhum');
  return semNenhum.includes(item)
    ? semNenhum.filter((s) => s !== item)
    : [...semNenhum, item];
}

// Chama o backend de IA pra analisar o texto livre do check-in.
// NUNCA lança erro -- se o backend estiver fora do ar, sem internet,
// ou qualquer outro problema, devolve null e o check-in continua
// salvando normalmente, só sem a análise extra.
async function analisarComIA(texto: string): Promise<AnaliseCheckin | null> {
  if (!texto.trim()) return null;
  try {
    const controle = new AbortController();
    const tempoLimite = setTimeout(() => controle.abort(), 5000);
    const resposta = await fetch(`${BACKEND_URL}/checkin/analisar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto }),
      signal: controle.signal,
    });
    clearTimeout(tempoLimite);
    if (!resposta.ok) return null;
    return (await resposta.json()) as AnaliseCheckin;
  } catch {
    // Sem internet, backend fora do ar, timeout -- qualquer motivo.
    // O check-in não pode depender disso pra funcionar.
    return null;
  }
}

export default function CheckinScreen() {
  const hoje = new Date();
  const [humor, setHumor] = useState(3);
  const [descricao, setDescricao] = useState('');
  const [sintomas, setSintomas] = useState<string[]>([]);
  const [movimentos, setMovimentos] = useState(0);
  const [focado, setFocado] = useState(false);
  const [salvando, setSalvando] = useState(false);

  const salvar = async () => {
    setSalvando(true);
    try {
      const sintomaDeAlertaMarcado = sintomas.some((s) => SINTOMAS_DE_ALERTA.has(s));
      const analiseIA = await analisarComIA(descricao);
      const alertaDoTexto = (analiseIA?.alerta_sintoma_fisico?.length ?? 0) > 0;

      const json = await AsyncStorage.getItem(CHECKINS_KEY);
      const historico: Checkin[] = json ? (JSON.parse(json) as Checkin[]) : [];

      historico.push({
        data: hoje.toISOString(),
        humor,
        descricao: descricao.trim(),
        sintomas,
        movimentosBebe: movimentos,
        analiseIA,
      });

      await AsyncStorage.setItem(CHECKINS_KEY, JSON.stringify(historico));

      if (sintomaDeAlertaMarcado || alertaDoTexto) {
        Alert.alert(
          'Atenção 🚨',
          'O que você registrou hoje merece contato com seu médico o quanto antes. Seu check-in foi salvo, mas não espere a próxima consulta -- procure orientação médica agora.',
          [{ text: 'Entendi', onPress: () => router.replace('/(main)') }],
        );
      } else {
        Alert.alert('Check-in salvo! 🌸', 'Seu registro de hoje foi guardado com sucesso.', [
          { text: 'OK', onPress: () => router.replace('/(main)') },
        ]);
      }
    } finally {
      setSalvando(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled">

          {/* Cabeçalho */}
          <Text style={styles.titulo}>Check-in de hoje</Text>
          <Text style={styles.subtitulo}>{formatarDataPt(hoje)}</Text>

          {/* ── Humor ── */}
          <Text style={styles.secaoLabel}>Como você está se sentindo?</Text>
          <View style={styles.humores}>
            {HUMORES.map(({ valor, emoji, rotulo }) => (
              <Pressable
                key={valor}
                style={[styles.humorItem, humor === valor && styles.humorItemAtivo]}
                onPress={() => setHumor(valor)}
                accessibilityRole="radio"
                accessibilityLabel={rotulo}
                accessibilityState={{ selected: humor === valor }}>
                <Text style={styles.humorEmoji}>{emoji}</Text>
                {humor === valor && (
                  <Text style={styles.humorRotulo}>{rotulo}</Text>
                )}
              </Pressable>
            ))}
          </View>

          {/* ── Descrição livre ── */}
          <Text style={styles.secaoLabel}>Descreva como você está</Text>
          <TextInput
            style={[styles.inputMultiline, focado && styles.inputFocado]}
            value={descricao}
            onChangeText={setDescricao}
            placeholder="Conte como se sente hoje, o que está diferente..."
            placeholderTextColor="#AAAAAA"
            multiline
            numberOfLines={4}
            textAlignVertical="top"
            onFocus={() => setFocado(true)}
            onBlur={() => setFocado(false)}
          />

          {/* ── Sintomas ── */}
          <Text style={styles.secaoLabel}>Sintomas de hoje</Text>
          <View style={styles.chips}>
            {SINTOMAS.map((s) => (
              <SelectableChip
                key={s}
                label={s}
                selected={sintomas.includes(s)}
                onPress={() => setSintomas(toggleSintoma(sintomas, s))}
              />
            ))}
          </View>

          {/* ── Movimentos do bebê ── */}
          <Text style={styles.secaoLabel}>Movimentos do bebê</Text>
          <Text style={styles.secaoHint}>quantas vezes o bebê se mexeu na última hora</Text>
          <View style={styles.stepper}>
            <Pressable
              style={styles.stepperBotao}
              onPress={() => setMovimentos(Math.max(0, movimentos - 1))}
              accessibilityRole="button"
              accessibilityLabel="Diminuir movimentos">
              <Text style={styles.stepperSinal}>−</Text>
            </Pressable>
            <Text style={styles.stepperValor}>{movimentos}</Text>
            <Pressable
              style={styles.stepperBotao}
              onPress={() => setMovimentos(movimentos + 1)}
              accessibilityRole="button"
              accessibilityLabel="Aumentar movimentos">
              <Text style={styles.stepperSinal}>+</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* ── Botão salvar fixo ── */}
      <View style={styles.rodape}>
        <Pressable
          style={[styles.botao, salvando && styles.botaoDesabilitado]}
          onPress={salvar}
          disabled={salvando}
          accessibilityRole="button">
          <Text style={styles.botaoTexto}>{salvando ? 'Analisando...' : 'Salvar check-in'}</Text>
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
    paddingTop: 32,
    paddingBottom: 24,
  },

  // Cabeçalho
  titulo: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.title,
  },
  subtitulo: {
    marginTop: 4,
    fontSize: 15,
    color: COLORS.body,
  },

  // Seções
  secaoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.title,
    marginTop: 28,
    marginBottom: 12,
  },
  secaoHint: {
    fontSize: 12,
    color: COLORS.body,
    marginTop: -8,
    marginBottom: 14,
  },

  // Humor
  humores: {
    flexDirection: 'row',
    gap: 6,
  },
  humorItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 2,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    gap: 4,
  },
  humorItemAtivo: {
    backgroundColor: COLORS.primaryLight,
    borderColor: COLORS.primary,
  },
  humorEmoji: {
    fontSize: 26,
  },
  humorRotulo: {
    fontSize: 10,
    fontWeight: '600',
    color: COLORS.primary,
    textAlign: 'center',
  },

  // Descrição
  inputMultiline: {
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: COLORS.title,
    backgroundColor: COLORS.background,
    height: 110,
  },
  inputFocado: {
    borderColor: COLORS.primary,
  },

  // Chips
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },

  // Stepper
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 28,
  },
  stepperBotao: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperSinal: {
    fontSize: 26,
    color: COLORS.primary,
    fontWeight: '600',
    lineHeight: 30,
  },
  stepperValor: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.title,
    minWidth: 40,
    textAlign: 'center',
  },

  // Rodapé
  rodape: {
    paddingHorizontal: 24,
    paddingBottom: 24,
    paddingTop: 8,
  },
  botao: {
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  botaoDesabilitado: {
    opacity: 0.6,
  },
  botaoTexto: {
    color: COLORS.background,
    fontSize: 18,
    fontWeight: '600',
  },
});
