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

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  title: '#212121',
  body: '#555555',
  border: '#E0E0E0',
  error: '#B71C1C',
};

export default function CadastroScreen() {
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState('');
  const [focado, setFocado] = useState<string | null>(null);

  const validar = () => {
    if (nome.trim().length < 3) {
      setErro('Digite seu nome completo.');
      return false;
    }
    if (!email.includes('@') || !email.includes('.')) {
      setErro('Digite um e-mail válido.');
      return false;
    }
    if (senha.length < 8) {
      setErro('A senha precisa ter pelo menos 8 caracteres.');
      return false;
    }
    setErro('');
    return true;
  };

  const criarConta = () => {
    if (!validar()) return;
    // TODO: integrar com backend (Supabase) — por enquanto segue direto
    router.replace('/onboarding-clinico');
  };

  const inputStyle = (campo: string) => [
    styles.input,
    focado === campo && styles.inputFocado,
  ];

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled">
          <Text style={styles.titulo}>Criar conta</Text>
          <Text style={styles.subtitulo}>Vamos começar sua jornada.</Text>

          <View style={styles.form}>
            <Text style={styles.label}>Nome completo</Text>
            <TextInput
              style={inputStyle('nome')}
              value={nome}
              onChangeText={setNome}
              placeholder="Maria da Silva"
              placeholderTextColor="#AAAAAA"
              autoCapitalize="words"
              onFocus={() => setFocado('nome')}
              onBlur={() => setFocado(null)}
            />

            <Text style={styles.label}>E-mail</Text>
            <TextInput
              style={inputStyle('email')}
              value={email}
              onChangeText={setEmail}
              placeholder="maria@email.com"
              placeholderTextColor="#AAAAAA"
              autoCapitalize="none"
              keyboardType="email-address"
              onFocus={() => setFocado('email')}
              onBlur={() => setFocado(null)}
            />

            <Text style={styles.label}>Senha</Text>
            <View style={styles.senhaContainer}>
              <TextInput
                style={[inputStyle('senha'), styles.senhaInput]}
                value={senha}
                onChangeText={setSenha}
                placeholder="Mínimo 8 caracteres"
                placeholderTextColor="#AAAAAA"
                secureTextEntry={!mostrarSenha}
                autoCapitalize="none"
                onFocus={() => setFocado('senha')}
                onBlur={() => setFocado(null)}
              />
              <Pressable
                style={styles.mostrarBotao}
                onPress={() => setMostrarSenha(!mostrarSenha)}>
                <Text style={styles.mostrarTexto}>
                  {mostrarSenha ? 'Ocultar' : 'Mostrar'}
                </Text>
              </Pressable>
            </View>

            {erro !== '' && <Text style={styles.erro}>{erro}</Text>}
          </View>

          <Pressable
            style={styles.botao}
            accessibilityRole="button"
            onPress={criarConta}>
            <Text style={styles.botaoTexto}>Criar conta</Text>
          </Pressable>

          <Pressable
            style={styles.linkContainer}
            onPress={() => router.push('/login')}>
            <Text style={styles.linkTexto}>
              Já tenho conta. <Text style={styles.linkDestaque}>Entrar.</Text>
            </Text>
          </Pressable>
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
  flex: {
    flex: 1,
  },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 48,
    paddingBottom: 32,
  },
  titulo: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.title,
  },
  subtitulo: {
    marginTop: 8,
    fontSize: 16,
    color: COLORS.body,
  },
  form: {
    marginTop: 32,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.title,
    marginBottom: 8,
    marginTop: 16,
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
  senhaContainer: {
    position: 'relative',
  },
  senhaInput: {
    paddingRight: 90,
  },
  mostrarBotao: {
    position: 'absolute',
    right: 16,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
  },
  mostrarTexto: {
    color: COLORS.primary,
    fontWeight: '600',
    fontSize: 14,
  },
  erro: {
    marginTop: 16,
    color: COLORS.error,
    fontSize: 14,
  },
  botao: {
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 32,
  },
  botaoTexto: {
    color: COLORS.background,
    fontSize: 18,
    fontWeight: '600',
  },
  linkContainer: {
    marginTop: 24,
    alignItems: 'center',
  },
  linkTexto: {
    fontSize: 15,
    color: COLORS.body,
  },
  linkDestaque: {
    color: COLORS.primary,
    fontWeight: '700',
  },
});