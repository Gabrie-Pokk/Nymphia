import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useState } from 'react';

// expo-notifications não funciona em Expo Go no Android (SDK 53+)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let Notifications: any = null;
try {
  Notifications = require('expo-notifications');
} catch {
  // Expo Go: notificações desativadas
}
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

export const ALARMES_KEY = '@nymphia/alarmes';

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  primaryLight: '#FCE4EC',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
  error: '#B71C1C',
};

type TipoAlarme = 'medicamento' | 'vitamina' | 'consulta' | 'vacina';
type Repeticao = 'diaria' | 'semanal';

export type Alarme = {
  id: string;
  notificacaoId: string;
  nome: string;
  horario: string;
  repeticao: Repeticao;
  tipo: TipoAlarme;
};

const TIPOS: { valor: TipoAlarme; rotulo: string; emoji: string }[] = [
  { valor: 'medicamento', rotulo: 'Medicamento', emoji: '💊' },
  { valor: 'vitamina', rotulo: 'Vitamina', emoji: '🌿' },
  { valor: 'consulta', rotulo: 'Consulta', emoji: '🩺' },
  { valor: 'vacina', rotulo: 'Vacina', emoji: '💉' },
];

const ROTULO_REPETICAO: Record<Repeticao, string> = {
  diaria: 'Diária',
  semanal: 'Semanal',
};

const MENSAGEM_TIPO: Record<TipoAlarme, string> = {
  medicamento: 'Hora de tomar seu medicamento.',
  vitamina: 'Hora de tomar sua vitamina.',
  consulta: 'Você tem uma consulta agendada.',
  vacina: 'Lembrete de vacinação.',
};

function gerarId(): string {
  return `alarm-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function formatarHorario(texto: string): string {
  const nums = texto.replace(/\D/g, '').slice(0, 4);
  if (nums.length <= 2) return nums;
  return `${nums.slice(0, 2)}:${nums.slice(2)}`;
}

function horarioValido(horario: string): boolean {
  if (horario.length !== 5 || horario[2] !== ':') return false;
  const h = Number(horario.slice(0, 2));
  const m = Number(horario.slice(3, 5));
  return h >= 0 && h <= 23 && m >= 0 && m <= 59;
}

async function solicitarPermissao(): Promise<boolean> {
  if (!Notifications) return true; // Expo Go: pula permissão
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('alarmes-nymphia', {
      name: 'Alarmes Nymphia',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
    });
  }
  const { status } = await Notifications.requestPermissionsAsync({
    ios: { allowAlert: true, allowBadge: true, allowSound: true },
  });
  return status === 'granted';
}

async function agendarNotificacao(
  nome: string,
  horario: string,
  repeticao: Repeticao,
  tipo: TipoAlarme,
): Promise<string> {
  if (!Notifications) return `local-${Date.now()}`; // Expo Go: sem notificação real
  const [hora, minuto] = horario.split(':').map(Number);
  const tipoInfo = TIPOS.find((t) => t.valor === tipo);
  const titulo = tipoInfo ? `${tipoInfo.emoji} ${nome}` : nome;

  if (repeticao === 'diaria') {
    return Notifications.scheduleNotificationAsync({
      content: { title: titulo, body: MENSAGEM_TIPO[tipo], sound: true },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.DAILY,
        hour: hora,
        minute: minuto,
      },
    });
  } else {
    const diaSemana = (new Date().getDay() + 1) as 1 | 2 | 3 | 4 | 5 | 6 | 7;
    return Notifications.scheduleNotificationAsync({
      content: { title: titulo, body: MENSAGEM_TIPO[tipo], sound: true },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.WEEKLY,
        weekday: diaSemana,
        hour: hora,
        minute: minuto,
      },
    });
  }
}

export default function AlarmesScreen() {
  const [alarmes, setAlarmes] = useState<Alarme[]>([]);
  const [nome, setNome] = useState('');
  const [horario, setHorario] = useState('');
  const [repeticao, setRepeticao] = useState<Repeticao>('diaria');
  const [tipo, setTipo] = useState<TipoAlarme>('medicamento');
  const [focado, setFocado] = useState<string | null>(null);
  const [erro, setErro] = useState('');
  const [adicionando, setAdicionando] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(ALARMES_KEY).then((json) => {
      if (json) setAlarmes(JSON.parse(json) as Alarme[]);
    });
  }, []);

  const validar = (): boolean => {
    if (nome.trim().length < 2) {
      setErro('Digite o nome do remédio ou evento (mínimo 2 caracteres).');
      return false;
    }
    if (!horarioValido(horario)) {
      setErro('Digite um horário válido no formato HH:MM.');
      return false;
    }
    setErro('');
    return true;
  };

  const adicionar = async () => {
    if (!validar()) return;
    setAdicionando(true);
    try {
      const permitido = await solicitarPermissao();
      if (!permitido) {
        Alert.alert(
          'Permissão necessária',
          'Autorize notificações nas configurações para receber alarmes.',
        );
        return;
      }

      const notificacaoId = await agendarNotificacao(nome.trim(), horario, repeticao, tipo);

      const novoAlarme: Alarme = {
        id: gerarId(),
        notificacaoId,
        nome: nome.trim(),
        horario,
        repeticao,
        tipo,
      };

      const novos = [...alarmes, novoAlarme].sort((a, b) =>
        a.horario.localeCompare(b.horario),
      );
      setAlarmes(novos);
      await AsyncStorage.setItem(ALARMES_KEY, JSON.stringify(novos));

      setNome('');
      setHorario('');
      setRepeticao('diaria');
      setTipo('medicamento');
      setErro('');
    } finally {
      setAdicionando(false);
    }
  };

  const deletar = (alarme: Alarme) => {
    Alert.alert('Remover alarme', `Remover "${alarme.nome}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Remover',
        style: 'destructive',
        onPress: async () => {
          if (Notifications) await Notifications.cancelScheduledNotificationAsync(alarme.notificacaoId);
          const novos = alarmes.filter((a) => a.id !== alarme.id);
          setAlarmes(novos);
          await AsyncStorage.setItem(ALARMES_KEY, JSON.stringify(novos));
        },
      },
    ]);
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
          <Text style={styles.titulo}>Alarmes</Text>
          <Text style={styles.subtitulo}>
            Gerencie seus lembretes de medicamentos e consultas.
          </Text>

          {/* ── Formulário ── */}
          <View style={styles.form}>
            <Text style={styles.label}>Nome do remédio ou evento</Text>
            <TextInput
              style={[styles.input, focado === 'nome' && styles.inputFocado]}
              value={nome}
              onChangeText={setNome}
              placeholder="Ex: Ácido fólico, Consulta pré-natal"
              placeholderTextColor="#AAAAAA"
              autoCapitalize="words"
              onFocus={() => setFocado('nome')}
              onBlur={() => setFocado(null)}
            />

            <Text style={styles.label}>Horário</Text>
            <TextInput
              style={[styles.input, focado === 'horario' && styles.inputFocado]}
              value={horario}
              onChangeText={(t) => setHorario(formatarHorario(t))}
              placeholder="HH:MM"
              placeholderTextColor="#AAAAAA"
              keyboardType="numeric"
              maxLength={5}
              onFocus={() => setFocado('horario')}
              onBlur={() => setFocado(null)}
            />

            <Text style={styles.label}>Repetição</Text>
            <View style={styles.toggle}>
              {(['diaria', 'semanal'] as Repeticao[]).map((r) => (
                <Pressable
                  key={r}
                  style={[styles.toggleOpcao, repeticao === r && styles.toggleAtivo]}
                  onPress={() => setRepeticao(r)}>
                  <Text
                    style={[styles.toggleTexto, repeticao === r && styles.toggleTextoAtivo]}>
                    {ROTULO_REPETICAO[r]}
                  </Text>
                </Pressable>
              ))}
            </View>

            <Text style={styles.label}>Tipo</Text>
            <View style={styles.chips}>
              {TIPOS.map(({ valor, rotulo, emoji }) => (
                <SelectableChip
                  key={valor}
                  label={`${emoji} ${rotulo}`}
                  selected={tipo === valor}
                  onPress={() => setTipo(valor)}
                />
              ))}
            </View>

            {erro !== '' && <Text style={styles.erro}>{erro}</Text>}

            <Pressable
              style={[styles.botaoAdicionar, adicionando && styles.botaoDesabilitado]}
              onPress={adicionar}
              disabled={adicionando}
              accessibilityRole="button">
              <Text style={styles.botaoAdicionarTexto}>
                {adicionando ? 'Agendando...' : '+ Adicionar alarme'}
              </Text>
            </Pressable>
          </View>

          {/* ── Lista ── */}
          <View style={styles.separadorRow}>
            <View style={styles.separadorLinha} />
            <Text style={styles.separadorTexto}>Meus alarmes</Text>
            <View style={styles.separadorLinha} />
          </View>

          {alarmes.length === 0 ? (
            <View style={styles.vazio}>
              <Text style={styles.vazioEmoji}>🔕</Text>
              <Text style={styles.vazioTexto}>Nenhum alarme agendado ainda.</Text>
            </View>
          ) : (
            <View style={styles.lista}>
              {alarmes.map((alarme) => {
                const tipoInfo = TIPOS.find((t) => t.valor === alarme.tipo);
                return (
                  <View key={alarme.id} style={styles.alarmeItem}>
                    <View style={styles.alarmeIcone}>
                      <Text style={styles.alarmeEmoji}>{tipoInfo?.emoji ?? '🔔'}</Text>
                    </View>
                    <View style={styles.alarmeInfo}>
                      <Text style={styles.alarmeNome}>{alarme.nome}</Text>
                      <Text style={styles.alarmeDetalhe}>
                        {alarme.horario} · {ROTULO_REPETICAO[alarme.repeticao]}
                      </Text>
                    </View>
                    <Pressable
                      style={styles.deletarBotao}
                      onPress={() => deletar(alarme)}
                      accessibilityRole="button"
                      accessibilityLabel={`Remover alarme ${alarme.nome}`}>
                      <Text style={styles.deletarTexto}>×</Text>
                    </Pressable>
                  </View>
                );
              })}
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  flex: { flex: 1 },
  scroll: {
    paddingHorizontal: 24,
    paddingTop: 32,
    paddingBottom: 48,
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

  // Formulário
  form: {
    marginTop: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.title,
    marginTop: 16,
    marginBottom: 8,
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
  toggle: {
    flexDirection: 'row',
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    overflow: 'hidden',
  },
  toggleOpcao: {
    flex: 1,
    paddingVertical: 13,
    alignItems: 'center',
  },
  toggleAtivo: {
    backgroundColor: COLORS.primary,
  },
  toggleTexto: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.body,
  },
  toggleTextoAtivo: {
    color: COLORS.background,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  erro: {
    marginTop: 12,
    color: COLORS.error,
    fontSize: 14,
  },
  botaoAdicionar: {
    marginTop: 20,
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  botaoDesabilitado: {
    opacity: 0.6,
  },
  botaoAdicionarTexto: {
    color: COLORS.background,
    fontSize: 17,
    fontWeight: '600',
  },

  // Separador
  separadorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 32,
    marginBottom: 16,
  },
  separadorLinha: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.border,
  },
  separadorTexto: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.body,
  },

  // Lista
  lista: {
    gap: 10,
  },
  vazio: {
    alignItems: 'center',
    paddingVertical: 32,
    gap: 8,
  },
  vazioEmoji: {
    fontSize: 32,
  },
  vazioTexto: {
    fontSize: 15,
    color: COLORS.body,
  },

  // Item
  alarmeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 14,
    padding: 14,
    gap: 12,
    backgroundColor: COLORS.background,
  },
  alarmeIcone: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  alarmeEmoji: {
    fontSize: 22,
  },
  alarmeInfo: {
    flex: 1,
  },
  alarmeNome: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.title,
  },
  alarmeDetalhe: {
    fontSize: 13,
    color: COLORS.body,
    marginTop: 2,
  },
  deletarBotao: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FFEBEE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  deletarTexto: {
    fontSize: 20,
    color: COLORS.error,
    fontWeight: '600',
    lineHeight: 24,
  },
});
