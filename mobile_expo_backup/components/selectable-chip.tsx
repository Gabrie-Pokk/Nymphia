import { Pressable, StyleSheet, Text } from 'react-native';

type SelectableChipProps = {
  label: string;
  selected: boolean;
  onPress: () => void;
};

export default function SelectableChip({ label, selected, onPress }: SelectableChipProps) {
  return (
    <Pressable
      style={[styles.chip, selected && styles.chipSelecionado]}
      onPress={onPress}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: selected }}>
      <Text style={[styles.texto, selected && styles.textoSelecionado]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: '#E0E0E0',
    backgroundColor: '#FFFFFF',
  },
  chipSelecionado: {
    backgroundColor: '#C2185B',
    borderColor: '#C2185B',
  },
  texto: {
    fontSize: 14,
    fontWeight: '500',
    color: '#555555',
  },
  textoSelecionado: {
    color: '#FFFFFF',
  },
});
