import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { Stack } from 'expo-router';
import { useColorScheme } from 'react-native';
import { View } from 'react-native';

import { AuthProvider } from '@/components/auth-context';
import { AnimatedSplashOverlay } from '@/components/animated-icon';
import EmergencyButton from '@/components/emergency-button';

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <AuthProvider>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <View style={{ flex: 1 }}>
          <AnimatedSplashOverlay />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="(main)" />
            <Stack.Screen name="onboarding" />
            <Stack.Screen name="cadastro" />
            <Stack.Screen name="login" />
            <Stack.Screen name="onboarding-clinico" />
            <Stack.Screen name="checkin" />
            <Stack.Screen name="agenda" />
            <Stack.Screen name="alarmes" />
            <Stack.Screen name="emergencia" options={{ presentation: 'fullScreenModal' }} />
          </Stack>
          <EmergencyButton />
        </View>
      </ThemeProvider>
    </AuthProvider>
  );
}
