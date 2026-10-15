import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import LotusLogo from './components/LotusLogo';
import FloatingEmergencyButton from './components/FloatingEmergencyButton';
import PWAInstallPrompt from './components/PWAInstallPrompt';
import { apiFetch } from './utils/api';

// Páginas Públicas
import WelcomeIntro from './pages/WelcomeIntro';
import Login from './pages/Login';
import EquipeAdmin from './pages/EquipeAdmin';
import RegisterGestante from './pages/RegisterGestante';
import RegisterProfissional from './pages/RegisterProfissional';
import RegisterParceiro from './pages/RegisterParceiro';
import EmergencyScreen from './pages/EmergencyScreen';
import LegalModal from './components/LegalModal';

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
import BemEstarEmocional from './pages/gestante/BemEstarEmocional';

// Páginas do Profissional
import DoctorDashboard from './pages/profissional/DoctorDashboard';
import PatientRecord from './pages/profissional/PatientRecord';
import GenerateInvite from './pages/profissional/GenerateInvite';

// Páginas do Parceiro
import PartnerDashboard from './pages/parceiro/PartnerDashboard';

import { useI18n } from './context/I18nContext';
import { Home, Activity, MessageSquare, Calendar, Shield, LogOut, Heart, Globe } from 'lucide-react';

const SUBROTAS_GESTANTE = [
  '/checkin', '/conversa', '/agenda', '/prenatal-card', '/exames',
  '/diario-visual', '/dispositivos', '/vinculo-medico', '/comunidade',
  '/assinatura', '/planos', '/meus-dados', '/quiz-gostos',
  '/visao-corporal', '/antropometria', '/bem-estar-emocional'
];

const SUBROTAS_PROFISSIONAL = [
  '/paciente', '/convite'
];

const SUBROTAS_PARCEIRO = [
  '/quiz-gostos', '/agenda', '/checkin'
];

export default function App() {
  const { user, isAuthenticated, logout, authHeaders, login } = useAuth();
  const { lang, setLang, t } = useI18n();
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

  // Link de redefinição de senha aberto com alguém já logado neste aparelho:
  // sai da sessão atual para a tela de login abrir a troca de senha.
  useEffect(() => {
    if (isAuthenticated && new URLSearchParams(window.location.search).has('redefinir')) {
      logout();
    }
  }, []);

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
      apiFetch('/perfil-clinico')
        .then((data) => {
          if (data) {
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

  // Área da equipe (aprovação de profissionais). O acesso é pelo token da equipe, não pelo login.
  if (currentPath === '/equipe') {
    return (
      <div className="app-container">
        <EquipeAdmin onExit={() => navigate('/')} />
      </div>
    );
  }

  // Rotas Públicas Legais (Acessíveis autenticado ou anônimo)
  if (currentPath === '/politica-privacidade' || currentPath === '/termos' || currentPath === '/termos-de-uso') {
    return (
      <div className="app-container" style={{ padding: '24px', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <PWAInstallPrompt />
        <LegalModal
          isOpen={true}
          onClose={() => navigate(isAuthenticated ? '/' : '/login')}
          initialTab={currentPath === '/politica-privacidade' ? 'politica' : 'termos'}
        />
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', flexShrink: 0 }} onClick={() => navigate('/')}>
          <LotusLogo size={26} color="#FFFFFF" />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1 style={{ color: '#FFFFFF', margin: 0, fontSize: '1.18rem', fontWeight: 800, lineHeight: 1.1 }}>Nymphia</h1>
            <span className="header-slogan" style={{ color: '#FDF0F2', opacity: 0.92, fontSize: '0.68rem', whiteSpace: 'nowrap' }}>
              {lang === 'en' ? 'Every heartbeat matters.' : 'Cada batimento importa.'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
          <button
            onClick={() => setLang(lang === 'pt' ? 'en' : 'pt')}
            style={{
              background: 'rgba(255,255,255,0.22)',
              border: '1px solid rgba(255,255,255,0.4)',
              color: '#FFFFFF',
              padding: '3px 8px',
              borderRadius: '9999px',
              fontSize: '0.72rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
            title={lang === 'pt' ? 'Switch to English' : 'Mudar para Português'}
            aria-label="Alternar idioma / Toggle Language"
          >
            <Globe size={13} />
            <span>{lang.toUpperCase()}</span>
          </button>

          <span
            style={{
              fontSize: '0.72rem',
              backgroundColor: 'rgba(255,255,255,0.2)',
              padding: '3px 8px',
              borderRadius: '9999px',
              textTransform: 'capitalize',
              whiteSpace: 'nowrap',
              flexShrink: 0
            }}
          >
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
              width: '34px',
              height: '34px',
              minWidth: '34px',
              minHeight: '34px',
              aspectRatio: '1 / 1',
              borderRadius: '50%',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              padding: 0
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
                {currentPath === '/bem-estar-emocional' && <BemEstarEmocional onBack={() => navigate('/')} />}
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
            <span>{t('nav_dashboard', 'Início')}</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/checkin' ? 'active' : ''}`}
            onClick={() => navigate('/checkin')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Activity size={20} />
            <span>{t('nav_checkin', 'Check-in')}</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/conversa' ? 'active' : ''}`}
            onClick={() => navigate('/conversa')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <MessageSquare size={20} />
            <span>{t('nav_chat_ia', 'Chat IA')}</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/agenda' ? 'active' : ''}`}
            onClick={() => navigate('/agenda')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Calendar size={20} />
            <span>{t('nav_agenda', 'Agenda')}</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/meus-dados' ? 'active' : ''}`}
            onClick={() => navigate('/meus-dados')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Shield size={20} />
            <span>{t('nav_meus_dados', 'LGPD')}</span>
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
            <span>{t('nav_dashboard', 'Início')}</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/checkin' ? 'active' : ''}`}
            onClick={() => navigate('/checkin')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Activity size={20} />
            <span>{t('nav_checkin', 'Check-in')}</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/agenda' ? 'active' : ''}`}
            onClick={() => navigate('/agenda')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Calendar size={20} />
            <span>{t('nav_agenda', 'Agenda')}</span>
          </button>
          <button
            className={`nav-item ${currentPath === '/quiz-gostos' ? 'active' : ''}`}
            onClick={() => navigate('/quiz-gostos')}
            style={{ background: 'transparent', border: 'none' }}
          >
            <Heart size={20} />
            <span>{lang === 'en' ? 'Gifts' : 'Mimos'}</span>
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
