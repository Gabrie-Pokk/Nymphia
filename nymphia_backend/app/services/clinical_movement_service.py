"""
Orientação de movimento e postura na gestação, por regras fixas (não é IA).

Base principal: diretriz canadense de atividade física na gestação (Mottola MF
et al., Br J Sports Med 2018;52:1339-1346, publicada como "2019 Canadian
guideline"): sinais para parar o exercício (Quadro 2), posição de barriga para
cima (recomendação 6) e exercícios do assoalho pélvico (recomendação 5).

Revisado em 15/10/2026: saíram afirmações sem base ("melhora a oxigenação da
placenta", "prepara a bacia para o parto", proibição de deitar de costas a
partir de 16 semanas por "mais de 3 minutos").
"""

from typing import Dict, Any, List, Optional

SINAIS_ALERTA_CONTRAINDICACAO_ABSOLUTA = [
    "sangramento", "sangramento vaginal", "perda de liquido", "bolsa rompeu",
    "contracoes regulares", "contrações de parto", "dor toracica", "dor no peito",
    "falta de ar em repouso", "tontura subita", "escotomas", "pontos brilhantes na visao",
    "visao embaçada", "pressao alta", "febre"
]

# Diretriz canadense 2019, Quadro 2: parar a atividade e procurar atendimento
SINAIS_PARA_PARAR = (
    "Pare o exercício e procure atendimento se tiver: falta de ar forte que continua mesmo parada, "
    "dor forte no peito, contrações regulares e doloridas, sangramento vaginal, perda de líquido "
    "pela vagina, ou tontura ou desmaio que continua mesmo parada."
)

POSICAO_DE_COSTAS = (
    "Se ao fazer exercício deitada de barriga para cima você sentir tontura, enjoo ou mal-estar, "
    "mude de posição: de lado, sentada ou em pé."
)

def avaliar_seguranca_movimento(
    disposicao: str, # "disposta" | "leve_cansaco" | "exausta"
    queixas: List[str], # ["dor_lombar", "dor_pelvica", "ciatico", "pernas_inchadas", "azia", "nenhuma"]
    sinais_alerta: List[str], # sinais reportados
    semana_gestacional: Optional[int] = None
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
                "Você marcou um sinal de alerta. Não faça exercício agora. Procure a maternidade ou ligue "
                "192 (SAMU). Enquanto espera, fique em repouso, de preferência deitada de lado."
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

    # Semana desconhecida: vale a cautela de fim de gestação (todas as restrições)
    semana_para_regras = semana_gestacional if semana_gestacional is not None else 40

    # 2. Gestante Apta com Adaptações Personalizadas
    recomendados: List[Dict[str, Any]] = []
    proibidos: List[str] = []
    orientacoes: List[str] = []

    # Sinais para parar valem para todas
    orientacoes.append(SINAIS_PARA_PARAR)

    # Barriga para cima: a diretriz pede mudar de posição se houver sintomas.
    # A partir da metade da gestação o útero pode comprimir a veia cava; antes, a orientação não se aplica.
    if semana_para_regras >= 20:
        proibidos.append("Continuar deitada de barriga para cima se der tontura, enjoo ou mal-estar")
        orientacoes.append(POSICAO_DE_COSTAS)

    # Análise das queixas específicas:
    tem_dor_lombar = "dor_lombar" in queixas
    tem_dor_pelvica = "dor_pelvica" in queixas
    tem_ciatico = "ciatico" in queixas
    tem_pernas_inchadas = "pernas_inchadas" in queixas
    tem_azia = "azia" in queixas

    # Avaliação por Disposição
    if disposicao == "exausta":
        orientacoes.append("Hoje o seu corpo está pedindo descanso. A sugestão é ficar só com respiração e posições de alívio, sem treino de esforço.")
        proibidos.append("Treinos de resistência ou musculação com carga")
        proibidos.append("Exercícios aeróbicos ou caminhadas longas")
        recomendados.append({
            "id": "respiracao_diafragmatica",
            "titulo": "Respiração Diafragmática Acalmadora",
            "beneficio": "Ajuda a relaxar e a soltar a tensão dos ombros.",
            "como_fazer": "Sente-se confortavelmente com as costas apoiadas. Inspire profundamente pelo nariz contando 4 segundos, sinta suas costelas se expandirem lateralmente e expire pela boca suavemente por 6 segundos."
        })
        recomendados.append({
            "id": "relaxamento_lateral_esquerdo",
            "titulo": "Descanso deitada de lado",
            "beneficio": "Alivia as costas; deitada de lado, o útero não pesa sobre os vasos das costas.",
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
            "beneficio": "Movimenta a parte baixa das costas e pode aliviar a tensão na lombar.",
            "como_fazer": "Em pé com joelhos levemente destravados ou sentada na bola: encaixe o quadril para frente suavemente (retroversão) e retorne à posição neutra, sem empinar exageradamente."
        })
        recomendados.append({
            "id": "gato_vaca_suave",
            "titulo": "Postura Quatro Apoios (Gato-Vaca Suave)",
            "beneficio": "Tira o peso da barriga da lombar por alguns instantes.",
            "como_fazer": "Em um tapete macio em 4 apoios (mãos sob os ombros, joelhos sob os quadris): ao expirar, curve as costas para cima suavemente como um gato. Ao inspirar, volte à posição reta e neutra."
        })
        recomendados.append({
            "id": "alongamento_piriforme_sentada",
            "titulo": "Alongamento de Glúteo e Piriforme Sentada",
            "beneficio": "Alonga o glúteo, o que costuma aliviar o desconforto que desce pela perna.",
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
            "beneficio": "Fortalece a musculatura da bacia com as pernas alinhadas, sem forçar a frente da bacia.",
            "como_fazer": "Sentada ou deitada de lado: coloque uma almofada ou bola macia entre os joelhos. Pressione suavemente por 5 segundos e relaxe, mantendo sempre as duas pernas unidas e alinhadas."
        })
        recomendados.append({
            "id": "kegel_suave",
            "titulo": "Fortalecimento Suave do Assoalho Pélvico (Kegel)",
            "beneficio": "Feito todo dia, reduz o risco de perder urina sem querer (diretriz canadense 2019). Vale pedir para a equipe ou fisioterapeuta conferir a técnica.",
            "como_fazer": "Contraia suavemente a musculatura perineal (como se fosse segurar o xixi por 3 segundos) e solte completamente por 5 segundos. Faça 5 repetições sem prender a respiração."
        })

    # Avaliação de Ciático
    if tem_ciatico and not tem_dor_lombar:
        recomendados.append({
            "id": "alongamento_ciatico",
            "titulo": "Descompressão do Nervo Ciático na Cadeira",
            "beneficio": "Alongamento leve para o desconforto que desce pela perna.",
            "como_fazer": "Sentada, estique suavemente a perna afetada apoiando o calcanhar no chão e aponte os dedos do pé para o teto, mantendo a coluna alinhada."
        })

    # Avaliação de Pernas Inchadas / Retorno Venoso
    if tem_pernas_inchadas:
        recomendados.append({
            "id": "bomba_tornozelo",
            "titulo": "Bomba de Panturrilha (Movimentos Circulares e Flexão)",
            "beneficio": "O movimento da panturrilha ajuda o sangue a voltar das pernas e pode aliviar o inchaço.",
            "como_fazer": "Sentada ou reclinada: aponte os pés para frente e puxe em direção ao corpo 15 vezes. Em seguida, faça giros circulares suaves nos tornozelos."
        })

    # Avaliação de Azia / Refluxo
    if tem_azia:
        proibidos.append("Posições invertidas ou deitar-se logo após os exercícios")
        orientacoes.append("Com azia, prefira fazer os exercícios em pé ou sentada, sem deitar e sem baixar a cabeça abaixo do estômago.")

    # Se a gestante estiver ótima e sem queixas
    if not queixas or queixas == ["nenhuma"]:
        recomendados.append({
            "id": "alongamento_peitoral_postura",
            "titulo": "Abertura Peitoral e Alinhamento Cervical",
            "beneficio": "Abre o peito e ajuda a não ficar com os ombros caídos para a frente.",
            "como_fazer": "Em pé ou sentada: entrelace as mãos atrás do quadril ou apoie as mãos na lombar, abrindo o peito com suavidade e olhando para frente."
        })
        recomendados.append({
            "id": "mobilidade_pelvica_ativa",
            "titulo": "Mobilidade Pélvica Ativa na Bola ou em Pé",
            "beneficio": "Movimenta o quadril e a lombar com suavidade.",
            "como_fazer": "Faça círculos lentos com o quadril (sentido horário e anti-horário), mantendo a respiração contínua e suave."
        })

    # Se a gestante estiver no 3º trimestre (> 28 semanas)
    if semana_para_regras >= 28:
        orientacoes.append("No fim da gestação o equilíbrio muda com o peso da barriga e as articulações ficam mais soltas. Faça os movimentos devagar, perto de um apoio, sem forçar.")

    return {
        "apta_exercicio": True,
        "status_clinico": "APTA_COM_ADAPTACOES",
        "nivel_risco": "baixo",
        "cor_alerta": "#27AE60",
        "mensagem_ia": _gerar_fala_personalizada_ia(disposicao, queixas, semana_gestacional),
        "exercicios_permitidos": recomendados,
        "exercicios_proibidos": proibidos,
        "orientacoes_especificas": orientacoes,
        "posicao_descanso_ideal": "Deitada de lado, com um travesseiro entre os joelhos"
    }

def _gerar_fala_personalizada_ia(disposicao: str, queixas: List[str], semana: Optional[int]) -> str:
    """Gera mensagem empática e natural da IA de voz para a gestante."""
    if "dor_lombar" in queixas and "dor_pelvica" in queixas:
        return "Como você marcou dor na lombar e na bacia, separei exercícios suaves e deixei de fora movimentos com uma perna de cada vez. Vá com calma e pare se doer."
    elif "dor_lombar" in queixas:
        return "Como você marcou dor na lombar, separei exercícios leves que costumam aliviar a tensão nas costas. Pare se a dor aumentar."
    elif "dor_pelvica" in queixas:
        return "Com dor na bacia, o melhor é manter as pernas alinhadas. Deixei de fora movimentos com uma perna de cada vez."
    elif disposicao == "exausta":
        return "Hoje o seu corpo está pedindo descanso. Ficamos só com respiração e posições de alívio, sem treino cansativo."
    else:
        quando = f" na sua {semana}ª semana" if semana else ""
        return f"Que bom te ver por aqui{quando}! Aqui estão movimentos leves de postura e mobilidade. Pare se sentir qualquer desconforto."
