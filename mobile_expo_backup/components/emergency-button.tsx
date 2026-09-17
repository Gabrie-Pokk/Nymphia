import { router, usePathname } from 'expo-router';
import { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

const COLORS = {
  vermelho: '#C0392B',
  vermelhoEscuro: '#922B21',
  branco: '#FFFFFF',
};

const TEMPO_CONFIRMACAO_MS = 4000;

// Botão de emergência flutuante -- fica visível em todas as telas do app,
// exceto na própria tela de emergência (verificado pelo pathname).
//
// Comportamento: 1º toque expande e pede confirmação; 2º toque (dentro de
// alguns segundos) navega pra tela de emergência. Sem confirmação, volta
// ao estado normal sozinho -- evita acionamento acidental sem atrapalhar
// quem realmente precisa.
export default function EmergencyButton() {
  const pathname = usePathname();
  const [confirmando, setConfirmando] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Não renderiza na própria tela de emergência
  if (pathname === '/emergencia') {
    return null;
  }

  const limparTimeout = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  const aoPressionar = () => {
    if (!confirmando) {
      setConfirmando(true);
      timeoutRef.current = setTimeout(() => {
        setConfirmando(false);
      }, TEMPO_CONFIRMACAO_MS);
      return;
    }
    limparTimeout();
    setConfirmando(false);
    router.push('/emergencia');
  };

  return (
    <View style={styles.container} pointerEvents="box-none">
      <Pressable
        style={[styles.botao, confirmando && styles.botaoConfirmando]}
        onPress={aoPressionar}
        accessibilityRole="button"
        accessibilityLabel={confirmando ? 'Toque novamente para confirmar emergência' : 'Emergência'}>
        {confirmando ? (
          <Text style={styles.textoConfirmar}>Toque{'\n'}de novo</Text>
        ) : (
          <Text style={styles.icone}>🚨</Text>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 28,
    right: 20,
    zIndex: 999,
    elevation: 999,
  },
  botao: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: COLORS.vermelho,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
  },
  botaoConfirmando: {
    backgroundColor: COLORS.vermelhoEscuro,
    width: 76,
    height: 76,
    borderRadius: 38,
  },
  icone: {
    fontSize: 26,
  },
  textoConfirmar: {
    color: COLORS.branco,
    fontSize: 11,
    fontWeight: '700',
    textAlign: 'center',
    lineHeight: 13,
  },
});
