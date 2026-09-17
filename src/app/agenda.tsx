import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import {
  Alert,
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { fetchAutenticado, useAuth } from '@/components/auth-context';

const BACKEND_URL = 'http://192.168.1.100:8000';

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  primaryLight: '#FCE4EC',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
};

const TIPOS = [
  { valor: 'consulta', rotulo: 'Consulta', icone: '🩺' },
  { valor: 'medicacao', rotulo: 'Medicação', icone: '💊' },
  { valor: 'vacina', rotulo: 'Vacina', icone: '💉' },
  { valor: 'exame', rotulo: 'Exame', icone: '🧪' },
  { valor: 'marco', rotulo: 'Marco', icone: '📌' },
] as const;

type TipoEvento = (typeof TIPOS)[number]['valor'];

type Evento = {
  id: number;
  tipo: string;
  titulo: string;
  data_hora: string;
  notas: string;
  concluido: boolean;
};

function iconePara(tipo: string): string {
  return TIPOS.find((t) => t.valor === tipo)?.icone ?? '📅';
}

function formatarDataHora(iso: string): { data: string; hora: string } {
  const d = new Date(iso);
  const dia = String(d.getDate()).padStart(2, '0');
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const hora = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return { data: `${dia}/${mes}/${d.getFullYear()}`, hora: `${hora}:${min}` };
}

export default function AgendaScreen() {
  const { token } = useAuth();
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [modalAberto, setModalAberto] = useState(false);

  const [tipoNovo, setTipoNovo] = useState<TipoEvento>('consulta');
  const [tituloNovo, setTituloNovo] = useState('');
  const [dataNova, setDataNova] = useState('');
  const [horaNova, setHoraNova] = useState('');
  const [notasNovas, setNotasNovas] = useState('');
  const [salvandoNovo, setSalvandoNovo] = useState(false);

  const carregarEventos = useCallback(async () => {
    if (!token) return;
    setCarregando(true);
    try {
      const resposta = await fetchAutenticado(`${BACKEND_URL}/agenda/eventos`, token);
      if (resposta.ok) {
        setEventos(await resposta.json());
      }
    } catch {
      // Sem conexão -- mantém a lista anterior na tela, não trava nem limpa.
    } finally {
      setCarregando(false);
    }
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      carregarEventos();
    }, [carregarEventos]),
  );

  const concluir = async (evento: Evento) => {
    if (!token) return;
    // Atualização otimista -- marca na tela antes da resposta do servidor.
    setEventos((atual) => atual.map((e) => (e.id === evento.id ? { ...e, concluido: true } : e)));
    try {
      const resposta = await fetchAutenticado(
        `${BACKEND_URL}/agenda/eventos/${evento.id}/concluir`,
        token,
        { method: 'PATCH' },
      );
      if (!resposta.ok) throw new Error();
    } catch {
      setEventos((atual) => atual.map((e) => (e.id === evento.id ? { ...e, concluido: false } : e)));
      Alert.alert('Não foi possível salvar', 'Tente novamente quando tiver conexão.');
    }
  };

  const abrirNovoEvento = () => {
    setTipoNovo('consulta');
    setTituloNovo('');
    setDataNova('');
    setHoraNova('');
    setNotasNovas('');
    setModalAberto(true);
  };

  const salvarNovoEvento = async () => {
    if (!token) return;
    if (tituloNovo.trim().length === 0) {
      Alert.alert('Preencha o título', 'Dê um nome pro evento, tipo "Consulta com Dra. Ana".');
      return;
    }
    const [dia, mes, ano] = dataNova.split('/');
    const [hora, minuto] = horaNova.split(':');
    if (!dia || !mes || !ano || !hora || !minuto) {
      Alert.alert('Data ou hora inválida', 'Use o formato dd/mm/aaaa para a data e hh:mm para a hora.');
      return;
    }
    const dataIso = new Date(
      Number(ano), Number(mes) - 1, Number(dia), Number(hora), Number(minuto),
    ).toISOString();

    setSalvandoNovo(true);
    try {
      const resposta = await fetchAutenticado(`${BACKEND_URL}/agenda/eventos`, token, {
        method: 'POST',
        body: JSON.stringify({
          tipo: tipoNovo, titulo: tituloNovo.trim(), data_hora: dataIso, notas: notasNovas,
        }),
      });
      if (!resposta.ok) throw new Error();
      setModalAberto(false);
      carregarEventos();
    } catch {
      Alert.alert('Não foi possível salvar', 'Confira sua conexão e tente novamente.');
    } finally {
      setSalvandoNovo(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.cabecalho}>
        <Text style={styles.titulo}>Agenda</Text>
        <Pressable style={styles.botaoAdicionar} onPress={abrirNovoEvento} accessibilityRole="button">
          <Text style={styles.botaoAdicionarTexto}>+ Novo</Text>
        </Pressable>
      </View>

      {!carregando && eventos.length === 0 && (
        <View style={styles.vazio}>
          <Text style={styles.vazioTexto}>Nenhum evento por aqui ainda.</Text>
          <Text style={styles.vazioSubtexto}>Toque em "+ Novo" para adicionar sua próxima consulta, vacina ou exame.</Text>
        </View>
      )}

      <FlatList
        data={eventos}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.lista}
        onRefresh={carregarEventos}
        refreshing={carregando}
        renderItem={({ item }) => {
          const { data, hora } = formatarDataHora(item.data_hora);
          return (
            <View style={[styles.cartao, item.concluido && styles.cartaoConcluido]}>
              <Text style={styles.cartaoIcone}>{iconePara(item.tipo)}</Text>
              <View style={styles.cartaoConteudo}>
                <Text style={[styles.cartaoTitulo, item.concluido && styles.textoConcluido]}>{item.titulo}</Text>
                <Text style={styles.cartaoData}>{data} às {hora}</Text>
                {!!item.notas && <Text style={styles.cartaoNotas}>{item.notas}</Text>}
              </View>
              {!item.concluido && (
                <Pressable
                  style={styles.botaoConcluir}
                  onPress={() => concluir(item)}
                  accessibilityRole="button"
                  accessibilityLabel={`Marcar ${item.titulo} como concluído`}>
                  <Text style={styles.botaoConcluirTexto}>✓</Text>
                </Pressable>
              )}
            </View>
          );
        }}
      />

      <Modal visible={modalAberto} animationType="slide" transparent onRequestClose={() => setModalAberto(false)}>
        <View style={styles.modalFundo}>
          <View style={styles.modalConteudo}>
            <Text style={styles.modalTitulo}>Novo evento</Text>

            <View style={styles.tipos}>
              {TIPOS.map((t) => (
                <Pressable
                  key={t.valor}
                  style={[styles.tipoChip, tipoNovo === t.valor && styles.tipoChipAtivo]}
                  onPress={() => setTipoNovo(t.valor)}>
                  <Text style={styles.tipoChipTexto}>{t.icone} {t.rotulo}</Text>
                </Pressable>
              ))}
            </View>

            <TextInput
              style={styles.modalInput}
              value={tituloNovo}
              onChangeText={setTituloNovo}
              placeholder="Título (ex: Consulta com Dra. Ana)"
              placeholderTextColor="#AAAAAA"
            />
            <View style={styles.linhaDataHora}>
              <TextInput
                style={[styles.modalInput, styles.inputData]}
                value={dataNova}
                onChangeText={setDataNova}
                placeholder="dd/mm/aaaa"
                placeholderTextColor="#AAAAAA"
                keyboardType="numbers-and-punctuation"
              />
              <TextInput
                style={[styles.modalInput, styles.inputHora]}
                value={horaNova}
                onChangeText={setHoraNova}
                placeholder="hh:mm"
                placeholderTextColor="#AAAAAA"
                keyboardType="numbers-and-punctuation"
              />
            </View>
            <TextInput
              style={styles.modalInput}
              value={notasNovas}
              onChangeText={setNotasNovas}
              placeholder="Notas (opcional)"
              placeholderTextColor="#AAAAAA"
            />

            <View style={styles.modalBotoes}>
              <Pressable style={styles.modalBotaoCancelar} onPress={() => setModalAberto(false)}>
                <Text style={styles.modalBotaoCancelarTexto}>Cancelar</Text>
              </Pressable>
              <Pressable
                style={[styles.modalBotaoSalvar, salvandoNovo && styles.botaoDesabilitado]}
                onPress={salvarNovoEvento}
                disabled={salvandoNovo}>
                <Text style={styles.modalBotaoSalvarTexto}>{salvandoNovo ? 'Salvando...' : 'Salvar'}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  cabecalho: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 24, paddingTop: 16, paddingBottom: 8,
  },
  titulo: { fontSize: 28, fontWeight: '700', color: COLORS.title },
  botaoAdicionar: { backgroundColor: COLORS.primary, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10 },
  botaoAdicionarTexto: { color: COLORS.background, fontWeight: '600', fontSize: 14 },
  vazio: { paddingHorizontal: 24, paddingTop: 60, alignItems: 'center' },
  vazioTexto: { fontSize: 16, fontWeight: '600', color: COLORS.title, marginBottom: 6 },
  vazioSubtexto: { fontSize: 13, color: COLORS.body, textAlign: 'center' },
  lista: { paddingHorizontal: 24, paddingTop: 12, paddingBottom: 24 },
  cartao: {
    flexDirection: 'row', alignItems: 'center', borderWidth: 1.5, borderColor: COLORS.border,
    borderRadius: 12, padding: 14, marginBottom: 10,
  },
  cartaoConcluido: { backgroundColor: '#F7F7F7', borderColor: '#EEEEEE' },
  cartaoIcone: { fontSize: 24, marginRight: 12 },
  cartaoConteudo: { flex: 1 },
  cartaoTitulo: { fontSize: 15, fontWeight: '600', color: COLORS.title },
  textoConcluido: { textDecorationLine: 'line-through', color: COLORS.body },
  cartaoData: { fontSize: 12, color: COLORS.body, marginTop: 2 },
  cartaoNotas: { fontSize: 12, color: COLORS.body, marginTop: 2, fontStyle: 'italic' },
  botaoConcluir: {
    width: 32, height: 32, borderRadius: 16, borderWidth: 1.5, borderColor: COLORS.primary,
    alignItems: 'center', justifyContent: 'center',
  },
  botaoConcluirTexto: { color: COLORS.primary, fontWeight: '700' },
  modalFundo: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  modalConteudo: { backgroundColor: COLORS.background, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 24 },
  modalTitulo: { fontSize: 20, fontWeight: '700', color: COLORS.title, marginBottom: 16 },
  tipos: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  tipoChip: { borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8 },
  tipoChipAtivo: { backgroundColor: COLORS.primaryLight, borderColor: COLORS.primary },
  tipoChipTexto: { fontSize: 13, color: COLORS.title },
  modalInput: {
    borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 12, fontSize: 14, color: COLORS.title, marginBottom: 12,
  },
  linhaDataHora: { flexDirection: 'row', gap: 10 },
  inputData: { flex: 2 },
  inputHora: { flex: 1 },
  modalBotoes: { flexDirection: 'row', gap: 10, marginTop: 8 },
  modalBotaoCancelar: { flex: 1, paddingVertical: 14, borderRadius: 10, borderWidth: 1.5, borderColor: COLORS.border, alignItems: 'center' },
  modalBotaoCancelarTexto: { color: COLORS.body, fontWeight: '600' },
  modalBotaoSalvar: { flex: 1, paddingVertical: 14, borderRadius: 10, backgroundColor: COLORS.primary, alignItems: 'center' },
  modalBotaoSalvarTexto: { color: COLORS.background, fontWeight: '600' },
  botaoDesabilitado: { opacity: 0.6 },
});
