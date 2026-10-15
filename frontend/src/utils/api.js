/**
 * Utilitário central de requisições HTTP seguras para o Nymphia.
 * Trata timeouts, quedas de conexão, cold-start de nuvem (Render) e expiração de JWT (401).
 */

const DEFAULT_TIMEOUT_MS = 15000;

const NOMES_DE_CAMPOS = {
  nome: 'Nome',
  email: 'E-mail',
  senha: 'Senha',
  nova_senha: 'Nova senha',
  registro_numero: 'Número do registro',
  registro_uf: 'UF do registro',
  registro_tipo: 'Tipo de registro',
  crm: 'CRM',
  crm_uf: 'UF do CRM',
  aceite_termos: 'Termos de uso',
  consentimento_dados_saude: 'Consentimento de dados de saúde',
  token: 'Código do e-mail'
};

/**
 * O FastAPI devolve erros de validação (422) como uma LISTA de objetos.
 * Antes, essa lista virava "[object Object]" na tela. Aqui ela vira texto.
 */
export function formatarDetalheErro(detail) {
  if (!detail) return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const partes = detail.map((item) => {
      if (!item || typeof item !== 'object') return String(item);
      const msg = String(item.msg || '').replace(/^Value error,\s*/i, '');
      const loc = Array.isArray(item.loc) ? item.loc.filter((x) => x !== 'body') : [];
      const campo = loc.length ? (NOMES_DE_CAMPOS[loc[loc.length - 1]] || loc[loc.length - 1]) : '';
      return campo && !msg.toLowerCase().includes(String(campo).toLowerCase()) ? `${campo}: ${msg}` : msg;
    });
    return [...new Set(partes.filter(Boolean))].join(' ');
  }
  if (typeof detail === 'object') return detail.msg || detail.mensagem || JSON.stringify(detail);
  return String(detail);
}

export async function apiFetch(endpoint, options = {}) {
  const {
    timeout = DEFAULT_TIMEOUT_MS,
    headers = {},
    skipAuth = false,
    ...restOptions
  } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // Anexa token JWT se disponível e não explicitamente desativado
  const finalHeaders = { ...headers };
  if (!skipAuth) {
    const token = localStorage.getItem('nymphia_token');
    if (
      token &&
      token !== 'undefined' &&
      token !== 'null' &&
      typeof token === 'string' &&
      token.trim().length > 10 &&
      !finalHeaders['Authorization']
    ) {
      finalHeaders['Authorization'] = `Bearer ${token.trim()}`;
    }
  }

  try {
    const response = await fetch(endpoint, {
      ...restOptions,
      headers: finalHeaders,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    // Tratamento para Sessão Expirada ou Token Inválido (401)
    if (response.status === 401) {
      // Dispara evento global para que AuthContext possa deslogar de forma graciosa
      window.dispatchEvent(
        new CustomEvent('nymphia:auth-expired', {
          detail: { endpoint, status: 401 }
        })
      );
    }

    // Leitura segura à prova de falhas do corpo da resposta
    // Lê via text() primeiro para NUNCA lançar "Failed to execute 'json' on 'Response': Unexpected end of JSON input"
    let data = null;
    let rawText = '';

    try {
      rawText = await response.text();
      if (rawText && rawText.trim().length > 0) {
        try {
          data = JSON.parse(rawText);
        } catch {
          data = null;
        }
      }
    } catch {
      data = null;
    }

    if (!response.ok) {
      let errorMessage = 'Ocorreu um erro no processamento da solicitação.';

      if (data && typeof data === 'object' && (data.detail || data.erro || data.message)) {
        errorMessage = formatarDetalheErro(data.detail) || data.erro || data.message || errorMessage;
      } else if (response.status === 503) {
        errorMessage = 'O servidor da Nymphia está ligando ou em manutenção. Tente de novo em alguns segundos.';
      } else if (response.status === 401) {
        errorMessage = 'Sua sessão expirou ou suas credenciais são inválidas.';
      } else if (response.status === 403) {
        errorMessage = 'Você não possui permissão para acessar este recurso.';
      } else if (response.status === 404) {
        errorMessage = 'Recurso não encontrado no servidor.';
      } else if (response.status >= 500) {
        errorMessage = 'O servidor seguro está temporariamente ocupado ou inicializando. Tente em alguns instantes.';
      }

      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      error.rawText = rawText;
      throw error;
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);

    if (err.name === 'AbortError') {
      const timeoutError = new Error(
        'Tempo limite esgotado. O servidor pode estar inicializando após inatividade. Por favor, tente novamente.'
      );
      timeoutError.isTimeout = true;
      throw timeoutError;
    }

    // Se for TypeError (ex: NetworkError, Failed to fetch)
    if (err instanceof TypeError && err.message.includes('fetch')) {
      const networkError = new Error(
        'Não foi possível conectar ao servidor da Nymphia. Verifique sua conexão com a internet ou aguarde alguns segundos se o servidor estiver despertando.'
      );
      networkError.isNetworkError = true;
      throw networkError;
    }

    throw err;
  }
}
