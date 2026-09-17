import { StyleSheet, Text, View } from 'react-native';

type ProgressBarProps = {
  currentStep: number;
  totalSteps: number;
};

export default function ProgressBar({ currentStep, totalSteps }: ProgressBarProps) {
  const pct = `${Math.round((currentStep / totalSteps) * 100)}%`;

  return (
    <View style={styles.container}>
      <View style={styles.track}>
        <View style={[styles.fill, { width: pct }]} />
      </View>
      <Text style={styles.texto}>
        Etapa {currentStep} de {totalSteps}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 4,
    gap: 8,
  },
  track: {
    height: 4,
    backgroundColor: '#E0E0E0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    backgroundColor: '#C2185B',
    borderRadius: 2,
  },
  texto: {
    fontSize: 13,
    color: '#555555',
  },
});
