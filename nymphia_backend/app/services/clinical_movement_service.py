"""
Serviço de Triagem Clínica de Movimento, Postura e Exercícios Gestacionais
Diretrizes: FEBRASGO, ACOG (American College of Obstetricians and Gynecologists)
e Ministério da Saúde do Brasil.

Analisa como a gestante se sente (energia, queixas musculoesqueléticas, dores e sinais de alerta)
para determinar com precisão médica o que a IA DEVE recomendar e o que NÃO PODE falar para ela fazer.
"""

from typing import Dict, Any, List, Optional

SINAIS_ALERTA_CONTRAINDICACAO_ABSOLUTA = [
    "sangramento", "sangramento vaginal", "perda de liquido", "bolsa rompeu",
    "contracoes regulares", "contrações de parto", "dor toracica", "dor no peito",
    "falta de ar em repouso", "tontura subita", "escotomas", "pontos brilhantes na visao",
    "visao embaçada", "pressao alta", "febre"
]

def avaliar_seguranca_movimento(
    disposicao: str, # "disposta" | "leve_cansaco" | "exausta"
    queixas: List[str], # ["dor_lombar", "dor_pelvica", "ciatico", "pernas_inchadas", "azia", "nenhuma"]
    sinais_alerta: List[str], # sinais reportados
    semana_gestacional: int = 24
) -> Dict[str, Any]:
    """
    Motor determinístico de segurança postural e prescrição de movimentos.
    Avalia o estado relatado pela paciente para filtrar o que a IA deve falar, sugerir ou proibir.
    """
    # 1. Checagem de Contraindicações Absolutas
    tem_sinal_alerta = len(sinais_alerta) > 0

    if tem_sinal_alerta:
        return {
            "apta_exercicio": False,
            "status_clinico": "CONTRAINDICACAO_ABSOLUTA",
            "nivel_risco": "alto",
            "cor_alerta": "#C0392B",
            "mensagem_ia": (
                "Atenção Médica Imediata: Você relatou sinais clínicos de alerta. "
                "Qualquer exercício, alongamento ou esforço físico está estritamente suspenso no momento. "
                "Deite-se confortavelmente sobre o lado esquerdo e entre em contato imediatamente com sua equipe obstétrica ou dirija-se à maternidade."
            ),
            "exercicios_permitidos": [],
            "exercicios_proibidos": [
                "Qualquer prática de exercício físico",
                "Caminhadas prolongadas ou subir escadas",
                "Alongamentos ou esforços abdominais",
                "Tarefas domésticas pesadas"
            ],
            "posicao_repouso_obrigatoria": "Decúbito Lateral Esquerdo (DLE) com travesseiro entre as pernas e sob o abdômen",
            "orientacoes_especificas": [
                "Evite movimentos bruscos e não realize esforço de carregar pesos.",
                "Observe se há piora dos sintomas de sangramento, perda de líquido ou cólica.",
                "Tenha em mãos sua Caderneta de Pré-Natal e documento oficial."
            ]
        }

    # 2. Gestante Apta com Adaptações Personalizadas
    recomendados: List[Dict[str, Any]] = []
    proibidos: List[str] = []
    orientacoes: List[str] = []

    # Regra Universal da Veia Cava (> 16 semanas)
    if semana_gestacional >= 16:
        proibidos.append("Decúbito dorsal prolongado (deitar de barriga para cima por mais de 3 minutos sem elevação)")
        orientacoes.append("Como você está com 16 semanas ou mais, nunca permaneça deitada de costas no chão: o peso do bebê pode comprimir a veia cava e diminuir a oxigenação fetal. Sempre opte pelo lado esquerdo ou posição sentada.")

    # Análise das queixas específicas:
    tem_dor_lombar = "dor_lombar" in queixas
    tem_dor_pelvica = "dor_pelvica" in queixas
    tem_ciatico = "ciatico" in queixas
    tem_pernas_inchadas = "pernas_inchadas" in queixas
    tem_azia = "azia" in queixas

    # Avaliação por Disposição
    if disposicao == "exausta":
        orientacoes.append("Seu corpo está demandando descanso metabólico hoje. Focaremos 100% em respiração e alívio postural, sem treinos de esforço.")
        proibidos.append("Treinos de resistência ou musculação com carga")
        proibidos.append("Exercícios aeróbicos ou caminhadas longas")
        recomendados.append({
            "id": "respiracao_diafragmatica",
            "titulo": "Respiração Diafragmática Acalmadora",
            "beneficio": "Reduz o cortisol, acalma o sistema nervoso autônomo e melhora a oxigenação da placenta.",
            "como_fazer": "Sente-se confortavelmente com as costas apoiadas. Inspire profundamente pelo nariz contando 4 segundos, sinta suas costelas se expandirem lateralmente e expire pela boca suavemente por 6 segundos."
        })
        recomendados.append({
            "id": "relaxamento_lateral_esquerdo",
            "titulo": "Repouso em Decúbito Lateral Esquerdo",
            "beneficio": "Alívio gravitacional imediato na coluna e liberação máxima do fluxo da veia cava.",
            "como_fazer": "Deite sobre o lado esquerdo do corpo. Coloque um travesseiro entre os joelhos mantendo o quadril alinhado e outro travesseiro suave sob a barriga."
        })

    # Avaliação de Dor Lombar
    if tem_dor_lombar:
        proibidos.append("Hiperextensão da coluna lombar (arcar as costas para trás)")
        proibidos.append("Levantamento de pesos livres do chão flexionando a coluna sem dobrar os joelhos")
        proibidos.append("Abdominais tradicionais de flexão de tronco (risco de diástase)")
        recomendados.append({
            "id": "bascula_pelvica",
            "titulo": "Báscula Pélvica Suave (Em pé ou na Bola Suíça)",
            "beneficio": "Mobiliza as articulações lombossacrais e solta a fáscia tensa da região lombar.",
            "como_fazer": "Em pé com joelhos levemente destravados ou sentada na bola: encaixe o quadril para frente suavemente (retroversão) e retorne à posição neutra, sem empinar exageradamente."
        })
        recomendados.append({
            "id": "gato_vaca_suave",
            "titulo": "Postura Quatro Apoios (Gato-Vaca Suave)",
            "beneficio": "Descomprime a coluna vertebral, tirando o peso da barriga da região lombar.",
            "como_fazer": "Em um tapete macio em 4 apoios (mãos sob os ombros, joelhos sob os quadris): ao expirar, curve as costas para cima suavemente como um gato. Ao inspirar, volte à posição reta e neutra."
        })
        recomendados.append({
            "id": "alongamento_piriforme_sentada",
            "titulo": "Alongamento de Glúteo e Piriforme Sentada",
            "beneficio": "Alivia a pressão sobre o nervo ciático e reduz a contratura dos glúteos.",
            "como_fazer": "Sentada em uma cadeira firme, cruze um tornozelo sobre o joelho oposto. Mantenha a coluna ereta e incline levemente o peito para frente até sentir um alongamento agradável no glúteo."
        })

    # Avaliação de Dor Pélvica / Sínfise Púbica (DSP)
    if tem_dor_pelvica:
        proibidos.append("Exercícios com pernas assimétricas (afundo, passadas, agachamento unilateral)")
        proibidos.append("Aberturas extremas de pernas (borboleta extrema ou alongamento excessivo de virilha)")
        proibidos.append("Cruzar as pernas ao sentar ou subir degraus altos de dois em dois")
        recomendados.append({
            "id": "isometria_adutores",
            "titulo": "Ativação Isométrica Simétrica com Almofada",
            "beneficio": "Estabiliza o anel pélvico sem forçar a articulação da sínfise púbica.",
            "como_fazer": "Sentada ou deitada de lado: coloque uma almofada ou bola macia entre os joelhos. Pressione suavemente por 5 segundos e relaxe, mantendo sempre as duas pernas unidas e alinhadas."
        })
        recomendados.append({
            "id": "kegel_suave",
            "titulo": "Fortalecimento Suave do Assoalho Pélvico (Kegel)",
            "beneficio": "Dá suporte aos órgãos pélvicos e ao peso do útero, prevenindo perda involuntária de urina.",
            "como_fazer": "Contraia suavemente a musculatura perineal (como se fosse segurar o xixi por 3 segundos) e solte completamente por 5 segundos. Faça 5 repetições sem prender a respiração."
        })

    # Avaliação de Ciático
    if tem_ciatico and not tem_dor_lombar:
        recomendados.append({
            "id": "alongamento_ciatico",
            "titulo": "Descompressão do Nervo Ciático na Cadeira",
            "beneficio": "Libera a compressão do piriforme sobre o nervo ciático.",
            "como_fazer": "Sentada, estique suavemente a perna afetada apoiando o calcanhar no chão e aponte os dedos do pé para o teto, mantendo a coluna alinhada."
        })

    # Avaliação de Pernas Inchadas / Retorno Venoso
    if tem_pernas_inchadas:
        recomendados.append({
            "id": "bomba_tornozelo",
            "titulo": "Bomba de Panturrilha (Movimentos Circulares e Flexão)",
            "beneficio": "A panturrilha atua como o 'segundo coração', bombeando o sangue de volta e drenando o edema das pernas.",
            "como_fazer": "Sentada ou reclinada: aponte os pés para frente e puxe em direção ao corpo 15 vezes. Em seguida, faça giros circulares suaves nos tornozelos."
        })

    # Avaliação de Azia / Refluxo
    if tem_azia:
        proibidos.append("Posições invertidas ou deitar-se logo após os exercícios")
        orientacoes.append("Devido à azia relatada, todas as posturas devem ser executadas com o tronco ereto ou sentado, nunca deitada ou com a cabeça abaixo do nível do estômago.")

    # Se a gestante estiver ótima e sem queixas
    if not queixas or queixas == ["nenhuma"]:
        recomendados.append({
            "id": "alongamento_peitoral_postura",
            "titulo": "Abertura Peitoral e Alinhamento Cervical",
            "beneficio": "Compensa o peso das mamas e a curvatura dos ombros para frente.",
            "como_fazer": "Em pé ou sentada: entrelace as mãos atrás do quadril ou apoie as mãos na lombar, abrindo o peito com suavidade e olhando para frente."
        })
        recomendados.append({
            "id": "mobilidade_pelvica_ativa",
            "titulo": "Mobilidade Pélvica Ativa na Bola ou em Pé",
            "beneficio": "Prepara a bacia para o parto e melhora a circulação pélvica.",
            "como_fazer": "Faça círculos lentos com o quadril (sentido horário e anti-horário), mantendo a respiração contínua e suave."
        })

    # Se a gestante estiver no 3º trimestre (> 28 semanas)
    if semana_gestacional >= 28:
        orientacoes.append("No 3º trimestre, os ligamentos estão ainda mais flexíveis por conta da relaxina. Mantenha os movimentos dentro de uma faixa confortável, sem forçar o limite articular.")

    return {
        "apta_exercicio": True,
        "status_clinico": "APTA_COM_ADAPTACOES",
        "nivel_risco": "baixo",
        "cor_alerta": "#27AE60",
        "mensagem_ia": _gerar_fala_personalizada_ia(disposicao, queixas, semana_gestacional),
        "exercicios_permitidos": recomendados,
        "exercicios_proibidos": proibidos,
        "orientacoes_especificas": orientacoes,
        "posicao_descanso_ideal": "Decúbito Lateral Esquerdo com travesseiro entre os joelhos"
    }

def _gerar_fala_personalizada_ia(disposicao: str, queixas: List[str], semana: int) -> str:
    """Gera mensagem empática e natural da IA de voz para a gestante."""
    if "dor_lombar" in queixas and "dor_pelvica" in queixas:
        return "Olá querida! Percebi que você está com desconforto na lombar e na bacia hoje. Já filtrei apenas exercícios suaves que protegem suas articulações e proibi movimentos assimétricos. Vamos fazer tudo com calma!"
    elif "dor_lombar" in queixas:
        return "Olá querida! Como você relatou dor na lombar, preparei uma série especial para aliviar a tensão das costas e descomprimir a coluna com segurança."
    elif "dor_pelvica" in queixas:
        return "Olá! Com a dor na bacia que você mencionou, é muito importante mantermos as pernas sempre alinhadas. Bloqueei movimentos unilaterais para cuidar da sua sínfise púbica."
    elif disposicao == "exausta":
        return "Olá querida! Ouvi o seu corpo: hoje ele pediu acolhimento. Vamos focar apenas em respiração gostosa e alívio do peso do bebê, sem nenhum treino cansativo."
    else:
        return f"Que ótimo te ver por aqui na sua {semana}ª semana! Seu corpo está pronto para uma sessão gostosa de mobilidade e postura segura. Vamos começar?"
