import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { I18nProvider } from './context/I18nContext'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <I18nProvider>
        <App />
      </I18nProvider>
    </AuthProvider>
  </React.StrictMode>,
)

// Service Worker do PWA (funciona offline, inclusive a tela de emergência).
// Fica aqui, e não num <script> dentro do index.html, para a CSP não precisar
// liberar script inline.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .catch((err) => console.warn('[Nymphia PWA] Falha ao registrar Service Worker:', err));
  });
}
