import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/perfil-clinico': 'http://127.0.0.1:8000',
      '/historico-familiar': 'http://127.0.0.1:8000',
      '/checkin': 'http://127.0.0.1:8000',
      '/conversa': 'http://127.0.0.1:8000',
      '/agenda': 'http://127.0.0.1:8000',
      '/vinculo': 'http://127.0.0.1:8000',
      '/exames': 'http://127.0.0.1:8000',
      '/risco': 'http://127.0.0.1:8000',
      '/emergencia': 'http://127.0.0.1:8000',
      '/parceiro': 'http://127.0.0.1:8000',
      '/comunidade': 'http://127.0.0.1:8000',
      '/dispositivos': 'http://127.0.0.1:8000',
      '/cinta': 'http://127.0.0.1:8000',
      '/governance': 'http://127.0.0.1:8000',
      '/meus-dados': 'http://127.0.0.1:8000',
      '/minha-conta': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/storage': 'http://127.0.0.1:8000'
    }
  }
})
