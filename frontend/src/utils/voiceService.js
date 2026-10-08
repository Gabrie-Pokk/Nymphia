/**
 * NYMPHIA VOICE ENGINE (Síntese de Voz Humana e Fluente em Português)
 * Gerencia preferências de voz, personas auditivas, pronúncia obstétrica
 * e sintetização fluente com a Web Speech API.
 */

const STORAGE_KEY = 'nymphia_voice_preferences';

export const PERSONAS_VOZ = {
  carinhosa: {
    id: 'carinhosa',
    nome: 'Carinhosa & Acolhedora',
    descricao: 'Tom afetuoso, suave e doce. Ideal para o dia a dia e acolhimento emocional.',
    pitch: 1.10,
    rate: 0.95
  },
  calma: {
    id: 'calma',
    nome: 'Tranquila & Serena',
    descricao: 'Ritmo pausado e relaxante. Perfeito para respiração e alívio de ansiedade.',
    pitch: 0.98,
    rate: 0.88
  },
  encorajadora: {
    id: 'encorajadora',
    nome: 'Encorajadora & Positiva',
    descricao: 'Tom animador e confiante. Ótimo para exercícios e momentos de disposição.',
    pitch: 1.05,
    rate: 1.05
  },
  custom: {
    id: 'custom',
    nome: 'Personalizada',
    descricao: 'Ajuste manual de tom, velocidade e timbre de voz.',
    pitch: 1.0,
    rate: 1.0
  }
};

const DEFAULT_PREFERENCES = {
  voiceURI: null,
  persona: 'carinhosa',
  pitch: 1.10,
  rate: 0.95,
  volume: 1.0,
  autoFalarChat: false
};

export const getVoicePreferences = () => {
  try {
    const salvo = localStorage.getItem(STORAGE_KEY);
    if (salvo) {
      return { ...DEFAULT_PREFERENCES, ...JSON.parse(salvo) };
    }
  } catch (e) {}
  return { ...DEFAULT_PREFERENCES };
};

export const saveVoicePreferences = (prefs) => {
  try {
    const atual = getVoicePreferences();
    const novo = { ...atual, ...prefs };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(novo));
    return novo;
  } catch (e) {
    return prefs;
  }
};

/**
 * Retorna o emoji da bandeira do país correspondente à voz,
 * corrigindo com precisão Bodo (Índia), Português (Brasil), Português (Portugal), etc.
 */
export const getVoiceFlag = (voice) => {
  if (!voice) return '🌐';
  const lang = (voice.lang || '').toLowerCase().replace(/_/g, '-');
  const name = (voice.name || '').toLowerCase();

  // Bodo da Índia (ISO brx / brx-IN ou menção explícita a Índia/India)
  if (
    lang.startsWith('brx') ||
    name.includes('bodo') ||
    name.includes('índia') ||
    name.includes('india') ||
    lang.endsWith('-in') ||
    lang === 'hi' ||
    lang.startsWith('hi-')
  ) {
    return '🇮🇳';
  }

  // Português do Brasil
  if (
    lang === 'pt-br' ||
    lang.endsWith('-br') ||
    name.includes('brasil') ||
    name.includes('brazil')
  ) {
    return '🇧🇷';
  }

  // Português de Portugal
  if (
    lang === 'pt-pt' ||
    lang.startsWith('pt') ||
    name.includes('portugal')
  ) {
    return '🇵🇹';
  }

  // Outros idiomas comuns
  if (lang.includes('us') || name.includes('united states')) return '🇺🇸';
  if (lang.includes('gb') || lang.includes('uk')) return '🇬🇧';
  if (lang.startsWith('es') || name.includes('español')) return '🇪🇸';
  if (lang.startsWith('fr') || name.includes('français')) return '🇫🇷';
  if (lang.startsWith('it') || name.includes('italiano')) return '🇮🇹';
  if (lang.startsWith('de') || name.includes('deutsch')) return '🇩🇪';

  // Fallback para código de país ISO 3166-1 de 2 letras se presente (ex: en-US, pt-AO -> AO)
  const parts = lang.split('-');
  if (parts.length >= 2 && parts[1].length === 2) {
    const country = parts[1].toUpperCase();
    return String.fromCodePoint(...country.split('').map((c) => 127397 + c.charCodeAt(0)));
  }

  return '🌐';
};

/**
 * Formata o nome da voz com iniciais em maiúsculas (Title Case).
 * Exemplos: "bodo Índia" -> "Bodo Índia", "português Brasil" -> "Português Brasil"
 */
export const formatVoiceName = (rawName) => {
  if (!rawName) return 'Voz do Sistema';

  return rawName
    .split(/\s+/)
    .map((word) => {
      if (!word) return '';
      // Preserva siglas já maiúsculas como "BR", "PT", "TTS"
      if (word.length <= 3 && word.toUpperCase() === word && !/^[a-z]/i.test(word)) return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
};

/**
 * Obtém a lista de vozes disponíveis no navegador,
 * formatando letras maiúsculas, bandeiras corretas e ordenando alfabeticamente (A-Z).
 */
export const getAvailablePortugueseVoices = () => {
  if (!('speechSynthesis' in window)) return [];
  const allVoices = window.speechSynthesis.getVoices() || [];

  // Filtra vozes em português ou compatíveis no dispositivo
  const ptVoices = allVoices.filter(
    (v) => v.lang && (v.lang.toLowerCase().startsWith('pt') || v.lang.toLowerCase().includes('br'))
  );

  // Mapeia e enriquece com nome formatado e bandeira
  const enriched = ptVoices.map((v) => {
    const displayName = formatVoiceName(v.name);
    const flag = getVoiceFlag(v);
    const label = `${displayName} ${flag}`;
    return {
      ...v,
      voiceURI: v.voiceURI,
      name: v.name,
      lang: v.lang,
      displayName,
      flag,
      label
    };
  });

  // Ordena estritamente por ordem alfabética (A-Z) com suporte ao português brasileiro
  enriched.sort((a, b) =>
    a.label.localeCompare(b.label, 'pt-BR', { sensitivity: 'base' })
  );

  return enriched;
};

/**
 * Normaliza e higieniza textos para fala, expandindo siglas obstétricas
 * e removendo formatações markdown e caracteres especiais para fala fluente.
 */
export const sanitizarTextoParaFala = (texto) => {
  if (!texto) return '';

  let t = texto;

  // Remove blocos de código ou tags
  t = t.replace(/```[\s\S]*?```/g, '');
  t = t.replace(/`([^`]+)`/g, '$1');

  // Remove links markdown [texto](url) -> texto
  t = t.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');

  // Remove caracteres markdown (#, *, _, ~, >, •)
  t = t.replace(/[*#_~>•]/g, ' ');

  // Remove separadores horizontais
  t = t.replace(/---+/g, ' ');

  // Remove emojis para não gerar ruídos na síntese
  t = t.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F018}-\u{1F270}]/gu, '');

  // Dicionário de Fonética Obstétrica & Médica (Português Fluente)
  const substituicoesFoneticas = [
    [/\bFEBRASGO\b/gi, 'Febrásgo'],
    [/\bCFM\b/gi, 'Cê Éfe Eme'],
    [/\bOMS\b/gi, 'Organização Mundial da Saúde'],
    [/\bSAMU\b/gi, 'Sámu'],
    [/\b192\b/g, 'cento e noventa e dois'],
    [/\b190\b/g, 'cento e noventa'],
    [/\bDPP\b/gi, 'data provável do parto'],
    [/\bDUM\b/gi, 'data da última menstruação'],
    [/\bCCN\b/gi, 'comprimento cabeça nádega'],
    [/\bDBP\b/gi, 'diâmetro bi parietal'],
    [/\bBPM\b/gi, 'batimentos por minuto'],
    [/\breps\b/gi, 'repetições'],
    [/\brep\b/gi, 'repetição'],
    [/\bcm\b/gi, 'centímetros'],
    [/\bkg\b/gi, 'quilos'],
    [/\bmg\b/gi, 'miligramas'],
    [/\bml\b/gi, 'mililitros'],
    [/\bdTpa\b/gi, 'dê tê pê a'],
    [/\bTOTG\b/gi, 'teste oral de tolerância à glicose'],
    [/\bIgG\b/gi, 'I G G'],
    [/\bIgM\b/gi, 'I G M'],
    [/\bRN\b/gi, 'recém-nascido'],
    [/\b(Braxton Hicks|Braxton-Hicks)\b/gi, 'Brácston Rícks'],
    [/\b(\d+)x(\d+)\b/g, '$1 por $2'], // 140x90 -> 140 por 90
    [/\bmmHg\b/gi, 'milímetros de mercúrio'],
    [/\bºC\b/gi, 'graus celsius'],
    [/\b°C\b/gi, 'graus celsius'],
    [/\b1ª\b/g, 'primeira'],
    [/\b2ª\b/g, 'segunda'],
    [/\b3ª\b/g, 'terceira']
  ];

  substituicoesFoneticas.forEach(([regex, substituto]) => {
    t = t.replace(regex, substituto);
  });

  // Limpa espaços duplicados e quebras excessivas
  t = t.replace(/\s+/g, ' ').trim();

  return t;
};

/**
 * Fala o texto utilizando as preferências salvas da Nymphia
 */
export const speakNymphia = (
  texto,
  options = {}
) => {
  if (!('speechSynthesis' in window)) {
    if (options.onError) options.onError('Síntese de voz não suportada neste navegador.');
    return;
  }

  // Cancela falas anteriores
  window.speechSynthesis.cancel();

  const textoLimpo = sanitizarTextoParaFala(texto);
  if (!textoLimpo) return;

  const prefs = getVoicePreferences();
  const utterance = new SpeechSynthesisUtterance(textoLimpo);

  // Aplica velocidade e tom baseados nas preferências ou persona
  utterance.pitch = options.pitch !== undefined ? options.pitch : prefs.pitch;
  utterance.rate = options.rate !== undefined ? options.rate : prefs.rate;
  utterance.volume = options.volume !== undefined ? options.volume : prefs.volume;
  utterance.lang = 'pt-BR';

  // Localiza e seleciona a melhor voz em português
  const vozesPt = getAvailablePortugueseVoices();
  if (vozesPt.length > 0) {
    if (prefs.voiceURI) {
      const vozEscolhida = vozesPt.find((v) => v.voiceURI === prefs.voiceURI);
      if (vozEscolhida) utterance.voice = vozEscolhida;
      else utterance.voice = vozesPt[0];
    } else {
      utterance.voice = vozesPt[0];
    }
  }

  if (options.onStart) utterance.onstart = options.onStart;
  if (options.onEnd) utterance.onend = options.onEnd;
  if (options.onError) utterance.onerror = options.onError;

  window.speechSynthesis.speak(utterance);
};

export const stopNymphiaVoice = () => {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};

export const isNymphiaSpeaking = () => {
  if ('speechSynthesis' in window) {
    return window.speechSynthesis.speaking;
  }
  return false;
};
