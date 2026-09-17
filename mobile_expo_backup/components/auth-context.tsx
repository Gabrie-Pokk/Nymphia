import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

const TOKEN_KEY = '@nymphia/token';
const PERFIL_KEY = '@nymphia/perfil';
const ID_KEY = '@nymphia/conta_id';
const NOME_KEY = '@nymphia/nome';

export type Perfil = 'gestante' | 'profissional';

type AuthState = {
  token: string | null;
  perfil: Perfil | null;
  id: string | null;
  nome: string | null;
  carregando: boolean; // true enquanto confere o AsyncStorage na subida do app
};

type AuthContextType = AuthState & {
  login: (token: string, perfil: Perfil, id: string, nome: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    perfil: null,
    id: null,
    nome: null,
    carregando: true,
  });

  // Na subida do app, confere se já existe sessão salva -- assim a
  // gestante não precisa logar de novo toda vez que abre o app.
  useEffect(() => {
    (async () => {
      const [token, perfil, id, nome] = await Promise.all([
        AsyncStorage.getItem(TOKEN_KEY),
        AsyncStorage.getItem(PERFIL_KEY),
        AsyncStorage.getItem(ID_KEY),
        AsyncStorage.getItem(NOME_KEY),
      ]);
      setState({
        token,
        perfil: perfil === 'gestante' || perfil === 'profissional' ? perfil : null,
        id,
        nome,
        carregando: false,
      });
    })();
  }, []);

  const login = async (token: string, perfil: Perfil, id: string, nome: string) => {
    await Promise.all([
      AsyncStorage.setItem(TOKEN_KEY, token),
      AsyncStorage.setItem(PERFIL_KEY, perfil),
      AsyncStorage.setItem(ID_KEY, id),
      AsyncStorage.setItem(NOME_KEY, nome),
    ]);
    setState({ token, perfil, id, nome, carregando: false });
  };

  const logout = async () => {
    await Promise.all([
      AsyncStorage.removeItem(TOKEN_KEY),
      AsyncStorage.removeItem(PERFIL_KEY),
      AsyncStorage.removeItem(ID_KEY),
      AsyncStorage.removeItem(NOME_KEY),
    ]);
    setState({ token: null, perfil: null, id: null, nome: null, carregando: false });
  };

  return <AuthContext.Provider value={{ ...state, login, logout }}>{children}</AuthContext.Provider>;
}

// Hook que qualquer tela usa pra pegar o usuário logado e as funções
// de login/logout. Lança erro claro se alguém esquecer de envolver a
// tela no AuthProvider -- melhor falhar na hora do que silenciosamente
// devolver undefined.
export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth precisa ser chamado dentro de um <AuthProvider>.');
  }
  return ctx;
}

// Helper pra chamadas autenticadas -- inclui o Bearer token automaticamente,
// evitando repetir esse cabeçalho em cada tela.
export async function fetchAutenticado(url: string, token: string, opcoes: RequestInit = {}) {
  return fetch(url, {
    ...opcoes,
    headers: {
      'Content-Type': 'application/json',
      ...opcoes.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}
