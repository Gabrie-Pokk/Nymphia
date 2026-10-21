"""
Serviço Clínico de Antropometria Materna e Ganho Ponderal Gestacional.
Ganho de peso: recomendação brasileira (FEBRASGO 2023, curvas de Kac et al. 2021,
Ministério da Saúde 2022). Altura uterina: padrão internacional INTERGROWTH-21st
(Papageorghiou et al., BMJ 2016), percentis 10 e 90, de 16 a 40 semanas.
A curva de Atalah ficou só por compatibilidade e não é mais usada pela API.
"""

import re
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

# Altura uterina (sínfise-fundo), em cm: percentis 10, 50 e 90 do padrão
# internacional INTERGROWTH-21st, que acompanhou gestantes de 8 países (o Brasil
# entre eles, em Pelotas). Fonte: Papageorghiou AT et al. BMJ 2016;355:i5662,
# tabela oficial de centis de 16 a 40 semanas, conferida em 15/10/2026.
#
# ATENÇÃO: até 15/10/2026 esta tabela tinha o rótulo "Ministério da Saúde", mas
# os números não batiam com nenhuma curva publicada (subiam de 1 em 1 cm, como
# uma aproximação). A Caderneta da Gestante traz a curva só como gráfico, sem
# tabela; se a equipe quiser usar exatamente a da Caderneta, os números precisam
# vir de uma fonte oficial com valores.
# semana: (p10, p50, p90)
CURVA_ALTURA_UTERINA = {
    16: (14.0, 15.8, 17.6),
    17: (14.9, 16.8, 18.6),
    18: (15.9, 17.8, 19.6),
    19: (16.9, 18.8, 20.7),
    20: (17.8, 19.8, 21.7),
    21: (18.8, 20.8, 22.7),
    22: (19.8, 21.8, 23.8),
    23: (20.7, 22.8, 24.8),
    24: (21.7, 23.8, 25.8),
    25: (22.7, 24.7, 26.8),
    26: (23.6, 25.7, 27.9),
    27: (24.6, 26.7, 28.9),
    28: (25.5, 27.7, 29.9),
    29: (26.4, 28.6, 30.9),
    30: (27.3, 29.6, 31.8),
    31: (28.2, 30.5, 32.8),
    32: (29.1, 31.4, 33.8),
    33: (30.0, 32.3, 34.7),
    34: (30.8, 33.2, 35.6),
    35: (31.6, 34.0, 36.5),
    36: (32.4, 34.9, 37.3),
    37: (33.2, 35.7, 38.2),
    38: (33.9, 36.5, 39.0),
    39: (34.7, 37.2, 39.8),
    40: (35.4, 38.0, 40.5),
}
SEMANA_INICIAL_ALTURA_UTERINA = 16

REFERENCIA_ALTURA_UTERINA = (
    "Padrão internacional INTERGROWTH-21st de altura uterina (Papageorghiou et al., BMJ 2016), "
    "percentis 10 e 90"
)

# ---------------------------------------------------------------------------
# Ganho de peso gestacional: recomendações brasileiras
# ---------------------------------------------------------------------------
# Fonte primária: Surita FG et al. "Guidelines on how to monitor gestational
# weight gain during antenatal care". FEBRASGO Position Statement nº 2,
# fevereiro de 2023. Rev Bras Ginecol Obstet 2023;45(2):104-108 (Quadro 1).
# Base: curvas brasileiras de Kac G et al., Am J Clin Nutr 2021;113:1351-1360
# (Consórcio Brasileiro de Nutrição Materno-Infantil, UFRJ), adotadas pelo
# Ministério da Saúde na Caderneta da Gestante de 2022; faixas escolhidas por
# Carrilho TRB et al., Am J Clin Nutr 2023, pelos desfechos PIG, GIG,
# prematuridade e retenção de peso no pós-parto.
#
# Valores ACUMULADOS em kg (peso na consulta menos peso pré-gestacional),
# conferidos em 15/10/2026 no texto da FEBRASGO:
#   IMC pré-gestacional      até 13 sem      até 27 sem    até 40 sem
#   < 18,5 (baixo peso)      0,2 a 1,2       5,6 a 7,2     9,7 a 12,2
#   18,5 a < 25 (eutrofia)   -1,8 a 0,7      3,1 a 6,3     8,0 a 12,0
#   25 a < 30 (sobrepeso)    -1,6 a -0,05    2,3 a 3,7     7,0 a 9,0
#   >= 30 (obesidade)        -1,6 a -0,05    1,1 a 2,7     5,0 a 7,2
#
# ATENÇÃO: até 15/10/2026 este arquivo usava, com o rótulo "UFRJ/MS 2022", os
# valores norte-americanos do IOM 2009 (12,5-18; 11,5-16; 7-11,5; 5-9 kg).
# Com aqueles valores, uma gestante eutrófica com 15 kg na 40ª semana aparecia
# como "adequada"; pela recomendação brasileira ela está acima da faixa.
#
# Entre os marcos (0, 13, 27 e 40 semanas) a faixa é interpolada em linha
# reta. As curvas oficiais não são retas; a interpolação é uma aproximação e
# o app diz isso na tela. Depois de 40 semanas vale a faixa da 40ª.
GANHO_RECOMENDADO_BRASIL = {
    "baixo_peso": {
        "categoria": "Baixo Peso",
        "imc_min": 0.0,
        "imc_max": 18.5,
        "marcos": {13: (0.2, 1.2), 27: (5.6, 7.2), 40: (9.7, 12.2)},
    },
    "adequado": {
        "categoria": "Adequado (Eutrófica)",
        "imc_min": 18.5,
        "imc_max": 25.0,
        "marcos": {13: (-1.8, 0.7), 27: (3.1, 6.3), 40: (8.0, 12.0)},
    },
    "sobrepeso": {
        "categoria": "Sobrepeso",
        "imc_min": 25.0,
        "imc_max": 30.0,
        "marcos": {13: (-1.6, -0.05), 27: (2.3, 3.7), 40: (7.0, 9.0)},
    },
    "obesidade": {
        "categoria": "Obesidade",
        "imc_min": 30.0,
        "imc_max": 100.0,
        "marcos": {13: (-1.6, -0.05), 27: (1.1, 2.7), 40: (5.0, 7.2)},
    },
}

REFERENCIA_GANHO_PESO = (
    "Recomendação brasileira de ganho de peso (FEBRASGO 2023; curvas de Kac et al. 2021, UFRJ; "
    "Ministério da Saúde, Caderneta da Gestante 2022)"
)


def _formatar_kg(valor: float) -> str:
    return f"{valor:.2f}".rstrip("0").rstrip(".").replace(".", ",") if valor != int(valor) else f"{int(valor)},0"


def _completar_tabela() -> None:
    """Acrescenta os campos usados pelas telas (total, ritmo médio e textos)."""
    for dados in GANHO_RECOMENDADO_BRASIL.values():
        m13, m40 = dados["marcos"][13], dados["marcos"][40]
        dados["ganho_total_min"], dados["ganho_total_max"] = m40
        # Ritmo médio da 13ª à 40ª semana, calculado a partir da tabela
        # (aproximação nossa; a FEBRASGO publica os marcos, não o ritmo semanal)
        dados["ganho_semanal_min"] = round((m40[0] - m13[0]) / 27.0, 2)
        dados["ganho_semanal_max"] = round((m40[1] - m13[1]) / 27.0, 2)
        m27 = dados["marcos"][27]
        dados["descricao"] = (
            f"Ganho acumulado recomendado: até 13 semanas {_formatar_kg(m13[0])} a {_formatar_kg(m13[1])} kg; "
            f"até 27 semanas {_formatar_kg(m27[0])} a {_formatar_kg(m27[1])} kg; "
            f"até 40 semanas {_formatar_kg(m40[0])} a {_formatar_kg(m40[1])} kg."
        )


_completar_tabela()

# Nome antigo mantido para compatibilidade com quem importa a tabela
TABELA_GANHO_UFRJ_MS_2022 = GANHO_RECOMENDADO_BRASIL


def categoria_por_imc(imc: Optional[float]) -> str:
    if imc is None:
        return "adequado"
    if imc < 18.5:
        return "baixo_peso"
    if imc < 25.0:
        return "adequado"
    if imc < 30.0:
        return "sobrepeso"
    return "obesidade"


def calcular_imc(peso_kg: float, altura_cm: float) -> Optional[float]:
    """Calcula o Índice de Massa Corporal (IMC = kg / m²)."""
    if not peso_kg or not altura_cm or altura_cm <= 0 or peso_kg <= 0:
        return None
    altura_m = altura_cm / 100.0
    return round(peso_kg / (altura_m * altura_m), 2)


_RISCOS = {
    "baixo_peso": "Risco maior de prematuridade, recém-nascido pequeno para a idade gestacional (PIG) e baixo peso ao nascer.",
    "adequado": "Menor frequência de complicações maternas e neonatais.",
    "sobrepeso": "Risco maior de diabetes gestacional, hipertensão na gestação e bebê grande para a idade gestacional.",
    "obesidade": "Risco maior de pré-eclâmpsia, diabetes gestacional, cesárea e bebê grande para a idade gestacional.",
}


def classificar_imc_pre_gestacional(imc: float) -> Dict[str, Any]:
    """Classifica o IMC pré-gestacional (cortes da OMS) e devolve as metas brasileiras."""
    chave = categoria_por_imc(imc)
    dados = GANHO_RECOMENDADO_BRASIL[chave]
    return {
        "imc": imc,
        "categoria": dados["categoria"],
        "ganho_total_min": dados["ganho_total_min"],
        "ganho_total_max": dados["ganho_total_max"],
        "ganho_semanal_min": dados["ganho_semanal_min"],
        "ganho_semanal_max": dados["ganho_semanal_max"],
        "ganho_semanal_2_3_tri": round((dados["ganho_semanal_min"] + dados["ganho_semanal_max"]) / 2.0, 2),
        "marcos_kg": {str(k): v for k, v in dados["marcos"].items()},
        "meta_descricao": dados["descricao"],
        "riscos_associados": _RISCOS[chave],
        "padrao_oficial": REFERENCIA_GANHO_PESO,
    }


def calcular_faixa_ganho_esperado_ufrj(categoria_chave: str, semana: int) -> Tuple[float, float]:
    """
    Faixa de ganho ACUMULADO recomendada (mín, máx) em kg para a semana.
    Interpolação em linha reta entre os marcos 0, 13, 27 e 40 semanas.
    """
    dados = GANHO_RECOMENDADO_BRASIL.get(categoria_chave, GANHO_RECOMENDADO_BRASIL["adequado"])
    pontos = [(0, 0.0, 0.0)] + [(sem, lo, hi) for sem, (lo, hi) in sorted(dados["marcos"].items())]
    sem = max(0, min(40, int(semana)))
    for (s0, lo0, hi0), (s1, lo1, hi1) in zip(pontos, pontos[1:]):
        if s0 <= sem <= s1:
            fracao = (sem - s0) / (s1 - s0)
            return round(lo0 + fracao * (lo1 - lo0), 2), round(hi0 + fracao * (hi1 - hi0), 2)
    return dados["marcos"][40]


def classificar_ganho_ponderal_ufrj_ms(
    semana: int,
    peso_atual_kg: float,
    peso_pre_kg: Optional[float] = None,
    altura_cm: Optional[float] = None,
    idade_gestante: Optional[int] = 28,
    gestacao_multipla: bool = False
) -> Dict[str, Any]:
    """
    Avalia o ganho de peso acumulado pela recomendação brasileira (ver tabela acima).

    1. Escopo: gestante adulta, um bebê só. Adolescente (< 18 anos) ou gestação
       múltipla recebem aviso de que a referência não se aplica.
    2. A faixa depende do IMC pré-gestacional.
    3. Comunicação sem julgamento: o texto nunca usa expressões como
       "engordou demais" ou "ganhou pouco"; aponta o dado e orienta conversar
       com a equipe do pré-natal.
    """
    semana_clamp = max(1, min(42, semana))

    fora_do_escopo = False
    motivo_fora_do_escopo = None
    aviso_escopo = None
    if idade_gestante is not None and idade_gestante < 18:
        fora_do_escopo = True
        motivo_fora_do_escopo = "adolescente"
        aviso_escopo = (
            "Aviso Clínico: As curvas nacionais de ganho de peso foram padronizadas para gestantes adultas. "
            "Como você tem menos de 18 anos, seu desenvolvimento biológico possui particularidades e a "
            "avaliação ponderal deve ser individualizada com seu obstetra ou nutricionista."
        )
    elif gestacao_multipla:
        fora_do_escopo = True
        motivo_fora_do_escopo = "gestacao_multipla"
        aviso_escopo = (
            "Aviso Clínico: Para gestações múltiplas (gemelares), as metas de ganho de peso são diferentes "
            "e as curvas brasileiras não se aplicam. Consulte sua equipe obstétrica para acompanhamento dedicado."
        )

    imc_pre = calcular_imc(peso_pre_kg, altura_cm) if (peso_pre_kg and altura_cm) else None
    cat_chave = categoria_por_imc(imc_pre)
    dados_cat = GANHO_RECOMENDADO_BRASIL[cat_chave]
    categoria_nome = dados_cat["categoria"] if imc_pre is not None else "Adequado (Eutrófica - Estimado)"
    ganho_esperado_min, ganho_esperado_max = calcular_faixa_ganho_esperado_ufrj(cat_chave, semana_clamp)

    ganho_acumulado = None
    if peso_pre_kg and peso_atual_kg:
        ganho_acumulado = round(peso_atual_kg - peso_pre_kg, 2)

    faixa_txt = f"{ganho_esperado_min:.1f} a {ganho_esperado_max:.1f} kg"
    if ganho_acumulado is not None:
        if ganho_acumulado < ganho_esperado_min:
            status = "ABAIXO"
            diagnostico = "Abaixo da faixa estimada"
            cor = "#E67E22"
            orientacao = (
                f"O ganho de peso acumulado ({ganho_acumulado:+.1f} kg) está abaixo da faixa estimada "
                f"pela recomendação brasileira para esta semana ({faixa_txt}). "
                "Vale compartilhar essa evolução com seu obstetra ou nutricionista na próxima consulta para avaliação conjunta."
            )
        elif ganho_acumulado <= ganho_esperado_max:
            status = "ADEQUADO"
            diagnostico = "Dentro da faixa recomendada"
            cor = "#27AE60"
            orientacao = (
                f"O ganho de peso acumulado ({ganho_acumulado:+.1f} kg) está dentro da faixa estimada "
                f"pela recomendação brasileira para a {semana_clamp}ª semana ({faixa_txt})."
            )
        else:
            status = "ACIMA"
            diagnostico = "Acima da faixa estimada"
            cor = "#C0392B"
            orientacao = (
                f"O ganho de peso acumulado ({ganho_acumulado:+.1f} kg) está acima da faixa estimada "
                f"pela recomendação brasileira para esta semana ({faixa_txt}). "
                "Vale comentar com seu obstetra na próxima consulta para avaliar retenção de líquidos e receber orientações nutricionais personalizadas."
            )
    else:
        status = "SEM_PESO_PRE"
        diagnostico = "Pendente de peso pré-gestacional"
        cor = "#7F8C8D"
        orientacao = (
            "Para calcularmos a faixa de ganho de peso recomendada para você, "
            "informe seu peso e altura antes da gestação no botão acima."
        )

    return {
        "referencia": REFERENCIA_GANHO_PESO,
        "nota_metodo": (
            "Faixa da semana calculada em linha reta entre os marcos oficiais de 13, 27 e 40 semanas; "
            "as curvas oficiais não são retas, então entre os marcos o valor é aproximado."
        ),
        "semana": semana_clamp,
        "categoria_pre_gestacional": categoria_nome,
        "imc_pre_gestacional": imc_pre,
        "peso_atual_kg": peso_atual_kg,
        "peso_pre_kg": peso_pre_kg,
        "ganho_acumulado_kg": ganho_acumulado,
        "ganho_esperado_min_kg": ganho_esperado_min,
        "ganho_esperado_max_kg": ganho_esperado_max,
        "ganho_semanal_referencia": (
            f"cerca de {dados_cat['ganho_semanal_min']:.2f} a {dados_cat['ganho_semanal_max']:.2f} kg/semana "
            "em média entre a 13ª e a 40ª semana"
        ).replace(".", ","),
        "ganho_total_referencia": f"{_formatar_kg(dados_cat['ganho_total_min'])} a {_formatar_kg(dados_cat['ganho_total_max'])} kg",
        "marcos_referencia": dados_cat["descricao"],
        "status": status,
        "diagnostico": diagnostico,
        "cor": cor,
        "orientacao": orientacao,
        "fora_do_escopo": fora_do_escopo,
        "motivo_fora_do_escopo": motivo_fora_do_escopo,
        "aviso_escopo": aviso_escopo,
        # Chaves de compatibilidade com telas antigas:
        "limite_baixo": ganho_esperado_min,
        "limite_adequado": ganho_esperado_max,
        "limite_sobrepeso": round(ganho_esperado_max * 1.25, 2),
    }

def classificar_curva_atalah(
    semana: int,
    imc_atual: float,
    peso_atual_kg: Optional[float] = None,
    peso_pre_kg: Optional[float] = None,
    altura_cm: Optional[float] = None,
    idade_gestante: Optional[int] = 28
) -> Dict[str, Any]:
    """
    OBSOLETA desde 15/10/2026: a API não usa mais a curva de Atalah (substituída
    no Brasil em 2022). Mantida só para compatibilidade de importação.
    """
    if peso_atual_kg is not None and peso_pre_kg is not None:
        return classificar_ganho_ponderal_ufrj_ms(
            semana=semana,
            peso_atual_kg=peso_atual_kg,
            peso_pre_kg=peso_pre_kg,
            altura_cm=altura_cm,
            idade_gestante=idade_gestante
        )

    # Fallback caso apenas o IMC atual esteja disponível
    semana_clamp = max(6, min(42, semana))
    limites = CURVA_ATALAH.get(semana_clamp, (21.5, 26.3, 31.1))
    baixo_lim, adequado_lim, sobrepeso_lim = limites

    if imc_atual < baixo_lim:
        diagnostico = "Baixo Peso Gestacional"
        cor = "#E67E22"
        orientacao = "O ganho de peso acumulado está abaixo da faixa estimada pela UFRJ/MS. Vale compartilhar com seu obstetra na próxima consulta."
    elif baixo_lim <= imc_atual < adequado_lim:
        diagnostico = "Adequado (Eutrófica)"
        cor = "#27AE60"
        orientacao = "O ganho de peso acumulado está dentro da faixa estimada pela UFRJ/MS, acompanhando o crescimento fetal saudável."
    elif adequado_lim <= imc_atual < sobrepeso_lim:
        diagnostico = "Sobrepeso Gestacional"
        cor = "#F39C12"
        orientacao = "O ganho de peso acumulado está ligeiramente acima da faixa estimada pela UFRJ/MS. Vale conversar na próxima consulta para avaliação nutricional."
    else:
        diagnostico = "Obesidade Gestacional"
        cor = "#C0392B"
        orientacao = "O ganho de peso acumulado está acima da faixa estimada pela UFRJ/MS. Vale comentar com seu obstetra para orientações nutricionais personalizadas."

    return {
        "semana": semana_clamp,
        "imc_atual": imc_atual,
        "diagnostico": diagnostico,
        "cor": cor,
        "limite_baixo": baixo_lim,
        "limite_adequado": adequado_lim,
        "limite_sobrepeso": sobrepeso_lim,
        "orientacao": orientacao,
        "referencia": "UFRJ / Ministério da Saúde (2022)",
        "nota_transicao": "A curva de Atalah foi substituída no Brasil pela Curva UFRJ/MS em 2022."
    }

def avaliar_altura_uterina(semana: Optional[int], au_cm: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    Compara a altura uterina (cm) com os percentis 10 e 90 do INTERGROWTH-21st
    para a semana em que foi medida. Antes de 16 semanas a curva não existe e a
    medida não é classificada. Depois de 40 semanas vale a faixa da 40ª.
    """
    if au_cm is None or semana is None:
        return None

    base = {
        "semana": semana,
        "altura_uterina_cm": au_cm,
        "referencia": REFERENCIA_ALTURA_UTERINA,
        "observacao": ("A medida muda um pouco de pessoa para pessoa que mede. "
                       "Mais do que uma medida isolada, importa a sequência ao longo das consultas."),
    }
    if semana < SEMANA_INICIAL_ALTURA_UTERINA:
        return {**base, "p10": None, "p50": None, "p90": None, "semana_referencia": None,
                "status": "Sem curva antes de 16 semanas", "cor": "#C9A84C",
                "detalhe": "A curva de altura uterina começa na 16ª semana. Esta medida fica anotada, sem classificação."}

    semana_ref = min(40, semana)
    p10, p50, p90 = CURVA_ALTURA_UTERINA[semana_ref]

    if au_cm < p10:
        status = "Abaixo do percentil 10"
        cor = "#E67E22"
        detalhe = ("A medida ficou abaixo do esperado para a semana. Mostre para sua equipe de pré-natal: "
                   "costuma ser pedido um ultrassom para ver o crescimento do bebê. Não é emergência, mas "
                   "se o bebê estiver mexendo menos, procure atendimento hoje.")
    elif au_cm <= p90:
        status = "Dentro do esperado (P10 a P90)"
        cor = "#27AE60"
        detalhe = "A medida está dentro da faixa esperada para a semana."
    else:
        status = "Acima do percentil 90"
        cor = "#F39C12"
        detalhe = ("A medida ficou acima do esperado para a semana. Pode ser um bebê maior, mais líquido "
                   "amniótico, gêmeos ou diabetes na gestação. Mostre para sua equipe: costuma ser pedido um ultrassom.")

    return {**base, "p10": p10, "p50": p50, "p90": p90, "semana_referencia": semana_ref,
            "status": status, "cor": cor, "detalhe": detalhe}


def obter_guia_educativo_antropometria(exames: Optional[List[Any]] = None) -> Dict[str, Any]:
    """
    Retorna guia educativo completo e desmistificador sobre ganho de peso,
    nutrição e composição corporal durante a gestação, personalizado pelos exames laboratoriais.
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
                "fato": "Mito! No 1º trimestre, o gasto calórico mal se altera. No 2º trimestre, o aumento é de cerca de 340 kcal por dia e no 3º, de cerca de 450 kcal: o equivalente a um lanche a mais, como iogurte natural com frutas e castanhas. O mais importante é a DENSIDADE NUTRICIONAL, não a quantidade de calorias vazias."
            },
            {
                "mito": "Não se pode engordar nada se já estiver com sobrepeso.",
                "fato": "Mito! Pela recomendação brasileira, mulheres com sobrepeso ganham de 7 a 9 kg e com obesidade de 5 a 7,2 kg até a 40ª semana, para permitir a formação adequada da placenta, líquido amniótico e crescimento do feto. Dietas de fome ou restrição severa de carboidratos são contraindicadas na gravidez."
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
                "importancia": "Essencial para o fechamento do tubo neural do bebê (prevenção de anencefalia e espinha bífida). O ideal é começar pelo menos 30 dias antes de engravidar; o Ministério da Saúde orienta manter durante a gestação. A dose é a que sua equipe indicar.",
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
                "fontes_alimentos": "Peixes como sardinha e salmão, bem cozidos. Linhaça, chia e nozes têm outro tipo de ômega-3 (ALA), que o corpo transforma pouco em DHA."
            },
            {
                "nutriente": "Vitamina D",
                "importancia": "Ajuda o corpo a aproveitar o cálcio, para os ossos da mãe e do bebê.",
                "fontes_alimentos": "Sardinha, salmão e gema de ovo. A pele também produz vitamina D com o sol; se for preciso suplementar, a dose é indicada pela sua equipe."
            }
        ],
        "recomendacoes_trimestrais": [
            {
                "trimestre": "1º Trimestre (1ª a 13ª semana)",
                "foco": "Organogênese e alívio de náuseas",
                "ganho_esperado": "Pequeno ou nenhum: de -1,8 a 0,7 kg para quem começou com IMC adequado (FEBRASGO 2023)",
                "dicas": "Se sofrer com enjoos, faça refeições fracionadas e frias. Não se preocupe se o ganho de peso for pequeno no início, ou se o peso cair um pouco: o bebê ainda mede poucos centímetros."
            },
            {
                "trimestre": "2º Trimestre (14ª a 27ª semana)",
                "foco": "Crescimento esquelético fetal e expansão volêmica materna",
                "ganho_esperado": "Até 27 semanas, acumulado de 3,1 a 6,3 kg para quem começou com IMC adequado",
                "dicas": "Fase em que a disposição física melhora e o apetite costuma voltar. Mantenha caminhadas e boa hidratação (2,5 a 3 litros de água por dia)."
            },
            {
                "trimestre": "3º Trimestre (28ª a 40ª semana)",
                "foco": "Ganho de peso rápido do bebê e amadurecimento pulmonar",
                "ganho_esperado": "Até 40 semanas, acumulado de 8 a 12 kg para quem começou com IMC adequado",
                "dicas": "O útero comprime o estômago; coma porções menores mais vezes ao dia. Fique atenta a inchaços súbitos e meça a pressão periodicamente."
            }
        ],
        "nutricao_personalizada_exames": processar_nutricao_baseada_em_exames(exames)
    }

def processar_nutricao_baseada_em_exames(exames: Optional[List[Any]] = None) -> Dict[str, Any]:
    """
    Cruza exames laboratoriais da gestante (hemograma/ferro, glicemia, vitamina D, B12, TSH)
    com protocolos nutricionais FEBRASGO e Ministério da Saúde, personalizando o guia alimentar.
    """
    valores_encontrados = {}

    if exames:
        for ex in exames:
            extraidos = getattr(ex, "valores_extraidos", {}) or {}
            if not isinstance(extraidos, dict):
                continue

            # Hemoglobina e Ferritina
            if "hemoglobina" in extraidos and "hemoglobina" not in valores_encontrados:
                try: valores_encontrados["hemoglobina"] = float(extraidos["hemoglobina"])
                except: pass
            if "ferritina" in extraidos and "ferritina" not in valores_encontrados:
                try: valores_encontrados["ferritina"] = float(extraidos["ferritina"])
                except: pass

            # Glicemia de Jejum
            if "glicemia_jejum_mg_dl" in extraidos and "glicemia" not in valores_encontrados:
                try: valores_encontrados["glicemia"] = float(extraidos["glicemia_jejum_mg_dl"])
                except: pass
            elif "glicemia" in extraidos and "glicemia" not in valores_encontrados:
                try: valores_encontrados["glicemia"] = float(extraidos["glicemia"])
                except: pass

            # Vitamina D
            if "vitamina_d" in extraidos and "vitamina_d" not in valores_encontrados:
                try: valores_encontrados["vitamina_d"] = float(extraidos["vitamina_d"])
                except: pass

            # Vitamina B12
            if "vitamina_b12" in extraidos and "vitamina_b12" not in valores_encontrados:
                try: valores_encontrados["vitamina_b12"] = float(extraidos["vitamina_b12"])
                except: pass

            # TSH (Tireoide)
            if "tsh" in extraidos and "tsh" not in valores_encontrados:
                try: valores_encontrados["tsh"] = float(extraidos["tsh"])
                except: pass

    biomarcadores = []

    # 1. Ferro, Ferritina e Hemoglobina
    hb = valores_encontrados.get("hemoglobina")
    ferr = valores_encontrados.get("ferritina")
    if hb is not None or ferr is not None:
        # Anemia na gestação: hemoglobina abaixo de 11 g/dL (OMS). Ferritina baixa sem
        # anemia é estoque de ferro baixo, não anemia.
        tem_anemia = hb is not None and hb < 11.0
        estoque_baixo = ferr is not None and ferr < 30.0
        if tem_anemia:
            status_texto = "Atenção: hemoglobina abaixo de 11 g/dL, compatível com anemia. Converse com sua equipe."
        elif estoque_baixo:
            status_texto = "Atenção: estoque de ferro baixo (ferritina abaixo de 30). Converse com sua equipe."
        else:
            status_texto = "Hemoglobina e ferro dentro do esperado"
        cor = "#C0392B" if tem_anemia else ("#E67E22" if estoque_baixo else "#27AE60")
        detalhe_valor = f"Hemoglobina: {hb} g/dL" if hb else ""
        if ferr: detalhe_valor += f" (Ferritina: {ferr} ng/mL)"
    else:
        status_texto = "Prevenção Nutricional de Anemia (Sem exame recente cadastrado)"
        cor = "#C9A84C"
        detalhe_valor = "Referência: Hemoglobina >= 11,0 g/dL | Ferritina >= 30 ng/mL"

    biomarcadores.append({
        "id": "ferro_hemoglobina",
        "nome": "Ferro, Ferritina & Hemoglobina",
        "icone": "🩸",
        "valor_detectado": detalhe_valor,
        "status": status_texto,
        "cor": cor,
        "alimentos_recomendados": [
            "Carnes vermelhas magras bem cozidas (fonte de ferro heme de alta biodisponibilidade)",
            "Feijão preto, carioca e lentilhas temperados com folhas de louro",
            "Folhas verde-escuras: couve refogada, espinafre e agrião",
            "Sementes de abóbora tostadas e gergelim"
        ],
        "sinergia_absorcao": "🍋 Dica de Ouro: Sempre consuma uma fonte de Vitamina C (suco de limão ou laranja, acerola, kiwi) junto da refeição rica em ferro.",
        "inibidores_evitar": "☕ Deixe café, chá preto ou verde e leite para 1 a 2 horas longe das refeições ricas em ferro: eles diminuem a absorção do ferro."
    })

    # 2. Glicemia de Jejum
    glic = valores_encontrados.get("glicemia")
    if glic is not None:
        # Critério brasileiro (OPAS, Ministério da Saúde, FEBRASGO e SBD, 2016): jejum de
        # 92 a 125 mg/dL na gestação é critério de diabetes gestacional; 126 ou mais,
        # de diabetes diagnosticado na gestação. O app avisa; quem confirma é a equipe.
        if glic >= 126.0:
            status_texto = "Atenção: jejum de 126 mg/dL ou mais. Mostre este exame para sua equipe o quanto antes."
            cor = "#C0392B"
        elif glic >= 92.0:
            status_texto = "Atenção: jejum entre 92 e 125 mg/dL, faixa usada no critério de diabetes gestacional. Mostre para sua equipe."
            cor = "#E67E22"
        else:
            status_texto = "Glicemia de jejum abaixo de 92 mg/dL"
            cor = "#27AE60"
        detalhe_valor = f"{glic} mg/dL (critério brasileiro: OPAS, Ministério da Saúde, FEBRASGO e SBD)"
    else:
        status_texto = "Equilíbrio Glicêmico & Curva Glicêmica"
        cor = "#C9A84C"
        detalhe_valor = "Referência na gestação: jejum abaixo de 92 mg/dL"

    biomarcadores.append({
        "id": "glicemia",
        "nome": "Glicemia & Controle de Carboidratos",
        "icone": "🥑",
        "valor_detectado": detalhe_valor,
        "status": status_texto,
        "cor": cor,
        "alimentos_recomendados": [
            "Fibras solúveis: farelo de aveia, sementes de chia e linhaça dourada",
            "Saladas cruas no início das refeições para retardar o pico glicêmico",
            "Carboidratos complexos de baixo índice glicêmico: batata-doce, arroz integral, quinoa",
            "Proteínas magras em todas as refeições (ovos caipiras, peito de frango, peixes)"
        ],
        "sinergia_absorcao": "⏰ Estratégia de Fracionamento: Faça 5 a 6 refeições menores a cada 3 horas para evitar quedas e picos acentuados de insulina.",
        "inibidores_evitar": "🚫 Evite sucos de fruta concentrados (mesmo 100% fruta, pois perdem a fibra), refrigerantes, doces refinados e pães brancos em jejum."
    })

    # 3. Vitamina D
    vit_d = valores_encontrados.get("vitamina_d")
    if vit_d is not None:
        # SBEM e SBPC/ML (Arch Endocrinol Metab 2020;64(4):462-478): para gestantes,
        # 30 a 60 ng/mL; abaixo de 20 é deficiência.
        if vit_d < 20.0:
            status_texto = "Atenção: vitamina D abaixo de 20 ng/mL (deficiência). Mostre para sua equipe."
            cor = "#E67E22"
        elif vit_d < 30.0:
            status_texto = "Vitamina D abaixo de 30 ng/mL, valor recomendado para gestantes. Converse com sua equipe."
            cor = "#F39C12"
        else:
            status_texto = "Vitamina D dentro do recomendado para gestantes (30 ng/mL ou mais)"
            cor = "#27AE60"
        detalhe_valor = f"{vit_d} ng/mL"
    else:
        status_texto = "Mineralização Óssea & Fixação de Cálcio"
        cor = "#C9A84C"
        detalhe_valor = "Referência para gestantes: 30 a 60 ng/mL (SBEM e SBPC/ML, 2020)"

    biomarcadores.append({
        "id": "vitamina_d",
        "nome": "Vitamina D & Saúde Esquelética",
        "icone": "☀️",
        "valor_detectado": detalhe_valor,
        "status": status_texto,
        "cor": cor,
        "alimentos_recomendados": [
            "Ovos caipiras cozidos (consumir com a gema)",
            "Sardinha fresca e salmão bem cozidos",
            "Cogumelos frescos expostos ao sol"
        ],
        "sinergia_absorcao": "☀️ Sol com cuidado: use protetor solar (manchas na pele são comuns na gestação). A necessidade de suplementar vitamina D é avaliada pela sua equipe.",
        "inibidores_evitar": "⚠️ Não tome megadoses por conta própria; a suplementação em gotas ou cápsulas deve ser ajustada com a dosagem prescrita pelo obstetra."
    })

    # 4. Hormônios da Tireoide (TSH)
    tsh = valores_encontrados.get("tsh")
    if tsh is not None:
        # A faixa de TSH na gestação depende do trimestre e do laboratório; quem interpreta é a equipe
        status_texto = f"TSH: {tsh} mUI/L. Sua equipe interpreta pelo trimestre e pela referência do laboratório."
        cor = "#C9A84C"
        detalhe_valor = f"{tsh} mUI/L"
    else:
        status_texto = "Tireoide & Neurodesenvolvimento Fetal"
        cor = "#C9A84C"
        detalhe_valor = "A referência de TSH na gestação depende do trimestre e do laboratório"

    biomarcadores.append({
        "id": "tsh_tireoide",
        "nome": "Hormônio TSH & Suporte Tireoidiano",
        "icone": "🦋",
        "valor_detectado": detalhe_valor,
        "status": status_texto,
        "cor": cor,
        "alimentos_recomendados": [
            "Sal de cozinha iodado brasileiro (usado com moderação para não elevar a pressão)",
            "Peixes de água salgada bem cozidos",
            "Castanha-do-pará: 1 por dia já costuma cobrir o selênio do dia; não precisa de mais"
        ],
        "sinergia_absorcao": "💊 Se você toma levotiroxina: tome em jejum e deixe pelo menos 4 horas de distância dos suplementos de ferro e cálcio, que atrapalham a absorção.",
        "inibidores_evitar": "🚫 Evite excesso de soja não fermentada ou couve crua em grandes volumes se tiver hipotireoidismo diagnosticado."
    })

    return {
        "tem_exames_cadastrados": len(valores_encontrados) > 0,
        "valores_identificados": valores_encontrados,
        "biomarcadores": biomarcadores
    }


# ---------------------------------------------------------------------------
# Semana gestacional, pressão, edema e ritmo de ganho (15/10/2026)
# ---------------------------------------------------------------------------
# Até 15/10/2026 a pressão anotada junto com o peso era guardada e nunca
# avaliada: quem anotava 160/110 com 30 semanas não recebia alerta nenhum.
# Os cortes seguem os do check-in (rules_engine): 140/90 ou mais é urgente,
# porque na gestação pode ser pré-eclâmpsia e a prioridade é não deixar passar.

def semana_na_data(dum: Optional[date], dia: date) -> Optional[int]:
    """Semanas completas de gestação numa data, a partir da DUM. None sem DUM."""
    if not dum or not dia:
        return None
    return max(0, (dia - dum).days // 7)


_PRESSAO_TEXTO = re.compile(
    r"^\s*(\d{1,3})(?:[.,]\d)?\s*(?:/|x|por)\s*(\d{1,3})(?:[.,]\d)?\s*(?:mm\s*hg|cm\s*hg)?\s*$",
    re.IGNORECASE,
)


def ler_pressao_arterial(texto: Optional[str]) -> Optional[Tuple[int, int]]:
    """'120/80', '120x80', '120 por 80' ou '12 por 8' (cmHg) viram (120, 80). None se não der para ler."""
    if not texto:
        return None
    achado = _PRESSAO_TEXTO.match(texto.strip())
    if not achado:
        return None
    from app.services.rules_engine import pressao_em_mmhg
    return pressao_em_mmhg(int(achado.group(1)), int(achado.group(2)))


DIAS_PARA_PRESSAO_RECENTE = 7


def avaliar_pressao_arterial(texto: Optional[str], data_medida: Optional[date] = None,
                             hoje: Optional[date] = None) -> Optional[Dict[str, Any]]:
    leitura = ler_pressao_arterial(texto)
    if leitura is None:
        return None
    sistolica, diastolica = leitura
    hoje = hoje or datetime.utcnow().date()
    data_medida = data_medida or hoje
    recente = (hoje - data_medida).days <= DIAS_PARA_PRESSAO_RECENTE

    base = {"tipo": "pressao", "sistolica": sistolica, "diastolica": diastolica,
            "data": data_medida.isoformat(), "leitura": f"{sistolica}/{diastolica} mmHg"}
    if sistolica < 140 and diastolica < 90:
        return {**base, "nivel": "nenhum", "titulo": f"Pressão {sistolica}/{diastolica} mmHg",
                "orientacao": "Dentro do esperado na gestação (abaixo de 140/90)."}
    if not recente:
        return {**base, "nivel": "atencao", "titulo": f"Última pressão anotada estava alta ({sistolica}/{diastolica})",
                "orientacao": (f"A pressão anotada em {data_medida.strftime('%d/%m')} estava alta. "
                               "Meça de novo hoje e conte para sua equipe de pré-natal.")}
    if sistolica >= 160 or diastolica >= 110:
        return {**base, "nivel": "urgente", "titulo": f"Pressão muito alta: {sistolica}/{diastolica} mmHg",
                "orientacao": ("Procure a maternidade agora. Pressão nesse nível na gestação precisa de "
                               "avaliação imediata, mesmo sem outros sintomas.")}
    return {**base, "nivel": "urgente", "titulo": f"Pressão alta: {sistolica}/{diastolica} mmHg",
            "orientacao": ("Procure atendimento ainda hoje, na maternidade ou com sua equipe de pré-natal, "
                           "para medir de novo e investigar pré-eclâmpsia. Vá agora se tiver dor de cabeça forte, "
                           "visão embaçada ou pontos brilhantes, dor no estômago ou falta de ar.")}


def avaliar_edema(edema: Optional[str]) -> Optional[Dict[str, Any]]:
    """Inchaço discreto é comum na gestação; o intenso (3+ ou 4+) merece aviso."""
    if edema in ("+++/4+", "++++/4+"):
        return {"tipo": "edema", "nivel": "atencao", "titulo": f"Inchaço intenso anotado ({edema})",
                "orientacao": ("Conte para sua equipe de pré-natal. Procure a maternidade se o inchaço apareceu "
                               "de repente, no rosto ou nas mãos, ou veio com dor de cabeça, visão embaçada ou pressão alta.")}
    return None


def avaliar_ritmo_de_ganho(peso_atual: float, data_atual: date, peso_anterior: float, data_anterior: date,
                           semana: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    Ganho rápido entre duas pesagens, a partir de 20 semanas: 1 kg ou mais em até
    10 dias (regra antiga, mantida) ou ritmo de 1 kg por semana ou mais em até 21 dias.
    """
    dias = (data_atual - data_anterior).days
    if dias <= 0 or dias > 21 or semana is None or semana < 20:
        return None
    ganho = peso_atual - peso_anterior
    ritmo = ganho / dias * 7
    if (ganho >= 1.0 and dias <= 10) or ritmo >= 1.0:
        return {"tipo": "ganho_rapido", "nivel": "atencao",
                "titulo": f"Ganho rápido: {_formatar_kg(round(ganho, 1))} kg em {dias} dias",
                "orientacao": ("Ganho rápido de peso pode ser retenção de líquido. Meça a pressão hoje; "
                               "se estiver em 140/90 ou mais, ou se houver inchaço no rosto ou nas mãos, "
                               "procure a maternidade.")}
    return None


def curva_ganho_recomendada(categoria_chave: str) -> List[Dict[str, Any]]:
    """Faixa recomendada de ganho acumulado de 0 a 40 semanas, para o gráfico."""
    return [
        {"semana": s, "min_kg": lo, "max_kg": hi}
        for s in range(0, 41)
        for lo, hi in [calcular_faixa_ganho_esperado_ufrj(categoria_chave, s)]
    ]
