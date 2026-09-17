import AsyncStorage from '@react-native-async-storage/async-storage';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const PERFIL_CLINICO_KEY = '@nymphia/perfil_clinico';
const ALARMES_KEY = '@nymphia/alarmes';

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  primaryLight: '#FCE4EC',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
  emergency: '#C62828',
};

const EMOJI_TIPO: Record<string, string> = {
  medicamento: '💊',
  vitamina: '🌿',
  consulta: '🩺',
  vacina: '💉',
};

type DadosGestacionais = {
  tipoDada: 'dum' | 'dpp';
  data: string;
  semanaGestacional: number | null;
};

type AlarmeSimples = {
  id: string;
  nome: string;
  horario: string;
  tipo: string;
};

function calcularSemanaAtual({ data, tipoDada, semanaGestacional }: DadosGestacionais): number | null {
  if (data.length >= 10) {
    const [dS, mS, aS] = data.split('/');
    const d = Number(dS);
    const m = Number(mS);
    const a = Number(aS);
    if (d && m && a && a >= 2000) {
      const ref = new Date(a, m - 1, d);
      const hoje = new Date();
      if (tipoDada === 'dum') {
        const semanas = Math.floor(
          (hoje.getTime() - ref.getTime()) / (7 * 24 * 60 * 60 * 1000),
        );
        if (semanas >= 1 && semanas <= 42) return semanas;
      } else {
        const restantes = Math.ceil(
          (ref.getTime() - hoje.getTime()) / (7 * 24 * 60 * 60 * 1000),
        );
        const semana = 40 - restantes;
        if (semana >= 1 && semana <= 42) return semana;
      }
    }
  }
  return semanaGestacional;
}

function rotuloTrimestre(semana: number): string {
  if (semana <= 12) return 'Primeiro trimestre';
  if (semana <= 26) return 'Segundo trimestre';
  return 'Terceiro trimestre';
}

function proximaHoraMs(horario: string): number {
  const [h, m] = horario.split(':').map(Number);
  const agora = new Date();
  const proxima = new Date();
  proxima.setHours(h, m, 0, 0);
  if (proxima.getTime() <= agora.getTime()) {
    proxima.setDate(proxima.getDate() + 1);
  }
  return proxima.getTime();
}

export default function HomeScreen() {
  const [semana, setSemana] = useState<number | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [proximosAlarmes, setProximosAlarmes] = useState<AlarmeSimples[]>([]);

  useFocusEffect(
    useCallback(() => {
      Promise.all([
        AsyncStorage.getItem(PERFIL_CLINICO_KEY),
        AsyncStorage.getItem(ALARMES_KEY),
      ]).then(([perfilJson, alarmesJson]) => {
        if (perfilJson) {
          const dados = JSON.parse(perfilJson) as DadosGestacionais;
          setSemana(calcularSemanaAtual(dados));
        }
        if (alarmesJson) {
          const todos = JSON.parse(alarmesJson) as AlarmeSimples[];
          const ordenados = [...todos].sort(
            (a, b) => proximaHoraMs(a.horario) - proximaHoraMs(b.horario),
          );
          setProximosAlarmes(ordenados.slice(0, 2));
        } else {
          setProximosAlarmes([]);
        }
        setCarregando(false);
      });
    }, []),
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}>

        {/* ── Hero: semana gestacional ── */}
        <View style={styles.hero}>
          {carregando ? (
            <ActivityIndicator color="#FFFFFF" size="large" />
          ) : semana !== null ? (
            <>
              <Text style={styles.heroLabel}>SEMANA</Text>
              <Text style={styles.heroNumero}>{semana}</Text>
              <Text style={styles.heroTrimestre}>{rotuloTrimestre(semana)}</Text>
            </>
          ) : (
            <>
              <Text style={styles.heroLabel}>SEMANA</Text>
              <Text style={styles.heroNumero}>—</Text>
              <Pressable onPress={() => router.push('/onboarding-clinico')}>
                <Text style={styles.heroAcao}>Completar perfil clínico →</Text>
              </Pressable>
            </>
          )}
        </View>

        {/* ── Cards ── */}
        <View style={styles.cards}>
          {/* Check-in */}
          <Pressable
            style={styles.card}
            onPress={() => router.push('/checkin')}
            accessibilityRole="button">
            <View style={[styles.icone, { backgroundColor: COLORS.primaryLight }]}>
              <Text style={styles.iconeEmoji}>💬</Text>
            </View>
            <View style={styles.cardTexto}>
              <Text style={styles.cardTitulo}>Como você está hoje?</Text>
              <Text style={styles.cardSubtitulo}>Registre seus sintomas e humor</Text>
            </View>
            <Text style={styles.seta}>›</Text>
          </Pressable>

          {/* Agenda */}
          <Pressable
            style={styles.card}
            onPress={() => router.push('/agenda')}
            accessibilityRole="button">
            <View style={[styles.icone, { backgroundColor: '#E3F2FD' }]}>
              <Text style={styles.iconeEmoji}>📅</Text>
            </View>
            <View style={styles.cardTexto}>
              <Text style={styles.cardTitulo}>Agenda</Text>
              <Text style={styles.cardSubtitulo}>Consultas, vacinas e exames</Text>
            </View>
            <Text style={styles.seta}>›</Text>
          </Pressable>

          {/* Alarmes */}
          <Pressable
            style={styles.card}
            onPress={() => router.push('/alarmes')}
            accessibilityRole="button">
            <View style={[styles.icone, { backgroundColor: '#EDE7F6' }]}>
              <Text style={styles.iconeEmoji}>🔔</Text>
            </View>
            <View style={styles.cardTexto}>
              <Text style={styles.cardTitulo}>Próximos alarmes</Text>
              {proximosAlarmes.length === 0 ? (
                <Text style={styles.cardSubtitulo}>Nenhum alarme agendado</Text>
              ) : (
                proximosAlarmes.map((a) => (
                  <Text key={a.id} style={styles.cardSubtitulo} numberOfLines={1}>
                    {EMOJI_TIPO[a.tipo] ?? '🔔'} {a.horario} · {a.nome}
                  </Text>
                ))
              )}
            </View>
            <Text style={styles.seta}>›</Text>
          </Pressable>
        </View>
      </ScrollView>

      {/* ── Botão de emergência fixo ── */}
      <View style={styles.rodape}>
        <Pressable
          style={styles.botaoEmergencia}
          accessibilityRole="button"
          accessibilityLabel="Botão de emergência — ligue para o seu médico">
          <Text style={styles.botaoEmergenciaTexto}>🚨  Emergência</Text>
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
  scroll: {
    flexGrow: 1,
  },

  // Hero
  hero: {
    backgroundColor: COLORS.primary,
    paddingTop: 40,
    paddingBottom: 56,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  heroLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.7)',
    letterSpacing: 2,
  },
  heroNumero: {
    fontSize: 100,
    fontWeight: '700',
    color: '#FFFFFF',
    lineHeight: 108,
  },
  heroTrimestre: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  heroAcao: {
    marginTop: 12,
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    fontWeight: '600',
    textDecorationLine: 'underline',
  },

  // Cards
  cards: {
    padding: 24,
    gap: 12,
    flex: 1,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 16,
    padding: 16,
    gap: 14,
    backgroundColor: COLORS.background,
  },
  icone: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconeEmoji: {
    fontSize: 22,
  },
  cardTexto: {
    flex: 1,
    gap: 2,
  },
  cardTitulo: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.title,
  },
  cardSubtitulo: {
    fontSize: 13,
    color: COLORS.body,
  },
  seta: {
    fontSize: 26,
    color: COLORS.border,
    fontWeight: '300',
  },

  // Rodapé
  rodape: {
    paddingHorizontal: 24,
    paddingBottom: 24,
    paddingTop: 8,
  },
  botaoEmergencia: {
    backgroundColor: COLORS.emergency,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  botaoEmergenciaTexto: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});
