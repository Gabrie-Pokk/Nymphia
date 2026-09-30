import re
import random
import logging
import requests
from typing import Tuple, Dict, Any, List, Optional
from app.config import settings
from app.services.rules_engine import analyze_urgency
from app.services.ai_text_service import (
    classify_text_emotions,
    normalizar_grafia_ptbr,
    termo_contido_fuzzy,
    remover_acentos
)

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
    "mal_estar_geral": {
        "resumo": "ACOLHIMENTO AO MAL-ESTAR E INDISPOSIÇÃO GESTACIONAL (FEBRASGO/MS): Sentir-se mal, indisposta, fraca ou com moleza no corpo é frequente na gestação devido à vasodilatação periférica (que diminui a pressão), ao consumo glicêmico fetal e às intensas variações hormonais.",
        "cuidados": [
            "Repouso imediato no lado esquerdo: Deite-se preferencialmente sobre o decúbito lateral esquerdo para desobstruir a veia cava e restabelecer o fluxo ideal de sangue e oxigênio para você e seu bebê;",
            "Hidratação fracionada: Tome pequenos goles de água fresca, água de coco ou soro caseiro ao longo do dia;",
            "Aporte de energia: Se estiver sem comer há mais de 2 a 3 horas, consuma algo leve (como uma fruta, biscoito de água e sal ou torrada) para estabilizar a glicemia;",
            "Ambiente fresco e arejado: Permaneça em local ventilado e afrouxe roupas que apertem a cintura e o abdômen;",
            "Aferição dos sinais vitais: Se possível, meça sua pressão arterial (o esperado é manter-se abaixo de 140x90 mmHg) e temperatura."
        ],
        "orientacao": "Sinais de Alerta: Caso o mal-estar seja súbito ou venha acompanhado de febre, dor forte na cabeça ou na boca do estômago, visão embaçada, falta de ar ou sangramento, procure imediatamente o pronto atendimento obstétrico."
    },
    "medicacao_segura": {
        "resumo": "SEGURANÇA FARMACOLÓGICA E MEDICAMENTOS NA GESTAÇÃO (Res. CFM 2.454/2026): Durante a gravidez, diversas substâncias atravessam a barreira placentária. Por isso, a automedicação é terminantemente contraindicada.",
        "cuidados": [
            "Evite estritamente anti-inflamatórios (como ibuprofeno, diclofenaco, cetoprofeno, nimesulida) e aspirina sem prescrição obstétrica formal, devido a riscos cardiovasculares e renais fetais;",
            "Para alívio de dor comum ou febre: analgésicos como paracetamol costumam ser de primeira linha em obstetrícia, porém sempre na dosagem e intervalo autorizados pelo seu médico de pré-natal;",
            "Atenção aos chás caseiros: evite infusões de canela, boldo, hibisco, carqueja, poejo e arruda (que estimulam contrações uterinas). Prefira chá suave de camomila ou erva-cidreira;",
            "Nunca interrompa nem tome remédios por conta própria sem antes dialogar com sua equipe de saúde."
        ],
        "orientacao": "Se estiver sentindo dor aguda ou febre acima de 37,8°C, entre em contato imediatamente com sua equipe de pré-natal ou dirija-se à emergência obstétrica."
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
    "medo_parto": {
        "resumo": "ACOLHIMENTO AO MEDO DO PARTO E MANEJO DA DOR (FEBRASGO/OMS): O medo da dor do parto é um sentimento humano e frequente.",
        "cuidados": [
            "Métodos não farmacológicos de alívio: banhos mornos de chuveiro ou banheira, massagens lombares, respiração calma e uso da bola de pilates;",
            "Analgesia farmacológica: direito da gestante em ambiente hospitalar, garantindo alívio seguro sempre que solicitado;",
            "Elaboração do Plano de Parto no pré-natal para alinhar expectativas com a equipe;",
            "Presença de acompanhante de livre escolha para suporte emocional contínuo."
        ],
        "orientacao": "Converse abertamente com seu obstetra sobre suas dúvidas e opções de alívio de dor disponíveis na maternidade escolhida."
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

def _detectar_saudacao(texto: str) -> bool:
    patterns = [
        r"^(oi|ol[aá]|bom dia|boa tarde|boa noite|oie|opa|e a[ií])\b",
        r"\b(tudo bem|como vai|como est[aá]|quem [eé] voc[eê]|o que voc[eê] faz|como voc[eê] funciona|ajuda)\b"
    ]
    return any(re.search(p, texto, re.IGNORECASE) for p in patterns)

def _construir_resposta_saudacao(texto: str, nome_gestante: Optional[str] = None) -> str:
    primeiro_nome = nome_gestante.strip().split()[0] if nome_gestante else ""
    vocativo = f", {primeiro_nome}" if primeiro_nome else ""
    saudacoes = [
        f"Olá{vocativo}! Tudo bem? Que bom falar com você! Como você e seu bebê estão se sentindo hoje? Se tiver qualquer dúvida, desconforto ou só quiser conversar, estou por aqui com muito carinho para te ouvir.",
        f"Oi{vocativo}! Que alegria ter você aqui. Como tem sido o seu dia? Me conte como você está se sentindo hoje, tanto física quanto emocionalmente.",
        f"Olá{vocativo}! Fico muito feliz em te acolher. Como você está passando hoje? Se estiver sentindo qualquer coisa diferente ou precisar de orientações para a sua gestação, estou aqui ao seu lado!"
    ]
    return random.choice(saudacoes)

def _buscar_tema_clinico(texto: str) -> Optional[str]:
    """
    Busca o tema clínico correspondente no conhecimento FEBRASGO/MS,
    com suporte robusto a erros de digitação, grafias fonéticas e linguagem coloquial.
    """
    texto_norm = normalizar_grafia_ptbr(texto)

    regras = {
        "toxoplasmose": [
            r"toxoplasmose", r"gato", r"areia de gato", r"caixa de areia", r"carne crua", r"hortali[çc]a"
        ],
        "enjoo_azia": [
            r"enjoo", r"enjouo", r"enjoada", r"enjoando", r"nausea", r"vomito", r"vomitando",
            r"vomitei", r"azia", r"queima[çc][aã]o", r"refluxo", r"est[oô]mago embrulhado",
            r"est[oô]mago ruim", r"ansia", r"anseia", r"azia terr[ií]vel"
        ],
        "mal_estar_geral": [
            r"sentindo mal", r"sentindo mau", r"passando mal", r"passando mau", r"estou mal",
            r"estou mau", r"to mal", r"to mau", r"me sinto mal", r"me sinto mau", r"indispost",
            r"moleza", r"fraca", r"corpo ruim", r"pessim[ao]", r"nao estou bem", r"nao to bem",
            r"mal estar", r"mau estar", r"fraqueza"
        ],
        "medicacao_segura": [
            r"posso tomar", r"remedio", r"medicamento", r"paracetamol", r"dipirona", r"buscopan",
            r"ibuprofeno", r"dorflex", r"tomar comprimido", r"qual remedio", r"ch[aá] de", r"automedica"
        ],
        "movimentos_fetais": [
            r"mexer", r"mexendo", r"chute", r"chutando", r"movimento.*beb[eê]", r"parou de mexer",
            r"beb[eê].*n[aã]o mexe", r"mexeu pouco", r"mecher", r"mecheu", r"parou de mecher"
        ],
        "alimentacao": [
            r"alimenta[çc][aã]o", r"alimentar", r"comer", r"almo[çc]o", r"jantar", r"caf[eé] da manh[aã]",
            r"dieta", r"gr[aá]vida pode comer", r"caf[eé]", r"peixe cru", r"sushi", r"frutas",
            r"peso", r"engordar", r"refrigerante", r"ch[aá]", r"nutri[çc][aã]o", r"comida"
        ],
        "dores_corpo": [
            r"dor nas costas", r"dor lombar", r"dor no p[eé] da barriga", r"c[oó]lica", r"dor p[eé]lvica",
            r"ci[aá]tico", r"dor na virilha", r"dor muscular", r"pontada na barriga", r"barriga",
            r"bariga", r"doendo", r"duendo", r"colica"
        ],
        "sono_cansaco": [
            r"sono", r"ins[oô]nia", r"cansa[çc]o", r"fadiga", r"posi[çc][aã]o de dormir",
            r"dormir de bru[çc]os", r"dormir de lado", r"lado esquerdo", r"muito sono", r"cansad", r"exaust"
        ],
        "medo_parto": [
            r"medo.*parto", r"parto.*medo", r"parto.*doer", r"parto.*doi", r"parto.*dor",
            r"dor.*parto", r"medo da dor", r"medo.*ces[aá]rea", r"medo.*normal"
        ],
        "trabalho_parto": [
            r"trabalho de parto", r"contra[çc][oõ]es", r"contra[çc][aã]o", r"dilata[çc][aã]o",
            r"tamp[aã]o mucoso", r"parto normal", r"ces[aá]rea", r"plano de parto", r"bolsa estourou",
            r"rompeu a bolsa", r"bolsa furou", r"bolsa estorou"
        ],
        "pressao_edema": [
            r"press[aã]o", r"hipertens[aã]o", r"pr[eé]-ecl[aâ]mpsia", r"inchada", r"incha[çc]o",
            r"p[eé]s inchados", r"pernas inchadas", r"press[aã]o alta", r"edema", r"pressao",
            r"precao", r"inchad", r"inxad"
        ],
        "saude_emocional": [
            r"ansiedade", r"ansiosa", r"medo", r"nervosa", r"preocupada", r"choro", r"triste",
            r"estresse", r"depress[aã]o", r"puerp[eé]rio", r"solid[aã]o", r"ang[uú]stia"
        ],
        "amamentacao": [
            r"amamenta[çc][aã]o", r"amamentar", r"leite materno", r"peito", r"bico do peito",
            r"colostro", r"rachadura no peito", r"fissura mamilar", r"livre demanda"
        ],
        "vacinas_exames": [
            r"vacina", r"vacinas", r"dtpa", r"influenza", r"hepatite", r"ultrassom",
            r"morfol[oó]gico", r"glicemia", r"hemograma", r"curva glic[eê]mica", r"transluc[eê]ncia"
        ],
        "enxoval_maternidade": [
            r"mala", r"enxoval", r"bolsa da maternidade", r"o que levar", r"roupinhas", r"quarto do beb[eê]"
        ]
    }

    # 1. Correspondência direta via Regex enriquecido
    for tema, patterns in regras.items():
        if any(re.search(p, texto_norm) for p in patterns):
            return tema

    # 2. Correspondência Difusa / Margem de Erro por Palavra-chave (Fuzzy Matching)
    termos_fuzzy_temas = {
        "enjoo_azia": ["enjoo", "nausea", "vomito", "azia", "refluxo", "ansia"],
        "mal_estar_geral": ["indisposta", "moleza", "fraca", "pessima", "adoentada"],
        "medicacao_segura": ["remedio", "medicamento", "paracetamol", "dipirona", "buscopan"],
        "dores_corpo": ["colica", "lombar", "ciatico", "doendo"],
        "sono_cansaco": ["insonia", "exaustao", "fadiga", "cansaco"],
        "pressao_edema": ["inchaco", "edema", "pressao"]
    }
    for tema, termos in termos_fuzzy_temas.items():
        if termo_contido_fuzzy(texto_norm, termos, limiar=0.82):
            return tema

    return None

def _formatar_conversa_clinica_natural(tema: str, nome_gestante: Optional[str] = None) -> str:
    """
    Gera uma resposta estritamente conversacional e humanizada para o tema clínico,
    sem títulos em caixa alta, sem listas engessadas de tópicos e sem avisos legais repetitivos.
    """
    primeiro_nome = nome_gestante.strip().split()[0] if nome_gestante else ""
    vocativo = f", {primeiro_nome}" if primeiro_nome else ""

    respostas_naturais = {
        "toxoplasmose": (
            f"Oi{vocativo}! É muito compreensível ter dúvidas sobre a prevenção da **toxoplasmose gestacional**, "
            f"especialmente para quem convive com gatinhos em casa. A boa notícia é que com alguns cuidados simples "
            f"no dia a dia você e seu bebê ficam totalmente seguros!\n\n"
            f"O ponto mais importante com a alimentação é consumir apenas carnes muito bem passadas (nada de carne crua "
            f"ou malpassada), lavar muito bem verduras, legumes e frutas antes de comer, e beber sempre água tratada ou filtrada. "
            f"Em relação aos gatos, a transmissão só ocorre pelas fezes se o animal estiver contaminado. Por isso, a recomendação "
            f"é pedir para outra pessoa limpar a caixa de areia diariamente ou, se você precisar fazer isso, usar luvas descartáveis "
            f"e lavar muito bem as mãos em seguida. Você pode continuar dando carinho ao seu gatinho com total tranquilidade!\n\n"
            f"Você já fez seus exames de sangue do pré-natal para toxoplasmose? Mantenha sempre seu médico informado sobre os resultados."
        ),
        "alimentacao": (
            f"Oi{vocativo}! Cuidar da alimentação é uma das melhores maneiras de manter sua disposição e apoiar o crescimento saudável do bebê.\n\n"
            f"Uma orientação prática que ajuda bastante é fracionar as refeições em 5 a 6 porções menores ao longo do dia, "
            f"evitando sobrecarregar o estômago e mantendo sua energia estável. Vale a pena caprichar em fontes de ferro (como carnes magras, "
            f"feijões e folhas verde-escuras), combinadas com vitamina C (uma laranja ou limão) para potencializar a absorção. Mantenha "
            f"também uma boa hidratação, tomando entre 2,5 e 3 litros de água por dia.\n\n"
            f"Por segurança, evite leites e queijos não pasteurizados, carnes e peixes crus ou malcozidos e ovos com gema mole. "
            f"E suplementos como ferro e ácido fólico devem sempre seguir a orientação do seu obstetra. O que você tem preferido comer nesses dias?"
        ),
        "enjoo_azia": (
            f"Oi{vocativo}! Sei bem como a azia, a queimação e os enjoos podem incomodar nessa fase da gravidez. "
            f"No início as variações hormonais deixam o estômago mais lento, e com o tempo o crescimento do útero pressiona o estômago, "
            f"o que facilita o refluxo.\n\n"
            f"Para te ajudar a aliviar: para os enjoos, comer uma bolachinha água e sal ou torrada seca ainda na cama antes de levantar costuma ser tiro e queda! "
            f"Pequenos goles de água bem gelada ou com limão também ajudam a refrescar. Já para a azia, o segredo é não se deitar logo após comer (espere pelo menos 1 horinha), "
            f"evitar frituras, café e alimentos muito condimentados, e dormir com a cabeceira um pouquinho elevada à noite.\n\n"
            f"Como você está se sentindo agora? Tem conseguido se hidratar e comer direitinho?"
        ),
        "mal_estar_geral": (
            f"Oi{vocativo}! Sinto muito que você esteja se sentindo mais fraca ou indisposta hoje. O corpo gasta uma energia gigantesca "
            f"na gestação: a circulação muda, a pressão pode cair um pouco e a demanda metabólica é enorme, o que causa essa sensação de moleza.\n\n"
            f"Se você puder agora, deite-se confortavelmente sobre o lado esquerdo do corpo. Essa posição descomprime a veia cava e restabelece "
            f"o fluxo ideal de sangue e oxigênio para você e seu bebê. Beba pequenos goles de água fresca ou água de coco e consuma algo leve "
            f"(como uma fruta ou biscoito) para estabilizar a glicose.\n\n"
            f"Fique muito atenta: se o mal-estar vier acompanhado de febre, dor forte na cabeça ou na boca do estômago, visão embaçada ou falta de ar, "
            f"procure imediatamente o pronto atendimento da maternidade. Como você está se sentindo neste exato momento?"
        ),
        "medicacao_segura": (
            f"Oi{vocativo}! Que bom que você perguntou antes de tomar qualquer coisa. Durante a gravidez, muitas substâncias atravessam "
            f"a barreira placentária, por isso a regra mais segura é nunca se automedicar.\n\n"
            f"Anti-inflamatórios como ibuprofeno, diclofenaco, cetoprofeno e nimesulida são contraindicados sem prescrição médica formal, "
            f"devido a riscos cardiovasculares e renais para o bebê. Até mesmo certos chás caseiros (como canela, boldo, hibisco e carqueja) "
            f"devem ser evitados por estimularem contrações.\n\n"
            f"Para dores comuns ou febre, analgésicos como paracetamol costumam ser de primeira linha na obstetrícia, mas sempre na dosagem "
            f"e intervalo recomendados pelo seu médico. Você está sentindo alguma dor específica agora? Se for intensa, vale a pena entrar em contato com sua equipe."
        ),
        "movimentos_fetais": (
            f"Oi{vocativo}! Sentir o bebê se mexer é uma das maiores alegrias da gestação e um excelente indicativo de vitalidade e bem-estar fetal!\n\n"
            f"Na primeira gravidez, os movimentos costumam ser percebidos entre a 18ª e a 22ª semana. Quem já teve filhos antes pode notar um pouco mais cedo, "
            f"por volta da 16ª semana. No terceiro trimestre, o bebê já tem ciclos próprios de sono e vigília. Um momento muito gostoso para observar é após "
            f"o almoço ou jantar: deite-se confortavelmente sobre o lado esquerdo e perceba — o esperado é sentir vários movimentos em uma hora.\n\n"
            f"Caso você esteja no terceiro trimestre e note uma diminuição súbita e acentuada dos movimentos por várias horas seguidas, "
            f"é sempre prudente comparecer à maternidade para um exame de vitalidade. Como tem sido a movimentação dele por aí?"
        ),
        "dores_corpo": (
            f"Oi{vocativo}! Dores lombares, incômodos nas costas ou pontadas na lateral da barriga são muito frequentes na gestação. "
            f"Os hormônios deixam as articulações mais frouxas para acomodar o bebê e o centro de gravidade muda com o crescimento da barriga.\n\n"
            f"Para aliviar a coluna, durma de lado com um travesseiro entre os joelhos para alinhar o quadril. Banhos mornos e compressas suaves "
            f"ajudam a relaxar a musculatura, e levantar-se da cama virando de lado primeiro evita forçar o abdômen.\n\n"
            f"Apenas preste atenção se a dor tiver um padrão rítmico (contrações regulares que vão e voltam ficando mais fortes) ou vier acompanhada "
            f"de febre ou sangramento. Como está a sua dor hoje?"
        ),
        "sono_cansaco": (
            f"Oi{vocativo}! Esse cansaço é real e totalmente justificado. Gerar uma vida demanda uma quantidade imensa de energia do seu organismo, "
            f"então a sonolência é a forma do seu corpo pedir pausas para se regenerar.\n\n"
            f"Para dormir melhor, especialmente a partir do segundo trimestre, a posição mais recomendada é deitada sobre o lado esquerdo, "
            f"pois facilita a circulação da veia cava e oxigena muito bem a placenta. Usar travesseiros de apoio entre as pernas e sob a barriga alivia bastante o peso.\n\n"
            f"Tente reduzir as telas e luzes fortes um pouco antes de deitar e permita-se descansar sempre que possível. Como tem sido o seu sono ultimamente?"
        ),
        "trabalho_parto": (
            f"Oi{vocativo}! Conhecer os sinais do trabalho de parto traz muita calma e confiança para a reta final.\n\n"
            f"É muito comum sentir contrações de treinamento (as chamadas Braxton Hicks): elas são irregulares, não costumam doer muito e cedem com repouso. "
            f"Já o trabalho de parto verdadeiro traz contrações rítmicas e coordenadas (por exemplo, a cada 4 a 5 minutos, durando cerca de 1 minuto) que vão ficando "
            f"progressivamente mais fortes e não passam com o repouso.\n\n"
            f"A saída do tampão mucoso pode ocorrer dias antes e por si só não exige ida imediata. Porém, se a bolsa romper (saída contínua de líquido transparente) "
            f"ou as contrações ficarem ritmadas e intensas, vá tranquilamente para a sua maternidade de referência. Você está sentindo contrações agora?"
        ),
        "pressao_edema": (
            f"Oi{vocativo}! Cuidar da pressão arterial e observar o inchaço são cuidados essenciais durante toda a gestação.\n\n"
            f"Um inchaço leve nos pés e tornozelos no fim do dia é bem comum pelo peso do útero na circulação. Descansar com as pernas elevadas "
            f"e deitar-se sobre o lado esquerdo costuma ajudar muito no retorno venoso.\n\n"
            f"Por outro lado, fique atenta a sinais de alerta: inchaço repentino no rosto e mãos ao acordar, dor de cabeça frontal forte e persistente, "
            f"pontos brilhantes na visão ou dor intensa na boca do estômago. A pressão ideal deve manter-se abaixo de 140 por 90 mmHg. Caso meça um valor igual "
            f"ou superior a isso, ou sinta esses sintomas, vá imediatamente ao serviço de emergência obstétrica. Como está a sua pressão?"
        ),
        "saude_emocional": (
            f"Oi{vocativo}! Quero que você saiba que tudo o que você está sentindo é absolutamente legítimo e humano. A gestação traz transformações "
            f"hormonais, físicas e emocionais muito profundas, e ter momentos de insegurança, sensibilidade ou ansiedade faz parte da experiência de muitas mães.\n\n"
            f"Você não precisa carregar o mundo nas costas nem estar bem o tempo todo. Fale abertamente sobre o que sente com pessoas de sua confiança, "
            f"reserve momentos de calma para respirar fundo e não hesite em pedir apoio profissional perinatal se o desânimo estiver pesado.\n\n"
            f"Como você está se sentindo hoje? Se quiser desabafar sobre qualquer medo ou expectativa, estou aqui para te ouvir com todo carinho."
        ),
        "amamentacao": (
            f"Oi{vocativo}! A amamentação é uma parceria que você e seu bebê vão aprender juntos logo após o nascimento.\n\n"
            f"Durante a gravidez, você não precisa fazer nada agressivo: evite esfregar buchas ou usar pomadas nos mamilos, pois a própria natureza "
            f"já prepara a aréola com óleos protetores naturais. Um banho de sol matinal de alguns minutos já ajuda bastante.\n\n"
            f"O grande segredo da amamentação sem dor é a pega correta: a boquinha do bebê deve cobrir boa parte da aréola, com os lábios evertidos "
            f"(como de peixinho) e queixo encostado na mama. E nos primeiros dias o colostro é o alimento perfeito e na quantidade exata que o estômago dele precisa! "
            f"Você tem alguma dúvida específica sobre a amamentação?"
        ),
        "vacinas_exames": (
            f"Oi{vocativo}! O acompanhamento de vacinas e exames é uma forma maravilhosa de proteger a sua saúde e o futuro do seu bebê.\n\n"
            f"As vacinas recomendadas na gravidez incluem a dTpa (a partir da 20ª semana, para proteger contra coqueluche e tétano), a vacina da gripe (Influenza) "
            f"e a de Hepatite B. Já os ultrassons essenciais incluem a translucência nucal (11 a 13 semanas) e o morfológico de 2º trimestre (20 a 24 semanas), "
            f"além do rastreio de diabetes gestacional entre a 24ª e a 28ª semana.\n\n"
            f"Mantenha sempre sua Caderneta da Gestante atualizada e leve em todas as consultas. Qual é o próximo exame que você tem marcado?"
        ),
        "medo_parto": (
            f"Oi{vocativo}! É absolutamente normal e muito compreensível sentir medo da dor do parto. Quase toda mãe passa por essa preocupação em algum momento da gestação!\n\n"
            f"O mais importante é você saber que hoje em dia existem diversos recursos para o seu conforto e você não precisa passar por nada com sofrimento. "
            f"A obstetrícia moderna conta com métodos não farmacológicos excelentes (como banhos mornos de chuveiro ou banheira, massagens lombares, respiração ritmada e uso da bola de pilates), "
            f"além da analgesia de parto hospitalar, que pode ser aplicada para trazer alívio sempre que você desejar.\n\n"
            f"Montar um Plano de Parto com seu obstetra e tirar todas as suas dúvidas nas consultas ajuda imensamente a transformar esse medo em tranquilidade. Você já conversou com seu médico sobre as opções de alívio de dor no hospital onde pretende ter o bebê?"
        ),
        "enxoval_maternidade": (
            f"Oi{vocativo}! Começar a organizar a mala da maternidade traz uma sensação gostosa de aconchego para a reta final da gravidez!\n\n"
            f"Uma boa época para deixar tudo pronto é por volta da 32ª à 34ª semana. Para você, separe camisolas ou pijamas fáceis de abrir para amamentar, "
            f"sutiãs confortáveis, calcinhas pós-parto de cintura alta, produtos de higiene pessoal e seus documentos (Caderneta da Gestante, documento com foto e exames). "
            f"Para o bebê, 3 a 4 trocas de roupinhas lavadas com sabão neutro (body, calça e macacão), fraldas RN/P e paninhos de boca.\n\n"
            f"Vale a pena também conferir com a maternidade escolhida se eles têm alguma lista de recomendações específicas. Em qual semana você está agora?"
        )
    }

    if tema in respostas_naturais:
        return respostas_naturais[tema]

    dados = CONHECIMENTO_CLINICO[tema]
    return (
        f"Oi{vocativo}! Sobre {dados['resumo'].lower()}: no dia a dia, {dados['orientacao'].lower()} "
        f"Se quiser conversar mais sobre isso, me conte o que você está sentindo!"
    )

def _gerar_resposta_dinamica_ia(
    texto: str,
    scores: Dict[str, float],
    active_categories: List[str],
    nome_gestante: Optional[str] = None
) -> str:
    """
    Gera uma resposta estritamente conversacional e humanizada, baseada no estado emocional
    e físico da gestante, sem scripts prontos e sem disclaimers repetitivos.
    """
    primeiro_nome = nome_gestante.strip().split()[0] if nome_gestante else ""
    vocativo = f", {primeiro_nome}" if primeiro_nome else ""

    partes: List[str] = []
    texto_norm = normalizar_grafia_ptbr(texto)
    tem_sintoma_ou_mal_estar = (
        "sintoma_fisico" in active_categories or 
        scores.get("sintoma_fisico", 0) > 0.35 or
        bool(re.search(r'\b(mal|mau|dor|enjoo|ruim|fraca|moleza|indispost|vomit|nause)\b', texto_norm))
    )

    # 1. Empatia e Validação Emocional Baseada em IA
    if "ansiedade" in active_categories or scores.get("ansiedade", 0) > 0.35:
        partes.append(
            f"Oi{vocativo}! Sinto em suas palavras uma pontinha de preocupação ou ansiedade. "
            f"Quero te lembrar que é absolutamente normal se sentir assim: a gestação envolve expectativas, "
            f"mudanças no corpo e na rotina que mexem muito com a cabeça da gente. Respire fundo, você está fazendo um trabalho lindo."
        )
    elif "tristeza_desanimo" in active_categories or scores.get("tristeza_desanimo", 0) > 0.35:
        partes.append(
            f"Oi{vocativo}! Sinto muito que você esteja se sentindo mais para baixo ou cansada hoje. "
            f"Nem todos os dias da gestação são leves, e reconhecer seu cansaço sem cobranças é fundamental. "
            f"Permita-se descansar e acolher o seu momento."
        )
    elif "estresse_sobrecarga" in active_categories or scores.get("estresse_sobrecarga", 0) > 0.35:
        partes.append(
            f"Oi{vocativo}! Entendo perfeitamente essa sensação de sobrecarga. Gerar uma vida já consome muita energia, "
            f"e somar isso às responsabilidades diárias às vezes pesa bastante. Tente desacelerar um pouquinho hoje e cuidar de você."
        )
    elif "medo_inseguranca" in active_categories or scores.get("medo_inseguranca", 0) > 0.35:
        partes.append(
            f"Oi{vocativo}! A insegurança diante de novos sinais do corpo é super comum. "
            f"Você não está sozinha nessa caminhada, e conversar sobre o que você está sentindo é a melhor maneira de acalmar o coração."
        )
    elif "bem_estar" in active_categories and not tem_sintoma_ou_mal_estar:
        partes.append(
            f"Que notícia maravilhosa{vocativo}! Fico muito contente em saber que você está se sentindo bem e em sintonia com o seu corpo e o seu bebê."
        )

    # 2. Avaliação de Sintomas Físicos ou Mal-Estar
    if tem_sintoma_ou_mal_estar:
        partes.append(
            "Em relação ao desconforto físico que você comentou: se for algo leve e passageiro, pequenas medidas como repousar sobre o lado esquerdo, "
            "beber bastante água e se alimentar de forma leve costumam aliviar muito.\n\n"
            "Mas se o sintoma for intenso, constante ou vier acompanhado de febre, dor forte ou sangramento, não hesite em procurar logo seu obstetra ou a maternidade."
        )

    # 3. Orientação Geral e Fechamento Conversacional
    if not partes:
        partes.append(
            f"Olá{vocativo}! Estou por aqui para te acompanhar e te apoiar em cada etapa da sua gestação.\n\n"
            f"Me conte um pouco mais: você está sentindo algum desconforto físico, tem dúvidas sobre consultas ou exames, "
            f"ou gostaria apenas de desabafar sobre como está sendo o seu dia? Estou aqui para te ouvir!"
        )
    else:
        partes.append(
            "Se quiser me contar mais detalhes de há quanto tempo está sentindo isso ou como está sua rotina, "
            "podemos continuar conversando com calma. Como você está agora?"
        )

    return "\n\n".join(partes)

SYSTEM_PROMPT_NYMPHIA = (
    "Você é a Nymphia, uma assistente virtual e companheira carinhosa, empática e acolhedora para gestantes, "
    "especializada em saúde materno-fetal fundamentada nas diretrizes da FEBRASGO (Federação Brasileira das "
    "Associações de Ginecologia e Obstetrícia) e do Ministério da Saúde do Brasil.\n\n"
    "DIRETRIZES FUNDAMENTAIS DE CONVERSAÇÃO:\n"
    "1. TOM HUMANO E CONVERSACIONAL: Converse com a gestante em português brasileiro com tom extremamente afetuoso, "
    "acolhedor, próximo e natural, como uma doula ou amiga profissional da saúde. Responda diretamente ao que ela disser.\n"
    "2. SEM SCRIPTS OU MENUS ROBÓTICOS: NUNCA envie respostas prontas engessadas, scripts automáticos ('Aqui você pode:'), "
    "nem listas de tópicos pré-formatadas. Se ela te der um 'oi' ou 'tudo bem', apenas cumprimente com carinho e pergunte como ela está.\n"
    "3. SEM AVISOS LEGAIS REPETITIVOS: Não fique mencionando resoluções (CFM), leis ou disclaimers legais repetitivos a cada resposta. "
    "A interface do aplicativo já possui o aviso permanente sobre apoio informativo.\n"
    "4. CUIDADO REAL E EMBASADO: Ofereça orientações preventivas e práticas baseadas na obstetrícia humanizada. Não dê diagnósticos "
    "conclusivos nem prescreva dosagens de remédios, mas responda de forma genuína, esclarecedora e tranquilizadora.\n"
    "5. OBJETIVIDADE E FLUIDEZ: Mantenha as respostas fluídas, carinhosas e em parágrafos conversacionais (2 a 3 parágrafos)."
)

def _consultar_gemini(
    texto: str,
    historico: Optional[List[Dict[str, str]]] = None,
    nome_gestante: Optional[str] = None,
    tema_clinico: Optional[str] = None,
    active_categories: Optional[List[str]] = None
) -> Optional[str]:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key or api_key == "COLE_SUA_CHAVE_AQUI" or len(api_key) < 10:
        return None

    # Contexto clínico e humano injetado de forma transparente para guiar o raciocínio da IA
    contexto_parts = []
    if nome_gestante:
        primeiro_nome = nome_gestante.strip().split()[0]
        contexto_parts.append(f"Nome da gestante: {primeiro_nome}")
    if active_categories:
        contexto_parts.append(f"Estado emocional detectado: {', '.join(active_categories)}")
    if tema_clinico and tema_clinico in CONHECIMENTO_CLINICO:
        info = CONHECIMENTO_CLINICO[tema_clinico]
        contexto_parts.append(
            f"Referência clínica FEBRASGO/MS: {info['resumo']}. Cuidados sugeridos: {'; '.join(info['cuidados'])}. "
            f"Orientação: {info['orientacao']}. Incorpore com suas próprias palavras na conversa, sem fazer listas mecânicas."
        )

    contexto_str = ""
    if contexto_parts:
        contexto_str = f"\n\n[Contexto de apoio: {' | '.join(contexto_parts)}]"

    prompt_atual = f"{texto}{contexto_str}"

    # Monta histórico multi-turn no formato do Gemini API v1beta
    contents = []
    if historico:
        for item in historico[-6:]:
            role = "user" if item.get("role") in ["user", "gestante"] else "model"
            msg_text = item.get("text") or item.get("conteudo") or ""
            if msg_text.strip():
                if contents and contents[-1]["role"] == role:
                    contents[-1]["parts"][0]["text"] += f"\n{msg_text.strip()}"
                else:
                    contents.append({"role": role, "parts": [{"text": msg_text.strip()}]})

    if contents and contents[-1]["role"] == "user":
        contents[-1]["parts"][0]["text"] += f"\n{prompt_atual}"
    else:
        contents.append({"role": "user", "parts": [{"text": prompt_atual}]})

    modelos = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
    for modelo in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT_NYMPHIA}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands and "content" in cands[0] and "parts" in cands[0]["content"]:
                    texto_gerado = cands[0]["content"]["parts"][0].get("text", "").strip()
                    if texto_gerado:
                        return texto_gerado
            elif resp.status_code == 402:
                logger.info("Gemini API: cota pré-paga esgotada (402), verificando provedores adicionais ou motor local.")
                break
            else:
                logger.info(f"Gemini API ({modelo}) retornou status {resp.status_code}.")
        except Exception as ex:
            logger.info(f"Falha de conexão com Gemini ({modelo}): {ex}")
    return None

def _consultar_openai_compativel(
    endpoint: str,
    api_key: str,
    modelo: str,
    texto: str,
    historico: Optional[List[Dict[str, str]]] = None,
    nome_gestante: Optional[str] = None,
    tema_clinico: Optional[str] = None,
    active_categories: Optional[List[str]] = None
) -> Optional[str]:
    if not api_key or len(api_key.strip()) < 5:
        return None

    contexto_parts = []
    if nome_gestante:
        contexto_parts.append(f"Nome da gestante: {nome_gestante.strip().split()[0]}")
    if active_categories:
        contexto_parts.append(f"Estado emocional detectado: {', '.join(active_categories)}")
    if tema_clinico and tema_clinico in CONHECIMENTO_CLINICO:
        info = CONHECIMENTO_CLINICO[tema_clinico]
        contexto_parts.append(
            f"Referência clínica FEBRASGO/MS: {info['resumo']}. Cuidados sugeridos: {'; '.join(info['cuidados'])}. "
            f"Orientação: {info['orientacao']}. Incorpore com suas próprias palavras na conversa."
        )

    prompt_atual = texto
    if contexto_parts:
        prompt_atual = f"{texto}\n\n[Contexto de apoio: {' | '.join(contexto_parts)}]"

    messages = [{"role": "system", "content": SYSTEM_PROMPT_NYMPHIA}]
    if historico:
        for item in historico[-6:]:
            role = "user" if item.get("role") in ["user", "gestante"] else "assistant"
            msg_text = item.get("text") or item.get("conteudo") or ""
            if msg_text.strip():
                messages.append({"role": role, "content": msg_text.strip()})
    messages.append({"role": "user", "content": prompt_atual})

    try:
        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json"
            },
            json={
                "model": modelo,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0] and "content" in choices[0]["message"]:
                res_text = choices[0]["message"]["content"].strip()
                if res_text:
                    return res_text
    except Exception as ex:
        logger.info(f"Falha de conexão com endpoint OpenAI compatível ({modelo}): {ex}")
    return None

def _consultar_api_llm(
    texto: str,
    historico: Optional[List[Dict[str, str]]] = None,
    nome_gestante: Optional[str] = None,
    tema_clinico: Optional[str] = None,
    active_categories: Optional[List[str]] = None
) -> Optional[str]:
    """
    Tenta consultar a API de IA Generativa com fallback em cascata (Gemini -> Groq -> OpenRouter -> OpenAI).
    """
    # 1. Google Gemini
    res_gemini = _consultar_gemini(texto, historico, nome_gestante, tema_clinico, active_categories)
    if res_gemini:
        return res_gemini

    # 2. Groq (se configurado)
    if getattr(settings, "GROQ_API_KEY", None):
        res_groq = _consultar_openai_compativel(
            "https://api.groq.com/openai/v1/chat/completions",
            settings.GROQ_API_KEY,
            "llama-3.3-70b-versatile",
            texto, historico, nome_gestante, tema_clinico, active_categories
        )
        if res_groq:
            return res_groq

    # 3. OpenRouter (se configurado)
    if getattr(settings, "OPENROUTER_API_KEY", None):
        res_openrouter = _consultar_openai_compativel(
            "https://openrouter.ai/api/v1/chat/completions",
            settings.OPENROUTER_API_KEY,
            "meta-llama/llama-3.3-70b-instruct",
            texto, historico, nome_gestante, tema_clinico, active_categories
        )
        if res_openrouter:
            return res_openrouter

    # 4. OpenAI (se configurado)
    if getattr(settings, "OPENAI_API_KEY", None):
        res_openai = _consultar_openai_compativel(
            "https://api.openai.com/v1/chat/completions",
            settings.OPENAI_API_KEY,
            "gpt-4o-mini",
            texto, historico, nome_gestante, tema_clinico, active_categories
        )
        if res_openai:
            return res_openai

    return None

def generate_chat_response(
    message: str,
    recusa_ia: bool = False,
    historico: Optional[List[Dict[str, str]]] = None,
    nome_gestante: Optional[str] = None
) -> Tuple[str, bool, str]:
    """
    Gera resposta conversacional inteligente, acolhedora e segura:
    1. Triage de Emergência: Identifica sinais de alarme obstétrico imediatamente (sem delay de LLM).
    2. Consulta de IA Generativa Real: Prioridade total para a API LLM (Gemini / Provedores),
       enviando contexto da gestante, histórico da conversa e referências clínicas com tom acolhedor.
    3. Fallback Conversacional Natural: Se a API estiver sem cota ou indisponível, responde
       com linguagem 100% natural, humana e acolhedora, SEM scripts prontos, SEM menus engessados
       e SEM repetição exaustiva de artigos e leis.
    """
    texto_limpo = message.strip()

    # 1. Checagem de Urgência Obstétrica Absoluta
    is_urgent, alerts, urgency_guidance = analyze_urgency(texto_limpo)
    if is_urgent:
        return urgency_guidance, True, "regras_urgencia"

    # Se a paciente optou por desativar IA generativa
    if recusa_ia:
        scores, active_categories = classify_text_emotions(texto_limpo)
        if _detectar_saudacao(texto_limpo) and len(texto_limpo.split()) <= 7:
            return _construir_resposta_saudacao(texto_limpo, nome_gestante), False, "assistente_nymphia"
        tema_clinico = _buscar_tema_clinico(texto_limpo)
        if tema_clinico and tema_clinico in CONHECIMENTO_CLINICO:
            return _formatar_conversa_clinica_natural(tema_clinico, nome_gestante), False, "base_clinica_ia"
        return _gerar_resposta_dinamica_ia(texto_limpo, scores, active_categories, nome_gestante), False, "bertimbau_ia"

    # 2. IA Conversacional Real: Usa e abusa da API com histórico e contexto
    scores, active_categories = classify_text_emotions(texto_limpo)
    tema_detectado = _buscar_tema_clinico(texto_limpo)

    resposta_api = _consultar_api_llm(
        texto=texto_limpo,
        historico=historico,
        nome_gestante=nome_gestante,
        tema_clinico=tema_detectado,
        active_categories=active_categories
    )
    if resposta_api:
        return resposta_api, False, "gemini_ia"

    # 3. Fallback Conversacional Humanizado (Sem scripts rígidos e sem disclaimers repetitivos)
    if _detectar_saudacao(texto_limpo) and len(texto_limpo.split()) <= 7:
        return _construir_resposta_saudacao(texto_limpo, nome_gestante), False, "assistente_nymphia"

    if tema_detectado and tema_detectado in CONHECIMENTO_CLINICO:
        return _formatar_conversa_clinica_natural(tema_detectado, nome_gestante), False, "base_clinica_ia"

    return _gerar_resposta_dinamica_ia(texto_limpo, scores, active_categories, nome_gestante), False, "bertimbau_ia"

