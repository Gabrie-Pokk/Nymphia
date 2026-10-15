"""
Triagem emocional com a Escala de Depressão Pós-Parto de Edimburgo (EPDS).

A EPDS (Cox, Holden e Sagovsky, Br J Psychiatry 1987) tem 10 perguntas sobre
os últimos 7 dias, cada uma com 4 respostas que valem de 0 a 3 pontos (total
de 0 a 30). Ela é usada na gestação e no pós-parto. No Brasil foi validada por
Santos IS et al. (Cad Saúde Pública 2007;23(11):2577-88): para triagem, o
melhor ponto de corte foi 10 ou mais (sensibilidade 82,6%, especificidade
65,4%). Triagem não é diagnóstico: o resultado positivo pede conversa com a
equipe.

O TEXTO DAS PERGUNTAS NÃO FICA NO CÓDIGO. Os direitos da escala são do Royal
College of Psychiatrists; reproduzir em software distribuído pede autorização
por escrito. O texto validado entra por um arquivo JSON fornecido pela equipe
(modelo em app/data/epds_ptbr.exemplo.json), por um destes caminhos, em ordem:
  1. variável NYMPHIA_EPDS_JSON com o conteúdo do arquivo;
  2. variável NYMPHIA_EPDS_ARQUIVO com o caminho do arquivo;
  3. app/data/epds_ptbr.json.
Sem o arquivo, a triagem fica desligada e o app não mostra a opção.
O repositório é público: o texto preenchido NÃO vai para o Git (o .gitignore
ignora app/data/epds_ptbr.json); em produção ele entra pela variável.

Pontuação: nas perguntas 1, 2 e 4 a primeira resposta vale 0 e a última vale 3;
nas perguntas 3 e 5 a 10 a ordem é invertida (a primeira vale 3). O arquivo
traz os pontos de cada resposta e o servidor confere com essa chave antes de
ligar a triagem, para que uma troca na ordem das respostas não mude a nota.

Pergunta 10 (pensamento de se machucar): qualquer resposta diferente de
"nunca" (pontos > 0) dispara a orientação de segurança na hora (CVV 188,
SAMU 192), qualquer que seja o total.
"""
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nymphia.epds")

ARQUIVO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "epds_ptbr.json"

TOTAL_ITENS = 10
OPCOES_POR_ITEM = 4
ITEM_AUTOLESAO = 10
CORTE_TRIAGEM = 10  # Santos et al., 2007: 10 ou mais

# Pontos de cada resposta, na ordem em que aparecem (Cox et al., 1987)
_DIRETA = (0, 1, 2, 3)
_INVERTIDA = (3, 2, 1, 0)
CHAVE_PONTUACAO: Dict[int, Tuple[int, ...]] = {
    numero: (_DIRETA if numero in (1, 2, 4) else _INVERTIDA) for numero in range(1, TOTAL_ITENS + 1)
}

REFERENCIA = (
    "Escala de Depressão Pós-Parto de Edimburgo (Cox, Holden e Sagovsky, 1987); validação brasileira de "
    "Santos et al., Cad Saúde Pública 2007, com ponto de corte 10 ou mais para triagem"
)

AVISO = (
    "Este questionário é uma triagem, não um diagnóstico. Quem avalia o resultado é a sua equipe de saúde."
)

MENSAGENS = {
    "urgente": {
        "titulo": "Você não está sozinha",
        "texto": (
            "Você contou que pensou em se machucar. Isso merece cuidado agora. Ligue para o CVV no 188 "
            "(gratuito, 24 horas) para conversar, ou para o SAMU no 192 se estiver em perigo. Se puder, "
            "peça para alguém de confiança ficar com você e conte para sua equipe de pré-natal."
        ),
    },
    "atencao": {
        "titulo": "Vale conversar com sua equipe",
        "texto": (
            "Suas respostas mostram sinais que pedem uma conversa com a equipe de pré-natal sobre como você "
            "tem se sentido. Isso não é diagnóstico, e tem cuidado e tratamento. Se quiser conversar com "
            "alguém agora, o CVV atende no 188, de graça, 24 horas."
        ),
    },
    "sem_sinais": {
        "titulo": "Nada que peça atenção agora",
        "texto": (
            "Suas respostas não mostram sinais que peçam atenção neste momento. Se o jeito como você se sente "
            "mudar, você pode responder de novo ou falar com sua equipe a qualquer hora."
        ),
    },
}


class QuestionarioIndisponivel(Exception):
    pass


def _ler_conteudo() -> Tuple[Optional[str], str]:
    """Devolve (texto JSON, origem). Texto None quando não há fonte configurada."""
    conteudo = os.getenv("NYMPHIA_EPDS_JSON")
    if conteudo and conteudo.strip():
        return conteudo, "variável NYMPHIA_EPDS_JSON"
    caminho = Path(os.getenv("NYMPHIA_EPDS_ARQUIVO") or ARQUIVO_PADRAO)
    if caminho.is_file():
        return caminho.read_text(encoding="utf-8"), str(caminho)
    return None, str(caminho)


def _validar(dados: Any) -> Dict[str, Any]:
    if not isinstance(dados, dict):
        raise QuestionarioIndisponivel("o arquivo precisa ser um objeto JSON")
    if not str(dados.get("licenca") or "").strip():
        raise QuestionarioIndisponivel("falta o campo 'licenca' (autorização de uso do texto)")
    itens = dados.get("itens")
    if not isinstance(itens, list) or len(itens) != TOTAL_ITENS:
        raise QuestionarioIndisponivel(f"o arquivo precisa ter exatamente {TOTAL_ITENS} perguntas")

    validados = []
    for posicao, item in enumerate(itens, start=1):
        if not isinstance(item, dict) or item.get("numero") != posicao:
            raise QuestionarioIndisponivel(f"a pergunta na posição {posicao} precisa ter numero = {posicao}")
        texto = str(item.get("texto") or "").strip()
        opcoes = item.get("opcoes")
        if not texto or not isinstance(opcoes, list) or len(opcoes) != OPCOES_POR_ITEM:
            raise QuestionarioIndisponivel(f"a pergunta {posicao} precisa de texto e de {OPCOES_POR_ITEM} respostas")
        textos_opcoes, pontos = [], []
        for opcao in opcoes:
            if not isinstance(opcao, dict) or not str(opcao.get("texto") or "").strip():
                raise QuestionarioIndisponivel(f"há resposta sem texto na pergunta {posicao}")
            textos_opcoes.append(str(opcao["texto"]).strip())
            pontos.append(opcao.get("pontos"))
        if tuple(pontos) != CHAVE_PONTUACAO[posicao]:
            raise QuestionarioIndisponivel(
                f"os pontos da pergunta {posicao} ({pontos}) não batem com a chave da escala "
                f"({list(CHAVE_PONTUACAO[posicao])}); confira a ordem das respostas"
            )
        validados.append({"numero": posicao, "texto": texto, "opcoes": textos_opcoes})

    return {
        "versao": str(dados.get("versao") or "EPDS").strip(),
        "licenca": str(dados["licenca"]).strip(),
        "instrucao": str(dados.get("instrucao") or "").strip(),
        "itens": validados,
    }


@lru_cache(maxsize=1)
def _carregar() -> Tuple[Optional[Dict[str, Any]], str]:
    conteudo, origem = _ler_conteudo()
    if conteudo is None:
        return None, "o texto validado da escala ainda não foi fornecido pela equipe"
    try:
        return _validar(json.loads(conteudo)), ""
    except json.JSONDecodeError as erro:
        motivo = f"o arquivo da escala não é um JSON válido ({erro.msg}, linha {erro.lineno})"
    except QuestionarioIndisponivel as erro:
        motivo = f"arquivo da escala recusado: {erro}"
    logger.error("[EPDS] Triagem desligada (%s): %s", origem, motivo)
    return None, motivo


def recarregar() -> None:
    """Esquece o questionário em memória (usado nos testes e depois de trocar o arquivo)."""
    _carregar.cache_clear()


def questionario() -> Tuple[Optional[Dict[str, Any]], str]:
    """(questionário validado ou None, motivo quando indisponível)."""
    return _carregar()


def disponivel() -> bool:
    return questionario()[0] is not None


def classificar(pontuacao: int, pontos_autolesao: int) -> str:
    if pontos_autolesao > 0:
        return "urgente"
    if pontuacao >= CORTE_TRIAGEM:
        return "atencao"
    return "sem_sinais"


def pontuar(respostas: List[int]) -> Dict[str, Any]:
    """
    respostas: posição da resposta escolhida em cada pergunta (0 = primeira), na ordem 1 a 10.
    Os pontos vêm da chave da escala, nunca do cliente.
    """
    if len(respostas) != TOTAL_ITENS:
        raise ValueError(f"são {TOTAL_ITENS} respostas")
    pontos = []
    for numero, escolha in enumerate(respostas, start=1):
        if not isinstance(escolha, int) or not 0 <= escolha < OPCOES_POR_ITEM:
            raise ValueError(f"resposta inválida na pergunta {numero}")
        pontos.append(CHAVE_PONTUACAO[numero][escolha])
    total = sum(pontos)
    autolesao = pontos[ITEM_AUTOLESAO - 1]
    nivel = classificar(total, autolesao)
    return {
        "pontos_por_item": pontos,
        "pontuacao": total,
        "pontos_autolesao": autolesao,
        "nivel": nivel,
        "titulo": MENSAGENS[nivel]["titulo"],
        "mensagem": MENSAGENS[nivel]["texto"],
    }
