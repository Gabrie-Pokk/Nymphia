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
import VinculoMedico from './pages/gestante/VinculoMedico';
import MyDataLGPD from './pages/gestante/MyDataLGPD';
import CommunityFeed from './pages/comunidade/CommunityFeed';
import SubscriptionScreen from './pages/gestante/SubscriptionScreen';
import QuizGostos from './pages/gestante/QuizGostos';
import BodyVision from './pages/gestante/BodyVision';
import Antropometria from './pages/gestante/Antropometria';

// Páginas do Profissional
import DoctorDashboard from './pages/profissional/DoctorDashboard';
import PatientRecord from './pages/profissional/PatientRecord';
import GenerateInvite from './pages/profissional/GenerateInvite';

// Páginas do Parceiro
import PartnerDashboard from './pages/parceiro/PartnerDashboard';

import { Home, Activity, MessageSquare, Calendar, Shield, LogOut, Heart } from 'lucide-react';

const SUBROTAS_GESTANTE = [
  '/checkin', '/conversa', '/agenda', '/prenatal-card', '/exames',
  '/diario-visual', '/dispositivos', '/vinculo-medico', '/comunidade',
  '/assinatura', '/planos', '/meus-dados', '/quiz-gostos',
  '/visao-corporal', '/antropometria'
];

const SUBROTAS_PROFISSIONAL = [
  '/paciente', '/convite'
];

const SUBROTAS_PARCEIRO = [
  '/quiz-gostos', '/agenda', '/checkin'
];

export default function App() {
  const { user, isAuthenticated, logout, authHeaders, login } = useAuth();
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

  // Se o usuário estiver autenticado e em rota pública de login/cadastro, redireciona imediatamente para a tela inicial '/'
  useEffect(() => {
    if (isAuthenticated) {
      const rotasPublicas = [
        '/login',
        '/cadastro-gestante',
        '/cadastro-profissional',
        '/cadastro-parceiro',
        '/welcome'
      ];
      if (rotasPublicas.includes(currentPath) || !currentPath || currentPath === '') {
        navigate('/');
      }
    }
  }, [isAuthenticated, currentPath]);

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
          <RegisterGestante
            onBackToLogin={() => navigate('/login')}
            onRegisterSuccess={() => navigate('/')}
          />
          <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
        </div>
      );
    }

    if (currentPath === '/cadastro-profissional') {
      return (
        <div className="app-container">
          <PWAInstallPrompt />
          <RegisterProfissional
            onBackToLogin={() => navigate('/login')}
            onRegisterSuccess={() => navigate('/')}
          />
          <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
        </div>
      );
    }

    if (currentPath === '/cadastro-parceiro') {
      return (
        <div className="app-container">
          <PWAInstallPrompt />
          <RegisterParceiro
            onBackToLogin={() => navigate('/login')}
            onRegisterSuccess={() => navigate('/')}
          />
          <FloatingEmergencyButton currentPath={currentPath} onNavigateEmergency={() => navigate('/emergencia')} />
        </div>
      );
    }

    return (
      <div className="app-container">
        <PWAInstallPrompt />
        <Login
          onLoginSuccess={() => navigate('/')}
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

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {user?.perfil === 'gestante' && (
            <button
              onClick={async () => {
                try {
                  const res = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: 'parceiro@nymphia.com.br', senha: 'senhaMaternidade123' })
                  });
                  const d = await res.json();
                  if (d.token) {
                    login(d.token, d);
                    navigate('/');
                  }
                } catch (e) {}
              }}
              style={{
                backgroundColor: 'rgba(255,255,255,0.22)',
                border: '1px solid rgba(255,255,255,0.4)',
                borderRadius: 'var(--radius-full)',
                color: '#FFFFFF',
                fontSize: '0.72rem',
                fontWeight: 600,
                padding: '4px 10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
              title="Alternar para visualização de Parceiro (Lucas)"
            >
              🤝 Ir p/ Parceiro
            </button>
          )}

          {user?.perfil === 'parceiro' && (
            <button
              onClick={async () => {
                try {
                  const res = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: 'gestante@nymphia.com.br', senha: 'senhaMaternidade123' })
                  });
                  const d = await res.json();
                  if (d.token) {
                    login(d.token, d);
                    navigate('/');
                  }
                } catch (e) {}
              }}
              style={{
                backgroundColor: 'rgba(255,255,255,0.22)',
                border: '1px solid rgba(255,255,255,0.4)',
                borderRadius: 'var(--radius-full)',
                color: '#FFFFFF',
                fontSize: '0.72rem',
                fontWeight: 600,
                padding: '4px 10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
              title="Alternar para visualização da Gestante (Mariana)"
            >
              🌸 Ir p/ Gestante
            </button>
          )}

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
                {(currentPath === '/' || !SUBROTAS_GESTANTE.includes(currentPath)) && (
                  <GestanteHome onNavigate={navigate} />
                )}
                {currentPath === '/checkin' && <DailyCheckin onBack={() => navigate('/')} />}
                {currentPath === '/conversa' && <AiChat onBack={() => navigate('/')} />}
                {currentPath === '/agenda' && <Agenda onBack={() => navigate('/')} />}
                {currentPath === '/prenatal-card' && <PrenatalCard onBack={() => navigate('/')} />}
                {currentPath === '/exames' && <Exams onBack={() => navigate('/')} />}
                {currentPath === '/diario-visual' && <VisualDiary onBack={() => navigate('/')} />}
                {currentPath === '/dispositivos' && <Devices onBack={() => navigate('/')} />}
                                {currentPath === '/vinculo-medico' && <VinculoMedico onBack={() => navigate('/')} />}
                {currentPath === '/comunidade' && <CommunityFeed onBack={() => navigate('/')} />}
                {currentPath === '/assinatura' && <SubscriptionScreen onBack={() => navigate('/')} />}
                {currentPath === '/planos' && <SubscriptionScreen onBack={() => navigate('/')} />}
                {currentPath === '/meus-dados' && <MyDataLGPD onBack={() => navigate('/')} />}
                {currentPath === '/quiz-gostos' && <QuizGostos onBack={() => navigate('/')} />}
                {currentPath === '/visao-corporal' && <BodyVision onBack={() => navigate('/')} />}
                {currentPath === '/antropometria' && <Antropometria onBack={() => navigate('/')} />}
              </>
            )}
          </>
        )}

        {user?.perfil === 'profissional' && (
          <>
            {(currentPath === '/' || !SUBROTAS_PROFISSIONAL.includes(currentPath)) && (
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
          <>
            {(currentPath === '/' || !SUBROTAS_PARCEIRO.includes(currentPath)) && (
              <PartnerDashboard
                onNavigateEmergency={() => navigate('/emergencia')}
                onNavigateQuiz={() => navigate('/quiz-gostos')}
                onNavigateCheckin={() => navigate('/checkin')}
                onNavigateAgenda={() => navigate('/agenda')}
              />
            )}
            {currentPath === '/quiz-gostos' && <QuizGostos onBack={() => navigate('/')} />}
            {currentPath === '/checkin' && <DailyCheckin onBack={() => navigate('/')} />}
            {currentPath === '/agenda' && <Agenda onBack={() => navigate('/')} />}
          </>
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

      {/* Barra de Navegação Inferior para Parceiro */}
      {user?.perfil === 'parceiro' && (
        <nav className="bottom-nav" aria-label="Navegação do Parceiro">
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
            className={`nav-item ${currentPath === '/agenda' ? 'active' : ''}`}
            onClick={() => navigate('/agenda')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Calendar size={20} />
            <span>Agenda</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/quiz-gostos' ? 'active' : ''}`}
            onClick={() => navigate('/quiz-gostos')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Heart size={20} />
            <span>Mimos</span>
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
