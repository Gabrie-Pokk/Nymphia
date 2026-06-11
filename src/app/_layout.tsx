import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { Stack } from 'expo-router';
import { useColorScheme } from 'react-native';

import { AnimatedSplashOverlay } from '@/components/animated-icon';

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AnimatedSplashOverlay />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(main)" />
        <Stack.Screen name="onboarding" />
        <Stack.Screen name="cadastro" />
        <Stack.Screen name="login" />
        <Stack.Screen name="onboarding-clinico" />
        <Stack.Screen name="checkin" />
        <Stack.Screen name="alarmes" />
      </Stack>
    </ThemeProvider>
  );
}
