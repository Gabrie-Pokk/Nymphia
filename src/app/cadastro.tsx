import { Link, router } from 'expo-router';
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

import { useAuth } from '@/components/auth-context';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL ?? 'http://192.168.1.100:8000';

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  primaryLight: '#FCE4EC',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
  erro: '#C0392B',
};

function emailValido(email: string): boolean {
  return email.includes('@') && email.includes('.');
}

export default function CadastroScreen() {
  const { login } = useAuth();
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [focoNome, setFocoNome] = useState(false);
  const [focoEmail, setFocoEmail] = useState(false);
  const [focoSenha, setFocoSenha] = useState(false);
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

  const validar = (): string | null => {
    if (nome.trim().length < 3) return 'Digite seu nome completo.';
    if (!emailValido(email)) return 'Digite um e-mail válido.';
    if (senha.length < 8) return 'A senha precisa ter pelo menos 8 caracteres.';
    return null;
  };

  const criarConta = async () => {
    const mensagemErro = validar();
    if (mensagemErro) {
      setErro(mensagemErro);
      return;
    }
    setErro('');
    setCarregando(true);
    try {
      const resposta = await fetch(`${BACKEND_URL}/auth/gestante/cadastro`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: nome.trim(), email, senha }),
      });
      const dados = await resposta.json();
      if (!resposta.ok) {
        setErro(dados.detail || 'Não foi possível criar sua conta.');
        return;
      }
      await login(dados.token, 'gestante', dados.id, dados.nome);
      router.replace('/onboarding-clinico');
    } catch {
      setErro('Não foi possível conectar. Verifique sua internet e tente novamente.');
    } finally {
      setCarregando(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <Text style={styles.titulo}>Criar conta</Text>
          <Text style={styles.subtitulo}>Comece a acompanhar sua gestação com a Nymphia</Text>

          <Text style={styles.label}>Nome completo</Text>
          <TextInput
            style={[styles.input, focoNome && styles.inputFocado]}
            value={nome}
            onChangeText={setNome}
            placeholder="Seu nome completo"
            placeholderTextColor="#AAAAAA"
            autoCapitalize="words"
            onFocus={() => setFocoNome(true)}
            onBlur={() => setFocoNome(false)}
          />

          <Text style={styles.label}>E-mail</Text>
          <TextInput
            style={[styles.input, focoEmail && styles.inputFocado]}
            value={email}
            onChangeText={setEmail}
            placeholder="seuemail@exemplo.com"
            placeholderTextColor="#AAAAAA"
            autoCapitalize="none"
            keyboardType="email-address"
            onFocus={() => setFocoEmail(true)}
            onBlur={() => setFocoEmail(false)}
          />

          <Text style={styles.label}>Senha</Text>
          <View style={[styles.inputSenhaWrapper, focoSenha && styles.inputFocado]}>
            <TextInput
              style={styles.inputSenha}
              value={senha}
              onChangeText={setSenha}
              placeholder="Mínimo 8 caracteres"
              placeholderTextColor="#AAAAAA"
              secureTextEntry={!mostrarSenha}
              onFocus={() => setFocoSenha(true)}
              onBlur={() => setFocoSenha(false)}
            />
            <Pressable onPress={() => setMostrarSenha(!mostrarSenha)} accessibilityRole="button">
              <Text style={styles.toggleSenha}>{mostrarSenha ? 'Ocultar' : 'Mostrar'}</Text>
            </Pressable>
          </View>

          {!!erro && <Text style={styles.erro}>{erro}</Text>}

          <Pressable
            style={[styles.botao, carregando && styles.botaoDesabilitado]}
            onPress={criarConta}
            disabled={carregando}
            accessibilityRole="button">
            <Text style={styles.botaoTexto}>{carregando ? 'Criando conta...' : 'Criar conta'}</Text>
          </Pressable>

          <Link href="/login" style={styles.link}>
            <Text style={styles.linkTexto}>Já tem conta? Entrar</Text>
          </Link>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  flex: { flex: 1 },
  scroll: { paddingHorizontal: 24, paddingTop: 48, paddingBottom: 24 },
  titulo: { fontSize: 28, fontWeight: '700', color: COLORS.title },
  subtitulo: { marginTop: 4, marginBottom: 32, fontSize: 15, color: COLORS.body },
  label: { fontSize: 14, fontWeight: '600', color: COLORS.title, marginBottom: 8 },
  input: {
    borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 12,
    paddingHorizontal: 16, paddingVertical: 14, fontSize: 15, color: COLORS.title, marginBottom: 20,
  },
  inputFocado: { borderColor: COLORS.primary },
  inputSenhaWrapper: {
    flexDirection: 'row', alignItems: 'center', borderWidth: 1.5, borderColor: COLORS.border,
    borderRadius: 12, paddingHorizontal: 16, marginBottom: 8,
  },
  inputSenha: { flex: 1, paddingVertical: 14, fontSize: 15, color: COLORS.title },
  toggleSenha: { color: COLORS.primary, fontSize: 13, fontWeight: '600' },
  erro: { color: COLORS.erro, fontSize: 13, marginTop: 8, marginBottom: 4 },
  botao: {
    backgroundColor: COLORS.primary, paddingVertical: 16, borderRadius: 12,
    alignItems: 'center', marginTop: 20,
  },
  botaoDesabilitado: { opacity: 0.6 },
  botaoTexto: { color: COLORS.background, fontSize: 18, fontWeight: '600' },
  link: { marginTop: 20, alignItems: 'center' },
  linkTexto: { color: COLORS.primary, fontSize: 14, fontWeight: '600', textAlign: 'center' },
});
