import React, { createContext, useContext, useState, useEffect } from 'react';

const translations = {
  pt: {
    // Top Bar & Branding
    app_title: 'Nymphia',
    app_subtitle: 'Cuidado Pré-Natal Inteligente & Seguro',
    emergency_button: 'EMERGÊNCIA (192)',
    emergency_title: 'Canal de Emergência Obstétrica',
    emergency_desc: 'Disque 192 (SAMU) imediatamente em caso de convulsão, sangramento grave ou perda de consciência.',
    
    // Navigation
    nav_dashboard: 'Início',
    nav_checkin: 'Check-in Diário',
    nav_agenda: 'Agenda & Consultas',
    nav_exames: 'Exames & Laudos',
    nav_chat_ia: 'Assistente IA',
    nav_painel_medico: 'Painel do Profissional',
    nav_comunidade: 'Comunidade',
    nav_planos: 'Planos & Assinatura',
    nav_meus_dados: 'Privacidade LGPD',
    nav_logout: 'Sair',
    nav_login: 'Entrar',
    
    // Status & Clinical
    status_active: 'Ativa',
    status_pending: 'Pendente',
    status_alert: 'Alerta Clínico',
    status_normal: 'Normal',
    vital_bp: 'Pressão Arterial',
    vital_glucose: 'Glicemia',
    vital_fetal_mov: 'Movimentação Fetal',
    
    // Actions & Buttons
    btn_save: 'Salvar',
    btn_cancel: 'Cancelar',
    btn_confirm: 'Confirmar',
    btn_export_data: 'Exportar Meus Dados (LGPD)',
    btn_subscribe: 'Assinar Plano',
    
    // Legal & Footer
    footer_text: 'Nymphia Saúde da Mulher — Em conformidade com LGPD e CFM 2.454/2026. A rota de emergência é sempre gratuita.',
    lang_selector: 'Idioma'
  },
  en: {
    // Top Bar & Branding
    app_title: 'Nymphia',
    app_subtitle: 'Intelligent & Safe Prenatal Care',
    emergency_button: 'EMERGENCY (911 / 192)',
    emergency_title: 'Obstetric Emergency Channel',
    emergency_desc: 'Call emergency services immediately in case of seizures, severe bleeding, or loss of consciousness.',
    
    // Navigation
    nav_dashboard: 'Dashboard',
    nav_checkin: 'Daily Check-in',
    nav_agenda: 'Appointments & Calendar',
    nav_exames: 'Lab & Ultrasound Exams',
    nav_chat_ia: 'AI Clinical Assistant',
    nav_painel_medico: 'Doctor Portal',
    nav_comunidade: 'Community',
    nav_planos: 'Plans & Subscription',
    nav_meus_dados: 'LGPD Privacy Rights',
    nav_logout: 'Log Out',
    nav_login: 'Log In',
    
    // Status & Clinical
    status_active: 'Active',
    status_pending: 'Pending',
    status_alert: 'Clinical Alert',
    status_normal: 'Normal',
    vital_bp: 'Blood Pressure',
    vital_glucose: 'Blood Glucose',
    vital_fetal_mov: 'Fetal Movements',
    
    // Actions & Buttons
    btn_save: 'Save',
    btn_cancel: 'Cancel',
    btn_confirm: 'Confirm',
    btn_export_data: 'Export My Data (GDPR/LGPD)',
    btn_subscribe: 'Subscribe Plan',
    
    // Legal & Footer
    footer_text: 'Nymphia Maternal Health — Compliant with LGPD, GDPR and medical safety standards. Emergency routes are always free of charge.',
    lang_selector: 'Language'
  }
};

const I18nContext = createContext(null);

export const I18nProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem('nymphia_lang') || 'pt';
  });

  const changeLanguage = (newLang) => {
    if (translations[newLang]) {
      setLang(newLang);
      localStorage.setItem('nymphia_lang', newLang);
    }
  };

  const t = (key, fallback = '') => {
    const dict = translations[lang] || translations.pt;
    return dict[key] || fallback || key;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang: changeLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    return {
      lang: 'pt',
      setLang: () => {},
      t: (k, fb) => fb || k
    };
  }
  return context;
};
