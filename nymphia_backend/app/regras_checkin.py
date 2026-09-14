"""
Nymphia -- Sistema de regras para o check-in emocional
Funciona hoje, sem nenhum treino de IA. Serve de base ate o BERTimbau
estar pronto, e continua rodando em paralelo depois como camada de
seguranca (se o modelo falhar ou tiver baixa confianca).

Taxonomia baseada em fatores de risco citados na literatura sobre saude
mental gestacional (ansiedade, tristeza/desanimo, estresse, medo/inseguranca).
"""
import re

PALAVRAS_CHAVE = {
    "ansiedade": [
        "ansiosa", "ansiedade", "nervosa", "aflita", "angustiada",
        "coração acelerado", "não consigo parar de pensar", "preocupada",
        "preocupação", "sem sossego", "inquieta",
    ],
    "tristeza_desanimo": [
        "triste", "tristeza", "desanimada", "sem vontade", "vontade de chorar",
        "chorando", "choro fácil", "sem energia", "desmotivada", "vazia por dentro",
        "não sinto prazer",
    ],
    "estresse_sobrecarga": [
        "estressada", "sobrecarregada", "não aguento mais", "exausta",
        "cansada demais", "sem tempo pra nada", "no limite", "pressão demais",
    ],
    "medo_inseguranca": [
        "medo", "insegura", "com medo de", "e se der errado", "não sei se consigo",
        "tenho pavor", "apavorada", "receio",
    ],
    "bem_estar": [
        "feliz", "tranquila", "bem hoje", "animada", "grata", "leve",
        "de bem com a vida", "tudo certo",
    ],
}

# Frases que indicam sintoma FÍSICO mencionado no texto livre -- não é
# emoção, mas deve acender o alerta já existente no app (não duplicar
# lógica clínica aqui, só sinalizar pra rotear).
SINTOMA_FISICO = [
    "sangramento", "dor forte", "inchaço", "visão embaçada", "dor de cabeça forte",
    "não sinto o bebê mexer", "contração", "febre",
]


def _para_padrao(frase):
    """Transforma uma frase-chave em regex tolerante: permite ate 2
    palavras entre os termos da frase (ex: 'visão embaçada' também bate
    em 'visão meio embaçada' ou 'visão ficou um pouco embaçada')."""
    palavras = frase.split()
    return r"\b" + r"\W+(?:\w+\W+){0,3}".join(re.escape(p) for p in palavras) + r"\b"


PADROES = {
    categoria: [re.compile(_para_padrao(p)) for p in palavras]
    for categoria, palavras in PALAVRAS_CHAVE.items()
}
PADROES_SINTOMA = [re.compile(_para_padrao(p)) for p in SINTOMA_FISICO]


def normalizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\w\sáàâãéêíóôõúüç]", " ", texto)
    return texto


def classificar_checkin(texto):
    """Retorna um dicionário com as categorias emocionais detectadas e um
    alerta separado se sintoma físico for mencionado."""
    texto_norm = normalizar(texto)

    categorias_detectadas = {}
    for categoria, padroes in PADROES.items():
        acertos = [p.pattern for p, orig in zip(padroes, PALAVRAS_CHAVE[categoria]) if p.search(texto_norm)]
        nomes_acertos = [orig for p, orig in zip(padroes, PALAVRAS_CHAVE[categoria]) if p.search(texto_norm)]
        if nomes_acertos:
            categorias_detectadas[categoria] = nomes_acertos

    sintomas_detectados = [orig for p, orig in zip(PADROES_SINTOMA, SINTOMA_FISICO) if p.search(texto_norm)]

    if not categorias_detectadas:
        categorias_detectadas = {"neutro_sem_sinal_claro": []}

    return {
        "categorias": categorias_detectadas,
        "alerta_sintoma_fisico": sintomas_detectados,
    }
