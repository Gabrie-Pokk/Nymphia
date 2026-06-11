import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  secondary: '#7B1FA2',
};

export default function WelcomeScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Nymphia</Text>
        <Text style={styles.tagline}>Cada batimento importa.</Text>
      </View>

      <Pressable style={styles.button} accessibilityRole="button">
        <Text style={styles.buttonText}>Começar</Text>
      </Pressable>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingHorizontal: 24,
    paddingBottom: 32,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 48,
    fontWeight: '700',
    color: COLORS.primary,
    textAlign: 'center',
  },
  tagline: {
    marginTop: 12,
    fontSize: 18,
    fontStyle: 'italic',
    color: COLORS.secondary,
    textAlign: 'center',
  },
  button: {
    alignSelf: 'stretch',
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonText: {
    color: COLORS.background,
    fontSize: 18,
    fontWeight: '600',
  },
});
