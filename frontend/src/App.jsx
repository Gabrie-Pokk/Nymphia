import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import LotusLogo from './components/LotusLogo';
import FloatingEmergencyButton from './components/FloatingEmergencyButton';
import PWAInstallPrompt from './components/PWAInstallPrompt';

// Páginas Públicas
import WelcomeIntro from './pages/WelcomeIntro';
import Login from './pages/Login';
import RegisterGestante from './pages/RegisterGestante';
import RegisterProfissional from './pages/RegisterProfissional';
import RegisterParceiro from './pages/RegisterParceiro';
import EmergencyScreen from './pages/EmergencyScreen';

// Páginas da Gestante
import OnboardingClinico from './pages/gestante/OnboardingClinico';
import GestanteHome from './pages/gestante/GestanteHome';
import DailyCheckin from './pages/gestante/DailyCheckin';
import AiChat from './pages/gestante/AiChat';
import Agenda from './pages/gestante/Agenda';
import PrenatalCard from './pages/gestante/PrenatalCard';
import Exams from './pages/gestante/Exams';
import VisualDiary from './pages/gestante/VisualDiary';
import Devices from './pages/gestante/Devices';
import CintaNymphia from './pages/gestante/CintaNymphia';
import VinculoMedico from './pages/gestante/VinculoMedico';
import MyDataLGPD from './pages/gestante/MyDataLGPD';
import CommunityFeed from './pages/comunidade/CommunityFeed';
import SubscriptionScreen from './pages/gestante/SubscriptionScreen';

// Páginas do Profissional
import DoctorDashboard from './pages/profissional/DoctorDashboard';
import PatientRecord from './pages/profissional/PatientRecord';
import GenerateInvite from './pages/profissional/GenerateInvite';

// Páginas do Parceiro
import PartnerDashboard from './pages/parceiro/PartnerDashboard';

import { Home, Activity, MessageSquare, Calendar, Shield, LogOut } from 'lucide-react';

export default function App() {
  const { user, isAuthenticated, logout, authHeaders } = useAuth();
  const [currentPath, setCurrentPath] = useState(() => window.location.pathname || '/');
  const [introViewed, setIntroViewed] = useState(() => localStorage.getItem('nymphia_intro_viewed') === 'true');
  const [onboardingCompleto, setOnboardingCompleto] = useState(false);
  const [verificandoOnboarding, setVerificandoOnboarding] = useState(true);
  const [selectedPatientId, setSelectedPatientId] = useState(null);

  // Sincroniza rota com o histórico do navegador (HTML5 History API)
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Verifica se gestante já completou onboarding clínico
  useEffect(() => {
    if (isAuthenticated && user?.perfil === 'gestante') {
      setVerificandoOnboarding(true);
      fetch('/perfil-clinico', { headers: authHeaders() })
        .then((res) => {
          if (res.ok) {
            setOnboardingCompleto(true);
          } else {
            setOnboardingCompleto(false);
          }
        })
        .catch(() => {
          setOnboardingCompleto(false);
        })
        .finally(() => {
          setVerificandoOnboarding(false);
        });
    } else {
      setVerificandoOnboarding(false);
    }
  }, [isAuthenticated, user]);

  // CRITÉRIO OBRIGATÓRIO: Abrir /emergencia sem sessão mostra o SAMU, nunca o login!
  if (currentPath === '/emergencia') {
    return (
      <div className="app-container">
        <PWAInstallPrompt />
        <EmergencyScreen onExit={() => navigate('/')} />
      </div>
    );
  }

  // Se não autenticado:
  if (!isAuthenticated) {
    if (!introViewed) {
      return (
        <div className="app-container">
          <PWAInstallPrompt />
          <WelcomeIntro onFinish={() => setIntroViewed(true)} />
          <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
        </div>
      );
    }

    if (currentPath === '/cadastro-gestante') {
      return (
        <div className="app-container">
          <PWAInstallPrompt />
          <RegisterGestante onBackToLogin={() => navigate('/login')} />
          <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
        </div>
      );
    }

    if (currentPath === '/cadastro-profissional') {
      return (
        <div className="app-container">
          <PWAInstallPrompt />
          <RegisterProfissional onBackToLogin={() => navigate('/login')} />
          <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
        </div>
      );
    }

    if (currentPath === '/cadastro-parceiro') {
      return (
        <div className="app-container">
          <PWAInstallPrompt />
          <RegisterParceiro onBackToLogin={() => navigate('/login')} />
          <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
        </div>
      );
    }

    return (
      <div className="app-container">
        <PWAInstallPrompt />
        <Login
          onNavigateRegister={() => navigate('/cadastro-gestante')}
          onNavigateRegisterProf={() => navigate('/cadastro-profissional')}
          onNavigateRegisterParc={() => navigate('/cadastro-parceiro')}
        />
        <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
      </div>
    );
  }

  // SE AUTENTICADO:
  return (
    <div className={`app-container ${user?.perfil === 'profissional' ? 'desktop-expanded' : ''}`}>
      {/* Banner de instalação PWA quando não estiver instalado */}
      <PWAInstallPrompt />

      {/* Top Header Comum */}
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }} onClick={() => navigate('/')}>
          <LotusLogo size={28} color="#FFFFFF" />
          <div>
            <h1 style={{ color: '#FFFFFF', margin: 0, fontSize: '1.28rem', fontWeight: 800 }}>Nymphia</h1>
            <span className="header-slogan" style={{ color: '#FDF0F2', opacity: 0.95, fontSize: '0.78rem' }}>Cada batimento importa.</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.78rem', backgroundColor: 'rgba(255,255,255,0.2)', padding: '3px 8px', borderRadius: 'var(--radius-full)', textTransform: 'capitalize' }}>
            {user?.perfil}
          </span>
          <button
            onClick={() => {
              logout();
              navigate('/login');
            }}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#FFFFFF',
              padding: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Sair da conta"
            aria-label="Encerrar sessão"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* Roteamento Interno por Perfil */}
      <main className="app-main">
        {user?.perfil === 'gestante' && (
          <>
            {verificandoOnboarding ? (
              <div style={{ padding: '24px', textAlign: 'center' }}>Carregando dados clínicos...</div>
            ) : !onboardingCompleto ? (
              <OnboardingClinico onCompleted={() => setOnboardingCompleto(true)} />
            ) : (
              <>
                {currentPath === '/' && <GestanteHome onNavigate={navigate} />}
                {currentPath === '/checkin' && <DailyCheckin onBack={() => navigate('/')} />}
                {currentPath === '/conversa' && <AiChat onBack={() => navigate('/')} />}
                {currentPath === '/agenda' && <Agenda onBack={() => navigate('/')} />}
                {currentPath === '/prenatal-card' && <PrenatalCard onBack={() => navigate('/')} />}
                {currentPath === '/exames' && <Exams onBack={() => navigate('/')} />}
                {currentPath === '/diario-visual' && <VisualDiary onBack={() => navigate('/')} />}
                {currentPath === '/dispositivos' && <Devices onBack={() => navigate('/')} />}
                {currentPath === '/cinta' && <CintaNymphia onBack={() => navigate('/')} onNavigateEmergency={() => navigate('/emergencia')} />}
                {currentPath === '/vinculo-medico' && <VinculoMedico onBack={() => navigate('/')} />}
                {currentPath === '/comunidade' && <CommunityFeed onBack={() => navigate('/')} />}
                {currentPath === '/assinatura' && <SubscriptionScreen onBack={() => navigate('/')} />}
                {currentPath === '/planos' && <SubscriptionScreen onBack={() => navigate('/')} />}
                {currentPath === '/meus-dados' && <MyDataLGPD onBack={() => navigate('/')} />}
              </>
            )}
          </>
        )}

        {user?.perfil === 'profissional' && (
          <>
            {currentPath === '/' && (
              <DoctorDashboard
                onSelectPatient={(id) => {
                  setSelectedPatientId(id);
                  navigate('/paciente');
                }}
                onNavigateGenerateInvite={() => navigate('/convite')}
              />
            )}
            {currentPath === '/paciente' && (
              <PatientRecord patientId={selectedPatientId} onBack={() => navigate('/')} />
            )}
            {currentPath === '/convite' && (
              <GenerateInvite onBack={() => navigate('/')} />
            )}
          </>
        )}

        {user?.perfil === 'parceiro' && (
          <PartnerDashboard onNavigateEmergency={() => navigate('/emergencia')} />
        )}
      </main>

      {/* Barra de Navegação Inferior para Gestante */}
      {user?.perfil === 'gestante' && onboardingCompleto && (
        <nav className="bottom-nav" aria-label="Navegação Principal">
          <button
            className={`nav-item ${currentPath === '/' ? 'active' : ''}`}
            onClick={() => navigate('/')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Home size={20} />
            <span>Início</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/checkin' ? 'active' : ''}`}
            onClick={() => navigate('/checkin')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Activity size={20} />
            <span>Check-in</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/conversa' ? 'active' : ''}`}
            onClick={() => navigate('/conversa')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <MessageSquare size={20} />
            <span>Chat IA</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/agenda' ? 'active' : ''}`}
            onClick={() => navigate('/agenda')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Calendar size={20} />
            <span>Agenda</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/meus-dados' ? 'active' : ''}`}
            onClick={() => navigate('/meus-dados')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Shield size={20} />
            <span>LGPD</span>
          </button>
        </nav>
      )}

      {/* Botão de Emergência SAMU Permanente (56x56, Vermelho #C0392B, 2 toques) */}
      <FloatingEmergencyButton
        currentPath={currentPath}
        onNavigateEmergency={() => navigate('/emergencia')}
      />
    </div>
  );
}
