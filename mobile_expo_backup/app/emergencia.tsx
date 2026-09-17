import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const COLORS = {
  vermelho: '#C0392B',
  vermelhoEscuro: '#922B21',
  vermelhoClaro: '#FDEDEB',
  branco: '#FFFFFF',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
};

const MATERNIDADE_KEY = '@nymphia/maternidade';

// Mesmo endereço configurado no checkin.tsx -- trocar pelo IP real do
// backend em produção.
const BACKEND_URL = 'http://192.168.0.114:8000';

type Maternidade = {
  nome: string;
  endereco: string;
  telefone: string;
};

function ligarPara(numero: string) {
  Linking.openURL(`tel:${numero}`).catch(() => {
    // Se o dispositivo não conseguir abrir o discador, não travamos a tela --
    // o número já está visível pra gestante discar manualmente.
  });
}

function abrirRota(endereco: string) {
  const url = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(endereco)}`;
  Linking.openURL(url).catch(() => {});
}

// Notifica o médico vinculado e registra o evento -- roda em paralelo à
// tela de emergência, nunca bloqueia nem atrasa a ação principal (ligar
// pro SAMU). Se o backend estiver fora do ar, a tela continua funcionando
// normalmente -- só essas duas ações silenciosamente não completam.
async function acionarBackendEmergencia(): Promise<void> {
  try {
    const controle = new AbortController();
    const tempoLimite = setTimeout(() => controle.abort(), 5000);
    await fetch(`${BACKEND_URL}/emergencia/notificar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ momento: new Date().toISOString() }),
      signal: controle.signal,
    });
    clearTimeout(tempoLimite);
  } catch {
    // Silencioso de propósito -- ver comentário acima.
  }
}

export default function EmergenciaScreen() {
  const [maternidade, setMaternidade] = useState<Maternidade | null>(null);
  const [carregandoMaternidade, setCarregandoMaternidade] = useState(true);
  const [avisoEnviado, setAvisoEnviado] = useState(false);

  useEffect(() => {
    // As três ações da emergência disparam ao mesmo tempo, assim que a tela abre --
    // nenhuma espera a outra terminar.
    (async () => {
      try {
        const json = await AsyncStorage.getItem(MATERNIDADE_KEY);
        setMaternidade(json ? (JSON.parse(json) as Maternidade) : null);
      } finally {
        setCarregandoMaternidade(false);
      }
    })();

    acionarBackendEmergencia().finally(() => setAvisoEnviado(true));
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.titulo}>Emergência</Text>

        <Pressable
          style={styles.botaoSamu}
          onPress={() => ligarPara('192')}
          accessibilityRole="button"
          accessibilityLabel="Ligar para o SAMU, 192">
          <Text style={styles.botaoSamuIcone}>📞</Text>
          <Text style={styles.botaoSamuTexto}>LIGAR PARA O SAMU</Text>
          <Text style={styles.botaoSamuNumero}>192</Text>
        </Pressable>

        <Text style={styles.aviso}>
          Se você está com sangramento, dor forte, visão embaçada ou não sente o bebê mexer,
          ligue agora. Não espere.
        </Text>

        {!carregandoMaternidade && maternidade && (
          <View style={styles.cardMaternidade}>
            <Text style={styles.cardLabel}>Sua maternidade de referência</Text>
            <Text style={styles.cardNome}>{maternidade.nome}</Text>
            <Text style={styles.cardEndereco}>{maternidade.endereco}</Text>
            <View style={styles.linhaBotoes}>
              <Pressable
                style={styles.botaoSecundario}
                onPress={() => ligarPara(maternidade.telefone)}
                accessibilityRole="button">
                <Text style={styles.botaoSecundarioTexto}>Ligar</Text>
              </Pressable>
              <Pressable
                style={styles.botaoSecundario}
                onPress={() => abrirRota(maternidade.endereco)}
                accessibilityRole="button">
                <Text style={styles.botaoSecundarioTexto}>Ver rota</Text>
              </Pressable>
            </View>
          </View>
        )}

        {!carregandoMaternidade && !maternidade && (
          <View style={styles.cardMaternidade}>
            <Text style={styles.cardLabel}>
              Você ainda não cadastrou uma maternidade de referência. Configure isso no seu
              perfil assim que possível.
            </Text>
          </View>
        )}

        <View style={styles.statusMedico}>
          <Text style={styles.statusMedicoTexto}>
            {avisoEnviado
              ? 'Seu médico foi avisado deste evento.'
              : 'Avisando seu médico...'}
          </Text>
        </View>

        <Pressable
          style={styles.botaoVoltar}
          onPress={() => router.back()}
          accessibilityRole="button">
          <Text style={styles.botaoVoltarTexto}>Já estou segura, voltar ao app</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.branco,
  },
  scroll: {
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 40,
    alignItems: 'center',
  },
  titulo: {
    fontSize: 26,
    fontWeight: '700',
    color: COLORS.vermelho,
    marginBottom: 20,
  },
  botaoSamu: {
    width: '100%',
    backgroundColor: COLORS.vermelho,
    borderRadius: 16,
    paddingVertical: 28,
    alignItems: 'center',
    marginBottom: 16,
  },
  botaoSamuIcone: {
    fontSize: 34,
    marginBottom: 6,
  },
  botaoSamuTexto: {
    color: COLORS.branco,
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  botaoSamuNumero: {
    color: COLORS.branco,
    fontSize: 34,
    fontWeight: '800',
    marginTop: 4,
  },
  aviso: {
    fontSize: 14,
    color: COLORS.body,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  cardMaternidade: {
    width: '100%',
    backgroundColor: COLORS.vermelhoClaro,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  cardLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.vermelhoEscuro,
    marginBottom: 4,
  },
  cardNome: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.title,
  },
  cardEndereco: {
    fontSize: 13,
    color: COLORS.body,
    marginTop: 2,
    marginBottom: 12,
  },
  linhaBotoes: {
    flexDirection: 'row',
    gap: 10,
  },
  botaoSecundario: {
    flex: 1,
    borderWidth: 1.5,
    borderColor: COLORS.vermelho,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  botaoSecundarioTexto: {
    color: COLORS.vermelho,
    fontWeight: '600',
    fontSize: 14,
  },
  statusMedico: {
    marginBottom: 28,
  },
  statusMedicoTexto: {
    fontSize: 13,
    color: COLORS.body,
    fontStyle: 'italic',
  },
  botaoVoltar: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  botaoVoltarTexto: {
    color: COLORS.body,
    fontSize: 14,
    textDecorationLine: 'underline',
  },
});
