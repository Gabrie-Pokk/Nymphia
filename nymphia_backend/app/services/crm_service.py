"""
Nymphia -- Conferência de registro profissional (CRM e COREN).

Regra deste módulo: nenhuma resposta afirma que um registro foi conferido no
Conselho quando não foi. A aprovação de todo profissional é MANUAL, feita pela
equipe Nymphia depois de olhar o documento enviado e o portal do CFM. Quando
a empresa tiver CNPJ, a consulta automática deve passar a usar o webservice
oficial do CFM (Resolução CFM 2.309/2022).

A consulta ao CREMESP (só para SP) é uma ajuda: preenche o nome e bloqueia
registros que o próprio CREMESP mostra como inativos. Ela nunca aprova ninguém.
Falha de rede, erro 5xx ou resposta inesperada viram "verificação manual
pendente", e nada disso é guardado em cache.

Situações possíveis da resposta:
  FORMATO_INVALIDO              número ou UF impossíveis
  ENCONTRADO_NO_CREMESP         SP, ativo no CREMESP; aprovação continua manual
  INATIVO_NO_CREMESP            SP, o CREMESP mostra o registro como inativo
  VERIFICACAO_MANUAL_PENDENTE   todos os outros casos
"""
import re
import json
import ssl
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger("nymphia.crm")

UFS_BRASIL = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
}

SEQUENCIAS_FICTICIAS = {"0000", "00000", "000000", "0000000", "111111", "1234567890"}

# Cache só de respostas conclusivas do CREMESP (ativo ou inativo).
_CACHE_CREMESP: Dict[str, Dict[str, Any]] = {}

MSG_MANUAL = (
    "Formato do registro conferido. A confirmação no Conselho é feita manualmente "
    "pela equipe Nymphia, a partir do documento enviado. Até lá, o acesso a pacientes fica bloqueado."
)


def normalizar_registro(numero: str) -> str:
    """Guarda só os dígitos do registro (ex.: '123.456-A' vira '123456')."""
    return re.sub(r"[^0-9]", "", str(numero or "").strip())


def validar_formato_crm(crm: str, uf: str) -> tuple[bool, str]:
    crm_limpo = normalizar_registro(crm)
    uf_limpa = str(uf or "").strip().upper()

    if not crm_limpo:
        return False, "Número de registro não informado."
    if uf_limpa not in UFS_BRASIL:
        return False, f"UF '{uf_limpa}' inválida. Informe um estado brasileiro válido (ex.: SP, RJ, MG)."
    if len(crm_limpo) < 3 or len(crm_limpo) > 10:
        return False, "O número do registro deve ter entre 3 e 10 dígitos."
    if crm_limpo in SEQUENCIAS_FICTICIAS:
        return False, "Número de registro com sequência inválida."
    return True, "Formato aceito."


def _consultar_cremesp(crm_limpo: str) -> Optional[Dict[str, Any]]:
    """
    Consulta o guia médico do CREMESP. Devolve um resultado só quando a resposta
    é conclusiva (200 com situação). Qualquer outra coisa devolve None.
    A verificação de certificado TLS fica LIGADA.
    """
    if crm_limpo in _CACHE_CREMESP:
        return _CACHE_CREMESP[crm_limpo]

    url = f"https://api.cremesp.org.br/guia-medico/medico-info/{crm_limpo}"
    requisicao = urllib.request.Request(
        url,
        headers={"User-Agent": "NymphiaSaude/2.0", "Accept": "application/json"},
    )
    try:
        contexto = ssl.create_default_context()
        with urllib.request.urlopen(requisicao, context=contexto, timeout=3.5) as resposta:
            if resposta.status != 200:
                return None
            dados = json.loads(resposta.read().decode("utf-8", errors="replace"))
    except Exception as erro:
        logger.info("CREMESP sem resposta conclusiva para %s: %s", crm_limpo, erro)
        return None

    nome = (dados.get("nome") or "").strip() or None
    codigo = (dados.get("situacao") or "").strip().upper()
    especialidades = [e.get("descricao") for e in (dados.get("especialidades") or []) if e and e.get("descricao")]
    especialidade = ", ".join(especialidades) if especialidades else None

    if codigo == "A":
        resultado = {
            "valido": True,
            "situacao": "ENCONTRADO_NO_CREMESP",
            "nome_medico": nome,
            "especialidade": especialidade,
            "mensagem": (
                f"Registro encontrado como ativo no CREMESP{': ' + nome if nome else ''}. "
                "A aprovação na Nymphia continua manual, a partir do documento enviado."
            ),
        }
    elif codigo:
        resultado = {
            "valido": False,
            "situacao": "INATIVO_NO_CREMESP",
            "nome_medico": nome,
            "especialidade": especialidade,
            "mensagem": (
                "O CREMESP mostra este registro como inativo ou com restrição. "
                "Se isso estiver errado, fale com o suporte da Nymphia."
            ),
        }
    else:
        return None

    _CACHE_CREMESP[crm_limpo] = resultado
    return resultado


def consultar_situacao_crm(crm: str, uf: str, db=None, registro_tipo: str = "CRM") -> Dict[str, Any]:
    """
    Responde só o que dá para afirmar. O parâmetro db é mantido por
    compatibilidade e não é usado: existir no banco da Nymphia não é prova de
    registro no Conselho.
    """
    crm_limpo = normalizar_registro(crm)
    uf_limpa = str(uf or "").strip().upper()
    tipo = (registro_tipo or "CRM").strip().upper()

    base = {
        "crm": crm_limpo,
        "uf": uf_limpa,
        "nome_medico": None,
        "conselho": f"{tipo}-{uf_limpa}" if uf_limpa else tipo,
        "especialidade": None,
    }

    valido_formato, motivo = validar_formato_crm(crm_limpo, uf_limpa)
    if not valido_formato:
        return {**base, "valido": False, "situacao": "FORMATO_INVALIDO", "mensagem": motivo}

    if tipo == "CRM" and uf_limpa == "SP":
        resultado = _consultar_cremesp(crm_limpo)
        if resultado is not None:
            return {**base, **resultado}

    return {**base, "valido": True, "situacao": "VERIFICACAO_MANUAL_PENDENTE", "mensagem": MSG_MANUAL}
