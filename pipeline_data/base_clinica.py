# -*- coding: utf-8 -*-
"""
Nymphia -- Base clínica pro RAG do Claude API.

Nível de informação educativa pro paciente (o que FEBRASGO/MS/OMS
comunicam pra gestante saber reconhecer), não protocolo clínico de
manejo -- isso é trabalho de profissional de saúde revisar e
formalizar antes de produção, isto aqui é o esqueleto.
"""

BASE_CLINICA = {
    "pre_eclampsia": """
Pré-eclâmpsia: pressão alta que aparece na segunda metade da gestação,
geralmente acompanhada de proteína na urina. Sinais de alerta pra
gestante saber reconhecer: dor de cabeça forte e persistente, visão
embaçada ou pontos luminosos, inchaço súbito (rosto, mãos), dor no
lado direito superior do abdômen. É a principal causa de morte materna
no Brasil -- qualquer combinação desses sinais pede avaliação médica
no mesmo dia, não espera pra próxima consulta.
""",
    "eclampsia": """
Eclâmpsia: evolução grave da pré-eclâmpsia, com convulsões. É uma
emergência médica absoluta. Sinais que precedem: os mesmos da
pré-eclâmpsia, muitas vezes se intensificando rápido.
""",
    "hellp": """
Síndrome HELLP: complicação grave e rara, geralmente associada a
quadros de pré-eclâmpsia. Sintomas: dor no abdômen superior, náusea e
vômito que pioram, mal-estar geral intenso. Emergência médica.
""",
    "diabetes_gestacional": """
Diabetes gestacional: aumento da glicemia que surge durante a
gravidez, geralmente identificado por exame de rotina (não por
sintoma perceptível na maioria dos casos). Controlado com
acompanhamento nutricional, monitoramento da glicemia e, se
necessário, medicação prescrita pelo médico. Sinais que merecem
atenção: sede muito fora do comum, urinar com frequência muito maior
que o normal, cansaço extremo.
""",
    "tireoide": """
Distúrbios de tireoide na gestação (hipo ou hipertireoidismo): podem
afetar o desenvolvimento do bebê se não tratados. Diagnóstico é por
exame de sangue de rotina do pré-natal. Sinais que merecem
investigação: cansaço extremo persistente, mudança de peso não
explicada, alteração de humor fora do padrão da própria gestante.
""",
    "infeccoes": """
Infecções na gestação (ITU, sífilis, toxoplasmose, zika, dengue): cada
uma com sinal próprio. ITU costuma dar ardência ao urinar e vontade
frequente; febre alta pede atenção sempre, principalmente combinada
com outros sintomas. Pré-natal de rotina já rastreia sífilis e
toxoplasmose -- adesão aos exames é a principal prevenção.
""",
    "bem_estar_fetal": """
Bem-estar fetal: acompanhado principalmente pela percepção da
gestante dos movimentos do bebê. Reduções importantes ou ausência de
movimento merecem contato com o médico no mesmo dia -- não é uma
situação de "esperar pra ver".
""",
    "malformacoes": """
Malformações: rastreadas principalmente por ultrassom morfológico,
nas janelas específicas da gestação recomendadas pelo pré-natal. Não é
algo que a gestante consiga notar sozinha no dia a dia -- é
acompanhamento de exame, não de sintoma.
""",
}

# Palavras-chave por categoria, pra recuperação simples (mesma lógica
# do sistema de regras do check-in, por consistência arquitetural)
PALAVRAS_CHAVE_RAG = {
    "pre_eclampsia": ["pressão", "dor de cabeça", "visão embaçada", "inchaço", "inchada"],
    "eclampsia": ["convulsão", "convulsionar"],
    "hellp": ["dor no abdômen", "mal-estar intenso"],
    "diabetes_gestacional": ["glicemia", "diabetes", "sede", "urinar muito", "açúcar"],
    "tireoide": ["tireoide", "hipotireoidismo", "hipertireoidismo"],
    "infeccoes": ["infecção", "ardência", "febre", "sífilis", "toxoplasmose", "zika", "dengue", "itu"],
    "bem_estar_fetal": ["bebê não mexe", "bebê parou de mexer", "movimento do bebê", "chutes"],
    "malformacoes": ["malformação", "ultrassom morfológico", "anomalia"],
}


def recuperar_contexto(mensagem_usuaria, max_categorias=2):
    """Retorna os trechos da base clínica relevantes pra mensagem,
    baseado em palavra-chave. Versão inicial simples -- evolução
    natural seria embeddings + busca vetorial, mas isso é próximo
    passo, não bloqueio pro MVP."""
    texto = mensagem_usuaria.lower()
    encontrados = []
    for categoria, palavras in PALAVRAS_CHAVE_RAG.items():
        if any(p in texto for p in palavras):
            encontrados.append(categoria)
    encontrados = encontrados[:max_categorias]
    if not encontrados:
        return ""
    return "\n".join(BASE_CLINICA[c].strip() for c in encontrados)
