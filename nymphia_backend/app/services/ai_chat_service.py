import re
import random
import logging
import requests
from typing import Tuple, Dict, Any, List, Optional
from app.config import settings
from app.services.rules_engine import analyze_urgency
from app.services.ai_text_service import classify_text_emotions

logger = logging.getLogger("nymphia.ai_chat_service")

# Base de Conhecimento Clínico Estruturada (FEBRASGO / Ministério da Saúde / OMS)
CONHECIMENTO_CLINICO = {
    "toxoplasmose": {
        "resumo": "TOXOPLASMOSE GESTACIONAL (Protocolo FEBRASGO/MS): A toxoplasmose congênita decorre da infecção pelo parasita *Toxoplasma gondii*, que pode atravessar a barreira placentária.",
        "cuidados": [
            "Consumir somente carnes muito bem passadas (temperatura interna superior a 66°C);",
            "Higienizar cuidadosamente verduras, legumes e frutas com solução de hipoclorito de sódio ou água clorada apropriada para alimentos;",
            "Evitar o manuseio de caixas de areia de gatos ou higienizá-las diariamente usando luvas descartáveis e lavando muito bem as mãos em seguida;",
            "Ingerir exclusivamente água tratada, filtrada ou fervida;",
            "Evitar contato desprotegido com terra, areia de construção ou jardinagem sem luvas."
        ],
        "orientacao": "Acompanhe seus exames sorológicos (IgG e IgM) no pré-natal. Caso haja qualquer alteração, seu obstetra avaliará a indicação de tratamento precoce."
    },
    "alimentacao": {
        "resumo": "NUTRIÇÃO E ALIMENTAÇÃO GESTACIONAL (FEBRASGO/MS): Uma nutrição rica e equilibrada durante a gestação é indispensável para a organogênese do bebê e a disposição materna.",
        "cuidados": [
            "Fracione as refeições em 5 a 6 porções menores ao longo do dia para evitar sobrecarga gástrica e manter a glicemia estável;",
            "Priorize fontes de ferro (carnes magras, feijões, lentilhas, folhas verde-escuras) combinadas com vitamina C (laranja, limão, acerola) para potencializar a absorção;",
            "Mantenha hidratação constante: consuma entre 2,5 e 3 litros de água por dia;",
            "Limite o consumo de cafeína a no máximo 1 a 2 xícaras pequenas ao dia (menos de 200 mg de cafeína);",
            "Evite estritamente leites e queijos não pasteurizados (risco de listeriose), carnes e peixes crus ou malcozidos e ovos com gema mole."
        ],
        "orientacao": "Suplementações como ácido fólico, ferro e polivitamínicos devem seguir exatamente a prescrição do seu médico de pré-natal."
    },
    "enjoo_azia": {
        "resumo": "CONTROLE DE NÁUSEAS E AZIA GESTACIONAL: Náuseas no primeiro trimestre e azia no segundo/terceiro trimestres são frequentes devido às variações hormonais (hCG e progesterona) e à compressão gástrica pelo útero.",
        "cuidados": [
            "Para enjoos matinais: coma uma bolacha água e sal ou torrada seca ainda na cama antes de se levantar;",
            "Prefira refeições frias ou em temperatura ambiente, que exalam menos odores estimulantes do refluxo;",
            "Pequenos goles de água gelada, água com limão ou picolés de fruta cítrica ajudam a aliviar a sensação de mal-estar;",
            "Para azia: evite deitar-se logo após as refeições (aguarde ao menos 60 a 90 minutos) e reduza frituras, pimentas, café e chocolate;",
            "Elevar ligeiramente a cabeceira da cama (10 a 15 cm) reduz bastante o refluxo gastroesofágico noturno."
        ],
        "orientacao": "Se os vômitos forem incessantes, impedindo qualquer hidratação por mais de 12 horas, comunique sua equipe de saúde para prevenção de desidratação."
    },
    "movimentos_fetais": {
        "resumo": "VITALIDADE FETAL E MOVIMENTAÇÃO (FEBRASGO): Os movimentos fetais são uma das maiores alegrias da gestante e um indicador clínico essencial de vitalidade e bem-estar fetal.",
        "cuidados": [
            "Na primeira gravidez, os movimentos costumam ser percebidos entre a 18ª e a 22ª semana de gestação;",
            "Em mulheres que já tiveram filhos antes, é possível sentir mais precocemente, a partir da 16ª semana;",
            "No terceiro trimestre, o bebê estabelece ciclos regulares de sono (20 a 40 minutos) intercalados com períodos ativos;",
            "Após o almoço ou jantar, deite-se confortavelmente sobre o lado esquerdo e observe: o esperado é perceber pelo menos 4 a 6 movimentos ao longo de uma hora."
        ],
        "orientacao": "No terceiro trimestre, caso note diminuição súbita e acentuada dos movimentos fetais por mais de 12 horas seguidas, procure imediatamente o serviço de maternidade para avaliação."
    },
    "dores_corpo": {
        "resumo": "ADAPTAÇÕES BIOMECÂNICAS E DORES MÚSCULO-ESQUELÉTICAS: Dores lombares, pélvicas e pontadas no baixo ventre são comuns devido à frouxidão ligamentar pela relaxina e à alteração do centro de gravidade.",
        "cuidados": [
            "Dor no ligamento redondo: pontadas rápidas nos lados da barriga ao mudar de posição são benignas; levante-se devagar;",
            "Para a coluna lombar: durma de lado com um travesseiro entre os joelhos para alinhar o quadril;",
            "Banhos mornos de chuveiro e compressas mornas locais proporcionam alívio muscular seguro;",
            "Evite sapatos de salto muito alto ou completamente rasteiros sem amortecimento;",
            "Atividades leves como caminhadas regulares e hidroginástica (com liberação obstétrica) fortalecem a musculatura paravertebral."
        ],
        "orientacao": "Atenção: dores com padrão rítmico (contrações regulares que aumentam de intensidade), acompanhadas de sangramento ou febre, devem ser avaliadas em pronto atendimento."
    },
    "sono_cansaco": {
        "resumo": "SONO E METABOLISMO NA GESTAÇÃO: A sonolência no início da gravidez e a dificuldade para dormir no fim são reações naturais às demandas metabólicas do organismo materno.",
        "cuidados": [
            "A melhor posição para dormir, especialmente a partir do 2º trimestre, é sobre o decúbito lateral esquerdo, pois otimiza o fluxo da veia cava e a oxigenação placentária;",
            "Utilize um travesseiro sob a barriga e outro entre as pernas para aliviar a tensão lombar;",
            "Pratique higiene do sono: reduza telas e luzes fortes pelo menos 45 minutos antes de deitar;",
            "Permita-se pequenas pausas de descanso de 15 a 20 minutos durante o dia quando possível."
        ],
        "orientacao": "Respeite os sinais de fadiga do seu corpo: gestar um bebê consome uma quantidade imensa de energia metabólica."
    },
    "trabalho_parto": {
        "resumo": "TRABALHO DE PARTO E SINAIS DE ADMISSÃO (OMS/FEBRASGO): O trabalho de parto ativo se caracteriza por contrações uterinas regulares, dolorosas e progressivas.",
        "cuidados": [
            "Falsas contrações (Braxton Hicks): são irregulares, indolores ou pouco desconfortáveis, e costumam ceder com repouso e hidratação;",
            "Trabalho de parto verdadeiro: contrações que ocorrem de forma rítmica (ex: a cada 4 a 5 minutos, durando 45 a 60 segundos) e aumentam progressivamente de intensidade;",
            "Tampão mucoso: a perda de secreção espessa e gelatinosa (às vezes com estrias de sangue) pode ocorrer dias antes do parto e isoladamente não significa início imediato;",
            "Ruptura da bolsa das águas: perda contínua de líquido transparente com odor característico (semelhante a água sanitária). Ao romper a bolsa, observe a cor do líquido e procure a maternidade."
        ],
        "orientacao": "Na presença de contrações rítmicas frequentes ou rompimento de bolsa antes de 37 semanas, vá imediatamente ao serviço de obstetrícia."
    },
    "pressao_edema": {
        "resumo": "PRESSÃO ARTERIAL E PREVENÇÃO DA PRÉ-ECLÂMPSIA (FEBRASGO): O acompanhamento da pressão arterial é o pilar central da prevenção e diagnóstico precoce da pré-eclâmpsia.",
        "cuidados": [
            "Inchaço fisiológico: edema nos pés e tornozelos no final do dia é comum pela gravidade e retorno venoso;",
            "Sinais de alerta: inchaço súbito que atinge rosto e mãos ao acordar, dor de cabeça frontal intensa e constante, alterações visuais (pontos brilhantes ou visão embaçada), ou dor forte na boca do estômago;",
            "Aferição periódica: registre os valores da sua pressão nas consultas de pré-natal e nos check-ins diários da Nymphia;",
            "A pressão normal na gestação deve permanecer abaixo de 140x90 mmHg."
        ],
        "orientacao": "Qualquer valor de pressão arterial igual ou superior a 140x90 mmHg associado a sintomas exige comparecimento imediato à maternidade."
    },
    "saude_emocional": {
        "resumo": "SAÚDE MENTAL E APOIO PERINATAL (MS/OMS): A gestação envolve transformações psicológicas e hormonais profundas. Sentimentos de ansiedade, insegurança ou sensibilidade são absolutamente humanos e válidos.",
        "cuidados": [
            "Converse abertamente com pessoas de confiança sobre seus receios e expectativas;",
            "Reserve momentos do dia para práticas de respiração diafragmática calma e desaceleração;",
            "Participe dos grupos de apoio e trocas acolhedoras na Comunidade Segura Nymphia;",
            "Não hesite em solicitar encaminhamento para acompanhamento psicológico perinatal caso o desânimo ou a angústia sejam constantes."
        ],
        "orientacao": "Cuidar da sua saúde emocional é cuidar diretamente da saúde do seu bebê. Você não precisa passar por tudo sozinha."
    },
    "amamentacao": {
        "resumo": "ALEITAMENTO MATERNO E PREPARAÇÃO (FEBRASGO/MS): O aleitamento materno é uma habilidade que mãe e bebê aprendem juntos após o nascimento.",
        "cuidados": [
            "Pega correta: a boca do bebê deve cobrir grande parte da aréola, com lábios evertidos ('peixinho') e queixo encostado na mama;",
            "Não esfregue buchas nem passe pomadas nos mamilos durante a gestação; a própria aréola produz óleos protetores naturais;",
            "O colostro produzido nos primeiros dias é altamente concentrado em anticorpos e é o alimento ideal e suficiente para o recém-nascido;",
            "Banhos de sol curtos de 10 a 15 minutos nas mamas (no início da manhã) ajudam a preparar a pele naturalmente."
        ],
        "orientacao": "Após o nascimento, solicite o apoio das enfermeiras obstétricas ou do banco de leite da maternidade para ajuste precoce da pega."
    },
    "vacinas_exames": {
        "resumo": "IMUNIZAÇÃO E EXAMES COMPLEMENTARES NO PRÉ-NATAL: A imunização na gestação protege tanto a mãe quanto o recém-nascido nos primeiros meses de vida via anticorpos transplacentários.",
        "cuidados": [
            "Vacinas preconizadas: dTpa (tríplice bacteriana acelular a partir da 20ª semana), Influenza (gripe, em qualquer trimestre) e Hepatite B;",
            "Exames ultrassonográficos essenciais: Translucência nucal (11 a 13 semanas) e Morfológico de 2º trimestre (20 a 24 semanas);",
            "Rastreio de Diabetes Gestacional: Teste oral de tolerância à glicose (TOTG 75g) entre 24 e 28 semanas;",
            "Exames de sangue periódicos: Hemograma, glicemia de jejum, sorologias e urina tipo 1 com urocultura."
        ],
        "orientacao": "Leve sua Caderneta da Gestante em todas as consultas para registro completo das vacinas e exames."
    },
    "enxoval_maternidade": {
        "resumo": "PLANEJAMENTO DO ENXOVAL E MALA MATERNIDADE: Organizar a mala da maternidade com antecedência (por volta da 32ª à 34ª semana) traz serenidade para a reta final.",
        "cuidados": [
            "Para a gestante: 2 a 3 camisolas ou pijamas com abertura frontal para amamentação, sutiãs de amamentação confortáveis, calcinhas pós-parto de cintura alta, absorventes pós-parto e itens de higiene pessoal;",
            "Documentos indispensáveis: Cartão de Pré-Natal/Caderneta da Gestante, documento oficial com foto, carteirinha do convênio ou cartão SUS e exames recentes;",
            "Para o bebê: 3 a 4 mudas de roupas lavadas com sabão neutro (body, culote e macacão), mantas, fraldas descartáveis tamanho RN/P e fraldas de pano/babetes."
        ],
        "orientacao": "Verifique com a maternidade escolhida se eles possuem uma lista recomendada de itens de admissão."
    }
}

AVISO_TRANSPARENCIA_CFM = (
    "\n\n---\n"
    "ℹ️ *Nota de Apoio Nymphia (Res. CFM 2.454/2026): Sou uma inteligência artificial assistente fundamentada em "
    "protocolos da FEBRASGO e Ministério da Saúde. Minhas orientações são educativas e preventivas, "
    "não substituindo o diagnóstico clínico presencial e as condutas do seu médico obstetra.*"
)

def _detectar_saudacao(texto: str) -> bool:
    patterns = [
        r"^(oi|ol[aá]|bom dia|boa tarde|boa noite|oie|opa|e a[ií])\b",
        r"\b(tudo bem|como vai|como est[aá]|quem [eé] voc[eê]|o que voc[eê] faz|como voc[eê] funciona|ajuda)\b"
    ]
    return any(re.search(p, texto, re.IGNORECASE) for p in patterns)

def _construir_resposta_saudacao(texto: str, categorias: List[str]) -> str:
    saudacoes = [
        "Olá, querida gestante! Que alegria ter você aqui.",
        "Olá! Estou muito feliz em te acolher hoje na Nymphia.",
        "Oi, tudo bem por aí? Espero que você e seu bebê estejam tendo um dia tranquilo e acolhedor."
    ]
    apresentacao = (
        f"{random.choice(saudacoes)}\n\n"
        "Sou a **Nymphia**, sua assistente inteligente dedicada ao acompanhamento gestacional. "
        "Fui desenvolvida sob os rigorosos protocolos da **FEBRASGO** e do **Ministério da Saúde** "
        "para te apoiar durante toda a gravidez.\n\n"
        "**Aqui você pode:**\n"
        "• Tirar dúvidas sobre sintomas comuns (enjoos, azia, dores lombares, inchaços);\n"
        "• Entender melhor o desenvolvimento do bebê e contagem de movimentos fetais;\n"
        "• Receber orientações de nutrição, hidratação e prevenção (como toxoplasmose);\n"
        "• Saber o que esperar de exames de pré-natal e vacinas;\n"
        "• Encontrar acolhimento para ansiedades, medos e oscilações de humor.\n\n"
        "Como você está se sentindo fisicamente e emocionalmente neste momento? Me conte, estou aqui para te ouvir!"
    )
    return apresentacao

def _buscar_tema_clinico(texto: str) -> Optional[str]:
    texto_lower = texto.lower()

    regras = {
        "toxoplasmose": [r"toxoplasmose", r"gato", r"areia de gato", r"carne crua", r"hortali[çc]a"],
        "enjoo_azia": [r"enjoo", r"enjoada", r"[aâ]nsia", r"v[oó]mito", r"azia", r"queima[çc][aã]o", r"refluxo", r"est[oô]mago embrulhado", r"azia terr[ií]vel"],
        "movimentos_fetais": [r"mexer", r"mexendo", r"chute", r"chutando", r"movimento.*beb[eê]", r"parou de mexer", r"beb[eê].*n[aã]o mexe", r"mexeu pouco"],
        "alimentacao": [r"alimenta[çc][aã]o", r"alimentar", r"comer", r"almo[çc]o", r"jantar", r"caf[eé] da manh[aã]", r"dieta", r"gr[aá]vida pode comer", r"caf[eé]", r"peixe cru", r"sushi", r"frutas", r"peso", r"engordar", r"refrigerante", r"ch[aá]", r"nutri[çc][aã]o", r"comida"],
        "dores_corpo": [r"dor nas costas", r"dor lombar", r"dor no p[eé] da barriga", r"c[oó]lica", r"dor p[eé]lvica", r"ci[aá]tico", r"dor na virilha", r"dor muscular", r"pontada na barriga"],
        "sono_cansaco": [r"sono", r"ins[oô]nia", r"cansa[çc]o", r"fadiga", r"posi[çc][aã]o de dormir", r"dormir de bru[çc]os", r"dormir de lado", r"lado esquerdo", r"muito sono"],
        "trabalho_parto": [r"trabalho de parto", r"contra[çc][oõ]es", r"contra[çc][aã]o", r"dilata[çc][aã]o", r"tamp[aã]o mucoso", r"parto normal", r"ces[aá]rea", r"plano de parto", r"bolsa estourou", r"rompeu a bolsa"],
        "pressao_edema": [r"press[aã]o", r"hipertens[aã]o", r"pr[eé]-ecl[aâ]mpsia", r"inchada", r"incha[çc]o", r"p[eé]s inchados", r"pernas inchadas", r"press[aã]o alta", r"edema"],
        "saude_emocional": [r"ansiedade", r"ansiosa", r"medo", r"nervosa", r"preocupada", r"choro", r"triste", r"estresse", r"depress[aã]o", r"puerp[eé]rio", r"solid[aã]o", r"ang[uú]stia"],
        "amamentacao": [r"amamenta[çc][aã]o", r"amamentar", r"leite materno", r"peito", r"bico do peito", r"colostro", r"rachadura no peito", r"fissura mamilar", r"livre demanda"],
        "vacinas_exames": [r"vacina", r"vacinas", r"dtpa", r"influenza", r"hepatite", r"ultrassom", r"morfol[oó]gico", r"glicemia", r"hemograma", r"curva glic[eê]mica", r"transluc[eê]ncia"],
        "enxoval_maternidade": [r"mala", r"enxoval", r"bolsa da maternidade", r"o que levar", r"roupinhas", r"quarto do beb[eê]"]
    }

    for tema, patterns in regras.items():
        if any(re.search(p, texto_lower) for p in patterns):
            return tema

    return None

def _formatar_resposta_clinica(tema: str) -> str:
    dados = CONHECIMENTO_CLINICO[tema]
    cuidados_formatados = "\n".join([f"• {c}" for c in dados["cuidados"]])
    
    resposta = (
        f"{dados['resumo']}\n\n"
        f"**Orientações e Recomendações Práticas:**\n{cuidados_formatados}\n\n"
        f"💡 **Dica de Cuidado:** {dados['orientacao']}"
    )
    return resposta

def _gerar_resposta_dinamica_ia(texto: str, scores: Dict[str, float], active_categories: List[str]) -> str:
    """
    Gera uma resposta altamente conversacional e contextualizada a partir das
    predições emocionais e físicas do modelo neural BERTimbau / motor de regras.
    """
    partes: List[str] = []

    # 1. Empatia e Validação Emocional Baseada em IA
    if "ansiedade" in active_categories or scores.get("ansiedade", 0) > 0.35:
        partes.append(
            "Percebo em suas palavras uma sensação de preocupação ou ansiedade. "
            "É absolutamente compreensível sentir isso: a maternidade traz transformações "
            "intensas no corpo, na mente e na nossa rotina."
        )
    elif "tristeza_desanimo" in active_categories or scores.get("tristeza_desanimo", 0) > 0.35:
        partes.append(
            "Sinto muito que você esteja se sentindo mais para baixo ou cansada hoje. "
            "Nem todos os dias da gestação são fáceis, e reconhecer seus sentimentos é um ato de profundo amor-próprio."
        )
    elif "estresse_sobrecarga" in active_categories or scores.get("estresse_sobrecarga", 0) > 0.35:
        partes.append(
            "Entendo perfeitamente o sentimento de sobrecarga. Gerar uma vida demanda muito esforço físico e mental, "
            "e às vezes as cobranças do dia a dia pesam mais do que deveriam."
        )
    elif "medo_inseguranca" in active_categories or scores.get("medo_inseguranca", 0) > 0.35:
        partes.append(
            "O receio e a insegurança diante de novos sinais do corpo são muito frequentes. "
            "Você não está sozinha nessa jornada, e buscar informação confiável é a melhor forma de acalmar o coração."
        )
    elif "bem_estar" in active_categories:
        partes.append(
            "Que notícia maravilhosa! Fico muito contente em saber que você está se sentindo bem e em sintonia com seu corpo e seu bebê."
        )

    # 2. Avaliação de Sintomas Físicos
    if "sintoma_fisico" in active_categories or scores.get("sintoma_fisico", 0) > 0.35:
        partes.append(
            "Sobre o desconforto físico que você mencionou: é importante observar a frequência e a intensidade com que ele ocorre. "
            "Se for um desconforto leve e passageiro, pequenas adaptações de repouso, hidratação e postura costumam trazer grande alívio. "
            "Contudo, caso o sintoma seja persistente ou progressivo, registrar no seu Diário Visual ou Check-in da Nymphia ajudará "
            "muito seu médico obstetra a avaliar o padrão."
        )

    # 3. Orientação Geral de Saúde e Bem-Estar
    if not partes:
        partes.append(
            "Obrigada por compartilhar isso comigo! Cada momento e cada fase da gestação trazem particularidades únicas."
        )

    partes.append(
        "Lembre-se sempre de manter uma boa hidratação ao longo do dia, respeitar suas pausas de repouso e manter seu cartão "
        "de pré-natal atualizado.\n\n"
        "Se quiser me contar mais detalhes (como há quanto tempo você está sentindo isso, sua idade gestacional aproximada ou se já conversou com seu médico), "
        "posso te orientar de forma ainda mais específica!"
    )

    return "\n\n".join(partes)

SYSTEM_PROMPT_NYMPHIA = (
    "Você é a Nymphia, assistente virtual inteligente e empática especializada em saúde materno-fetal "
    "e acompanhamento gestacional humanizado, fundamentada nas diretrizes da FEBRASGO (Federação Brasileira "
    "das Associações de Ginecologia e Obstetrícia) e do Ministério da Saúde do Brasil.\n\n"
    "Suas diretrizes fundamentais:\n"
    "1. Linguagem e Tom: Fale em português brasileiro com tom extremamente acolhedor, carinhoso, claro e tranquilizador.\n"
    "2. Acolhimento Integral: Valide as emoções da gestante (ansiedades, dúvidas, cansaço, medos e alegrias).\n"
    "3. Informação Educativa: Explique termos médicos de forma simples sobre desenvolvimento fetal, nutrição, exames e sinais comuns da gravidez.\n"
    "4. Limites Éticos (CFM 2.454/2026): NUNCA faça diagnósticos médicos conclusivos, NUNCA receite ou indique doses de remédios e sempre recomende discutir dúvidas clínicas na consulta de pré-natal.\n"
    "5. Formato: Respostas bem estruturadas, objetivas e carinhosas (2 a 4 parágrafos breves)."
)

def _consultar_gemini(texto: str, active_categories: List[str]) -> Optional[str]:
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "COLE_SUA_CHAVE_AQUI" or len(api_key.strip()) < 10:
        return None

    contexto_emocional = ""
    if active_categories:
        contexto_emocional = f"\n[Contexto emocional detectado pelo modelo clínico local da paciente: {', '.join(active_categories)}]"

    prompt_completo = f"{texto}{contexto_emocional}"

    modelos = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
    for modelo in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key.strip()}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT_NYMPHIA}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt_completo}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands and "content" in cands[0] and "parts" in cands[0]["content"]:
                    texto_gerado = cands[0]["content"]["parts"][0].get("text", "").strip()
                    if texto_gerado:
                        return texto_gerado
            else:
                logger.warning(f"Gemini API ({modelo}) retornou status {resp.status_code}: {resp.text[:150]}")
        except Exception as ex:
            logger.warning(f"Falha de conexão com Gemini ({modelo}): {ex}")
    return None

def generate_chat_response(message: str, recusa_ia: bool = False) -> Tuple[str, bool, str]:
    """
    Gera resposta conversacional inteligente e segura em múltiplos níveis:
    1. Triage de Emergência: Identifica sinais de alarme obstétrico imediatamente (sem delay de LLM).
    2. Detecção de Saudações: Responde com acolhimento caloroso e explicativo.
    3. Motor Clínico RAG FEBRASGO/MS: Responde a temas específicos com base sólida e orientações práticas.
    4. Consulta Gemini (se configurado): Resposta empática e clinicamente orientada por IA generativa.
    5. Inferência Neural BERTimbau: Gera resposta contextualizada pelo estado emocional e físico (fallback local).
    6. Transparência CFM 2.454/2026: Todos os pareceres informativos acompanham a nota de segurança.
    """
    texto_limpo = message.strip()

    # 1. Checagem de Urgência Obstétrica Absoluta
    is_urgent, alerts, urgency_guidance = analyze_urgency(texto_limpo)
    if is_urgent:
        return urgency_guidance, True, "regras_urgencia"

    # 2. Saudações e Apresentação
    scores, active_categories = classify_text_emotions(texto_limpo)
    if _detectar_saudacao(texto_limpo) and len(texto_limpo.split()) <= 7:
        resposta = _construir_resposta_saudacao(texto_limpo, active_categories)
        return resposta + AVISO_TRANSPARENCIA_CFM, False, "assistente_nymphia"

    # 3. Consulta ao Conhecimento Clínico Estruturado (FEBRASGO / MS)
    tema_detectado = _buscar_tema_clinico(texto_limpo)
    if tema_detectado and tema_detectado in CONHECIMENTO_CLINICO:
        resposta_clinica = _formatar_resposta_clinica(tema_detectado)
        return resposta_clinica + AVISO_TRANSPARENCIA_CFM, False, "base_clinica_ia"

    # 4. Consulta ao Gemini (se chave presente e sem recusa de IA pela gestante)
    if not recusa_ia:
        resposta_gemini = _consultar_gemini(texto_limpo, active_categories)
        if resposta_gemini:
            return resposta_gemini + AVISO_TRANSPARENCIA_CFM, False, "gemini_ia"

    # 5. Inferência Dinâmica BERTimbau + Contexto da Gestante (Fallback local)
    resposta_dinamica = _gerar_resposta_dinamica_ia(texto_limpo, scores, active_categories)
    return resposta_dinamica + AVISO_TRANSPARENCIA_CFM, False, "bertimbau_ia"
