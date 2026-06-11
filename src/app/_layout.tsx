import AsyncStorage from '@react-native-async-storage/async-storage';
import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { Stack } from 'expo-router';
import { useEffect, useState } from 'react';
import { useColorScheme } from 'react-native';

import { AnimatedSplashOverlay } from '@/components/animated-icon';

import { ONBOARDING_STORAGE_KEY } from './onboarding';

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState<boolean | null>(null);

  useEffect(() => {
    AsyncStorage.getItem(ONBOARDING_STORAGE_KEY).then((value) => {
      setHasCompletedOnboarding(value === 'true');
    });
  }, []);

  if (hasCompletedOnboarding === null) {
    return null;
  }

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AnimatedSplashOverlay />
      <Stack
        screenOptions={{ headerShown: false }}
        initialRouteName={hasCompletedOnboarding ? '(main)' : 'onboarding'}>
        <Stack.Screen name="onboarding" />
        <Stack.Screen name="(main)" />
      </Stack>
    </ThemeProvider>
  );
}
