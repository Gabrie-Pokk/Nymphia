"""
Serviço Clínico de Antropometria Materna e Ganho Ponderal Gestacional
Baseado nas diretrizes do Ministério da Saúde, FEBRASGO e Institute of Medicine (IOM / OMS).
Curvas de Atalah e Altura Uterina (P10-P90).
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date

# Tabela da Curva de Atalah: Pontos de corte de IMC gestacional por semana
# (Ministério da Saúde - Atenção ao Pré-Natal de Baixo Risco)
# Formato: semana: (limite_baixo_peso, limite_adequado, limite_sobrepeso)
# Se IMC < limite_baixo_peso: Baixo Peso
# Se limite_baixo_peso <= IMC < limite_adequado: Adequado / Eutrófica
# Se limite_adequado <= IMC < limite_sobrepeso: Sobrepeso
# Se IMC >= limite_sobrepeso: Obesidade
CURVA_ATALAH = {
    6:  (19.9, 24.9, 30.0),
    7:  (20.0, 25.0, 30.0),
    8:  (20.1, 25.0, 30.1),
    9:  (20.2, 25.1, 30.1),
    10: (20.2, 25.2, 30.2),
    11: (20.3, 25.3, 30.2),
    12: (20.4, 25.4, 30.3),
    13: (20.6, 25.6, 30.4),
    14: (20.7, 25.7, 30.5),
    15: (20.8, 25.8, 30.6),
    16: (21.0, 25.9, 30.7),
    17: (21.1, 26.0, 30.8),
    18: (21.2, 26.1, 30.9),
    19: (21.4, 26.2, 31.0),
    20: (21.5, 26.3, 31.1),
    21: (21.7, 26.4, 31.2),
    22: (21.8, 26.6, 31.3),
    23: (22.0, 26.7, 31.4),
    24: (22.2, 26.8, 31.5),
    25: (22.3, 26.9, 31.6),
    26: (22.5, 27.0, 31.7),
    27: (22.7, 27.2, 31.8),
    28: (22.8, 27.3, 31.9),
    29: (23.0, 27.4, 32.0),
    30: (23.2, 27.6, 32.1),
    31: (23.4, 27.7, 32.2),
    32: (23.6, 27.9, 32.3),
    33: (23.8, 28.0, 32.4),
    34: (23.9, 28.2, 32.5),
    35: (24.1, 28.3, 32.6),
    36: (24.3, 28.5, 32.7),
    37: (24.5, 28.7, 32.8),
    38: (24.7, 28.8, 32.9),
    39: (24.8, 28.9, 33.0),
    40: (24.9, 29.0, 33.1),
    41: (25.0, 29.1, 33.2),
    42: (25.0, 29.2, 33.2)
}

# Tabela de Altura Uterina por Idade Gestacional (Ministério da Saúde - Percentis 10 e 90 em centímetros)
# semana: (p10, p90)
CURVA_ALTURA_UTERINA = {
    13: (8.0, 12.0),
    14: (9.0, 13.0),
    15: (10.0, 14.5),
    16: (11.0, 16.0),
    17: (12.0, 17.0),
    18: (13.5, 18.5),
    19: (15.0, 20.0),
    20: (16.0, 21.0),
    21: (17.0, 22.0),
    22: (18.0, 23.0),
    23: (19.0, 24.5),
    24: (20.0, 25.5),
    25: (21.0, 26.5),
    26: (22.0, 27.5),
    27: (23.0, 28.5),
    28: (24.0, 29.5),
    29: (25.0, 30.5),
    30: (26.0, 31.5),
    31: (27.0, 32.5),
    32: (28.0, 33.5),
    33: (29.0, 34.5),
    34: (30.0, 35.5),
    35: (31.0, 36.0),
    36: (31.5, 36.5),
    37: (32.0, 37.0),
    38: (32.5, 37.5),
    39: (33.0, 38.0),
    40: (33.0, 38.5)
}

def calcular_imc(peso_kg: float, altura_cm: float) -> Optional[float]:
    """Calcula o Índice de Massa Corporal (IMC = kg / m²)."""
    if not peso_kg or not altura_cm or altura_cm <= 0 or peso_kg <= 0:
        return None
    altura_m = altura_cm / 100.0
    return round(peso_kg / (altura_m * altura_m), 2)

def classificar_imc_pre_gestacional(imc: float) -> Dict[str, Any]:
    """
    Classifica o estado nutricional pré-gestacional segundo IOM/OMS e Ministério da Saúde,
    retornando as faixas de ganho de peso recomendadas para toda a gravidez.
    """
    if imc < 18.5:
        categoria = "Baixo Peso"
        ganho_total_min = 12.5
        ganho_total_max = 18.0
        ganho_semanal_2_3_tri = 0.51
        riscos = "Risco elevado de prematuridade, recém-nascido pequeno para idade gestacional (PIG) e baixo peso ao nascer."
        meta_descricao = "Ganho total recomendado entre 12,5 kg e 18,0 kg (~0,5 kg por semana no 2º e 3º trimestres)."
    elif 18.5 <= imc <= 24.9:
        categoria = "Adequado (Eutrófica)"
        ganho_total_min = 11.5
        ganho_total_max = 16.0
        ganho_semanal_2_3_tri = 0.42
        riscos = "Menor índice de complicações obstétricas maternas e neonatais."
        meta_descricao = "Ganho total recomendado entre 11,5 kg e 16,0 kg (~0,4 kg por semana no 2º e 3º trimestres)."
    elif 25.0 <= imc <= 29.9:
        categoria = "Sobrepeso"
        ganho_total_min = 7.0
        ganho_total_max = 11.5
        ganho_semanal_2_3_tri = 0.28
        riscos = "Aumento do risco de diabetes gestacional, hipertensão gestacional e macrossomia fetal."
        meta_descricao = "Ganho total recomendado entre 7,0 kg e 11,5 kg (~0,3 kg por semana no 2º e 3º trimestres)."
    else:
        categoria = "Obesidade"
        ganho_total_min = 5.0
        ganho_total_max = 9.0
        ganho_semanal_2_3_tri = 0.22
        riscos = "Risco aumentado de pré-eclâmpsia, diabetes gestacional, parto cesáreo e distócia de ombro."
        meta_descricao = "Ganho total recomendado entre 5,0 kg e 9,0 kg (~0,2 kg por semana no 2º e 3º trimestres)."

    return {
        "imc": imc,
        "categoria": categoria,
        "ganho_total_min": ganho_total_min,
        "ganho_total_max": ganho_total_max,
        "ganho_semanal_2_3_tri": ganho_semanal_2_3_tri,
        "meta_descricao": meta_descricao,
        "riscos_associados": riscos
    }

def classificar_curva_atalah(semana: int, imc_atual: float) -> Dict[str, Any]:
    """
    Avalia o IMC da gestante para a semana gestacional atual segundo a Curva de Atalah
    (adotada oficialmente pelo Ministério da Saúde do Brasil).
    """
    semana_clamp = max(6, min(42, semana))
    limites = CURVA_ATALAH.get(semana_clamp, (21.5, 26.3, 31.1))
    baixo_lim, adequado_lim, sobrepeso_lim = limites

    if imc_atual < baixo_lim:
        diagnostico = "Baixo Peso Gestacional"
        cor = "#E67E22" # Laranja
        orientacao = "Seu IMC está abaixo do esperado para esta semana. É fundamental enriquecer o valor calórico e nutritivo das refeições com o apoio do nutricionista/obstetra."
    elif baixo_lim <= imc_atual < adequado_lim:
        diagnostico = "Adequado (Eutrófica)"
        cor = "#27AE60" # Verde
        orientacao = "Parabéns! Seu peso está na faixa ideal esperada para esta semana gestacional, protegendo o desenvolvimento fetal e seu bem-estar."
    elif adequado_lim <= imc_atual < sobrepeso_lim:
        diagnostico = "Sobrepeso Gestacional"
        cor = "#F39C12" # Âmbar
        orientacao = "Seu IMC está ligeiramente acima da faixa esperada para a semana. Priorize alimentos integrais, vegetais e caminhadas leves, evitando doces e frituras."
    else:
        diagnostico = "Obesidade Gestacional"
        cor = "#C0392B" # Vermelho suave
        orientacao = "Seu ganho de peso está acima da curva ideal. Não faça dietas restritivas por conta própria; converse com seu obstetra para ajustar calorias e acompanhar a pressão arterial."

    return {
        "semana": semana,
        "imc_atual": imc_atual,
        "diagnostico": diagnostico,
        "cor": cor,
        "limite_baixo": baixo_lim,
        "limite_adequado": adequado_lim,
        "limite_sobrepeso": sobrepeso_lim,
        "orientacao": orientacao
    }

def avaliar_altura_uterina(semana: int, au_cm: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    Avalia a Altura Uterina (AU) em centímetros em relação à curva P10-P90 do Ministério da Saúde.
    """
    if au_cm is None or semana < 13:
        return None

    semana_clamp = max(13, min(40, semana))
    p10, p90 = CURVA_ALTURA_UTERINA.get(semana_clamp, (semana_clamp - 2, semana_clamp + 2))

    if au_cm < p10:
        status = "Abaixo do Percentil 10"
        cor = "#E67E22"
        detalhe = "A medida uterina está menor do que a média esperada para a semana. O obstetra pode solicitar uma ultrassonografia com Doppler para avaliar o crescimento fetal e o volume de líquido amniótico."
    elif p10 <= au_cm <= p90:
        status = "Adequada (P10 - P90)"
        cor = "#27AE60"
        detalhe = "Crescimento uterino perfeitamente compatível com a idade gestacional."
    else:
        status = "Acima do Percentil 90"
        cor = "#F39C12"
        detalhe = "A medida está superior ao percentil 90. Pode indicar gestação múltipla, feto com crescimento acentuado (macrossomia) ou maior quantidade de líquido amniótico (polidrâmnio)."

    return {
        "semana": semana,
        "altura_uterina_cm": au_cm,
        "p10": p10,
        "p90": p90,
        "status": status,
        "cor": cor,
        "detalhe": detalhe
    }

def obter_guia_educativo_antropometria() -> Dict[str, Any]:
    """
    Retorna guia educativo completo e desmistificador sobre ganho de peso,
    nutrição e composição corporal durante a gestação.
    """
    return {
        "distribuicao_peso_fetal": [
            {"componente": "Bebê ao nascer", "media_kg": "3,0 a 3,5 kg", "descricao": "Peso médio do recém-nascido a termo"},
            {"componente": "Placenta", "media_kg": "0,6 a 0,8 kg", "descricao": "Órgão vital de oxigenação e nutrição fetal"},
            {"componente": "Líquido Amniótico", "media_kg": "0,8 a 1,0 kg", "descricao": "Proteção mecânica e térmica do bebê"},
            {"componente": "Aumento do Útero", "media_kg": "0,9 a 1,1 kg", "descricao": "Hipertrofia e crescimento muscular uterino"},
            {"componente": "Aumento das Mamas", "media_kg": "0,4 a 0,5 kg", "descricao": "Glândulas e tecido adiposo para amamentação"},
            {"componente": "Volume de Sangue Materno", "media_kg": "1,2 a 1,8 kg", "descricao": "Expansão de até 45% do volume plasmático"},
            {"componente": "Líquido Extracelular (Retenção)", "media_kg": "1,2 a 1,6 kg", "descricao": "Hidratação tecidual natural da gravidez"},
            {"componente": "Reservas de Gordura Materna", "media_kg": "2,5 a 4,0 kg", "descricao": "Energia biológica para o parto e lactação"}
        ],
        "mitos_e_verdades": [
            {
                "mito": "A gestante precisa 'comer por dois'.",
                "fato": "Mito! No 1º trimestre, o gasto calórico mal se altera. No 2º e 3º trimestres, o aumento necessário é de apenas 300 a 450 kcal por dia — o que equivale a 1 iogurte natural com frutas e castanhas. O mais importante é a DENSIDADE NUTRICIONAL, não a quantidade de calorias vazias."
            },
            {
                "mito": "Não se pode engordar nada se já estiver com sobrepeso.",
                "fato": "Mito! Mesmo mulheres com obesidade ou sobrepeso precisam ganhar entre 5 kg e 11,5 kg para permitir a formação adequada da placenta, líquido amniótico e crescimento do feto. Dietas de fome ou restrição severa de carboidratos são contraindicadas na gravidez."
            },
            {
                "mito": "Inchaço repentino no rosto e mãos é apenas 'retenção normal'.",
                "fato": "Alerta! Inchaço súbito (ganho de mais de 1 kg em poucos dias), especialmente na face e mãos ao acordar, pode ser sinal de pré-eclâmpsia e exige medição imediata da pressão arterial."
            },
            {
                "mito": "Depois do parto o peso não volta nunca mais.",
                "fato": "Mito! Com o parto, cerca de 5 a 6 kg são perdidos imediatamente (bebê, placenta e líquido). Nas semanas seguintes, o excesso de líquido é eliminado pela urina e a amamentação consome cerca de 500 kcal diárias adicionais."
            }
        ],
        "micronutrientes_essenciais": [
            {
                "nutriente": "Ácido Fólico (Vitamina B9)",
                "importancia": "Essencial para o fechamento do tubo neural do feto (prevenção de anencefalia e espinha bífida). Deve ser suplementado desde o pré-concepcional até a 12ª semana.",
                "fontes_alimentos": "Espinafre, couve, brócolis, feijão, lentilha, gema de ovo e cereais fortificados."
            },
            {
                "nutriente": "Ferro Quelato / Sulfato Ferroso",
                "importancia": "Prevenção da anemia ferropriva materna e suporte ao transporte maciço de oxigênio pela hemoglobina para a placenta.",
                "fontes_alimentos": "Carnes magras, feijões, folhas verdes escuras. Dica de ouro: consuma com fonte de Vitamina C (limão, laranja) e evite laticínios/café na mesma refeição para não inibir a absorção."
            },
            {
                "nutriente": "Cálcio",
                "importancia": "Mineralização do esqueleto fetal, formação dos brotos dentários e modulação da pressão arterial materna (prevenção de pré-eclâmpsia).",
                "fontes_alimentos": "Leite e derivados pasteurizados, gergelim, tofu, semente de chia e vegetais verde-escuros."
            },
            {
                "nutriente": "Ômega-3 (DHA)",
                "importancia": "Ácido graxo estrutural indispensável para o desenvolvimento neurológico, córtex cerebral e retina do feto.",
                "fontes_alimentos": "Sardinha, salmão bem cozido, sementes de linhaça, chia e nozes."
            },
            {
                "nutriente": "Vitamina D",
                "importancia": "Imunomodulação materna, fixação de cálcio e prevenção de complicações no parto.",
                "fontes_alimentos": "Banhos de sol curtos matinais (15 minutos), ovos cozidos e suplementação médica individualizada."
            }
        ],
        "recomendacoes_trimestrais": [
            {
                "trimestre": "1º Trimestre (1ª a 13ª semana)",
                "foco": "Organogênese e alívio de náuseas",
                "ganho_esperado": "0,5 kg a 2,0 kg no total do trimestre",
                "dicas": "Se sofrer com enjoos, faça refeições fracionadas e frias. Não se preocupe se o ganho de peso for pequeno no início — o bebê está medindo poucos centímetros."
            },
            {
                "trimestre": "2º Trimestre (14ª a 27ª semana)",
                "foco": "Crescimento esquelético fetal e expansão volêmica materna",
                "ganho_esperado": "~0,3 a 0,5 kg por semana",
                "dicas": "Fase em que a disposição física melhora e o apetite costuma voltar. Mantenha caminhadas e boa hidratação (2,5 a 3 litros de água por dia)."
            },
            {
                "trimestre": "3º Trimestre (28ª a 40ª semana)",
                "foco": "Ganho de peso rápido do bebê e amadurecimento pulmonar",
                "ganho_esperado": "~0,3 a 0,5 kg por semana",
                "dicas": "O útero comprime o estômago; coma porções menores mais vezes ao dia. Fique atenta a inchaços súbitos e meça a pressão periodicamente."
            }
        ]
    }
