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
        tem_anemia = (hb is not None and hb < 11.0) or (ferr is not None and ferr < 30.0)
        status_texto = "Atenção: Indicativo de Anemia Ferropriva / Estoque Baixo de Ferro" if tem_anemia else "Níveis de Hemoglobina e Ferro Adequados"
        cor = "#C0392B" if tem_anemia else "#27AE60"
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
        "inibidores_evitar": "☕ Evite estritamente café, chá preto/verde, leite e derivados até 2 horas após o almoço ou jantar (cálcio e polifenóis reduzem a absorção de ferro em até 60%)."
    })

    # 2. Glicemia de Jejum
    glic = valores_encontrados.get("glicemia")
    if glic is not None:
        tem_dg = glic >= 92.0
        status_texto = "Atenção: Glicemia Limítrofe / Rastreio de Diabetes Gestacional (>= 92 mg/dL)" if tem_dg else "Glicemia de Jejum Normal (< 92 mg/dL)"
        cor = "#E67E22" if tem_dg else "#27AE60"
        detalhe_valor = f"{glic} mg/dL (Critério FEBRASGO/IADPSG)"
    else:
        status_texto = "Equilíbrio Glicêmico & Curva Glicêmica"
        cor = "#C9A84C"
        detalhe_valor = "Meta no 1º, 2º e 3º trimestres: Jejum < 92 mg/dL"

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
        baixa_d = vit_d < 30.0
        status_texto = "Atenção: Vitamina D Subótima (< 30 ng/mL)" if baixa_d else "Vitamina D em Faixa Ideal (>= 30 ng/mL)"
        cor = "#F39C12" if baixa_d else "#27AE60"
        detalhe_valor = f"{vit_d} ng/mL"
    else:
        status_texto = "Mineralização Óssea & Fixação de Cálcio"
        cor = "#C9A84C"
        detalhe_valor = "Meta gestacional recomendada: >= 30 ng/mL"

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
        "sinergia_absorcao": "☀️ Banho de Sol Seguro: 15 a 20 minutos de sol matinal antes das 9h com braços e pernas descobertos (sem protetor nas áreas expostas por curto período).",
        "inibidores_evitar": "⚠️ Não tome megadoses por conta própria; a suplementação em gotas ou cápsulas deve ser ajustada com a dosagem prescrita pelo obstetra."
    })

    # 4. Hormônios da Tireoide (TSH)
    tsh = valores_encontrados.get("tsh")
    if tsh is not None:
        status_texto = f"TSH: {tsh} mUI/L (Acompanhamento Perinatal)"
        cor = "#27AE60" if 0.4 <= tsh <= 3.0 else "#E67E22"
        detalhe_valor = f"{tsh} mUI/L"
    else:
        status_texto = "Tireoide & Neurodesenvolvimento Fetal"
        cor = "#C9A84C"
        detalhe_valor = "Referência: 1º tri < 2,5 mUI/L | 2º e 3º tri < 3,0 mUI/L"

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
            "Castanha-do-pará (1 unidade ao dia fornece o selênio ideal para a conversão de T4 em T3)"
        ],
        "sinergia_absorcao": "💧 Hidratação Plena: A tireoide regula a temperatura corporal e a expansão do volume sanguíneo gestacional.",
        "inibidores_evitar": "🚫 Evite excesso de soja não fermentada ou couve crua em grandes volumes se tiver hipotireoidismo diagnosticado."
    })

    return {
        "tem_exames_cadastrados": len(valores_encontrados) > 0,
        "valores_identificados": valores_encontrados,
        "biomarcadores": biomarcadores
    }
