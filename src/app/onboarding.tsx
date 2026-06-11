import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { SymbolView, type SymbolViewProps } from 'expo-symbols';
import { useRef, useState } from 'react';
import {
  Dimensions,
  FlatList,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  StyleSheet,
  Text,
  View,
  type ListRenderItemInfo,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export const ONBOARDING_STORAGE_KEY = '@nymphia/onboarding_complete';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const COLORS = {
  background: '#FFFFFF',
  primary: '#C2185B',
  title: '#212121',
  body: '#555555',
};

type OnboardingStep = {
  icon: SymbolViewProps['name'];
  title: string;
  description: string;
};

const STEPS: OnboardingStep[] = [
  {
    icon: { ios: 'heart.fill', android: 'favorite', web: 'favorite' },
    title: 'Bem-vinda à Nymphia',
    description: 'Seu coach de saúde durante toda a gestação.',
  },
  {
    icon: { ios: 'shield.fill', android: 'shield', web: 'shield' },
    title: 'Redução de risco real',
    description:
      'A IA aprende com você e identifica sinais de risco antes que virem problema.',
  },
  {
    icon: { ios: 'stethoscope', android: 'medical_services', web: 'medical_services' },
    title: 'Seu médico mais preparado',
    description: 'Relatórios automáticos chegam pro seu médico antes de cada consulta.',
  },
];

function OnboardingSlide({ item }: { item: OnboardingStep }) {
  return (
    <View style={styles.slide}>
      <SymbolView name={item.icon} tintColor={COLORS.primary} size={88} />
      <Text style={styles.slideTitle}>{item.title}</Text>
      <Text style={styles.slideDescription}>{item.description}</Text>
    </View>
  );
}

export default function OnboardingScreen() {
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef<FlatList<OnboardingStep>>(null);

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const index = Math.round(event.nativeEvent.contentOffset.x / SCREEN_WIDTH);
    setActiveIndex(index);
  };

  const finishOnboarding = async () => {
    await AsyncStorage.setItem(ONBOARDING_STORAGE_KEY, 'true');
    router.replace('/cadastro');
  };

  const renderItem = ({ item }: ListRenderItemInfo<OnboardingStep>) => (
    <OnboardingSlide item={item} />
  );

  const isLastStep = activeIndex === STEPS.length - 1;

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        ref={listRef}
        style={styles.carousel}
        data={STEPS}
        renderItem={renderItem}
        keyExtractor={(_, index) => String(index)}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={onScroll}
        scrollEventThrottle={16}
        bounces={false}
      />

      <View style={styles.footer}>
        <View style={styles.dots}>
          {STEPS.map((_, index) => (
            <View
              key={index}
              style={[styles.dot, index === activeIndex && styles.dotActive]}
            />
          ))}
        </View>

        {isLastStep ? (
          <Pressable
            style={styles.button}
            accessibilityRole="button"
            onPress={finishOnboarding}>
            <Text style={styles.buttonText}>Começar</Text>
          </Pressable>
        ) : (
          <View style={styles.buttonPlaceholder} />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  carousel: {
    flex: 1,
  },
  slide: {
    width: SCREEN_WIDTH,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 48,
  },
  slideTitle: {
    marginTop: 32,
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.title,
    textAlign: 'center',
  },
  slideDescription: {
    marginTop: 16,
    fontSize: 16,
    lineHeight: 24,
    color: COLORS.body,
    textAlign: 'center',
  },
  footer: {
    paddingHorizontal: 24,
    paddingBottom: 32,
    gap: 24,
  },
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#E0E0E0',
  },
  dotActive: {
    backgroundColor: COLORS.primary,
    width: 24,
  },
  button: {
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
  buttonPlaceholder: {
    height: 52,
  },
});
