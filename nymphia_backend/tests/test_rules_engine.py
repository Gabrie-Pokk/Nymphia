"""
Bateria de frases do motor de sinais de alerta (app/services/rules_engine.py).

Regra de ouro desta bateria: NENHUMA mudança no motor pode fazer uma frase da
lista URGENTES deixar de ser urgente. Falso negativo é o erro mais grave.
Quando aparecer um relato real que o motor não pegou, a frase entra aqui
antes da correção.

As frases das listas URGENTES e NENHUM marcadas com "auditoria 15/10" são os
erros encontrados na versão anterior do motor.
"""
import pytest

from app.services.rules_engine import analyze_urgency, avaliar, normalizar

URGENTES = [
    # Falsos negativos da versão anterior (auditoria 15/10)
    "Sangrou bastante hoje de manhã",
    "Faz um dia que não sinto o bebê",
    "Escorreu um líquido pelas pernas",
    "As contrações estão vindo de 5 em 5 minutos",
    "Meu rosto e minhas mãos incharam muito de repente",
    "Estou com dor de cabeça que não passa e vendo pontinhos",
    # Frases dos testes de ponta a ponta
    "Notei um sangramento vermelho vivo agora de manhã com dor forte.",
    "Estou com sangramento e dor de cabeca insuportavel com pontos brilhantes",
    "Estou tendo um sangramento vermelho vivo muito forte",
    "Dor de cabeça súbita pulsátil muito forte, com visão embaçada e pontinhos brilhantes.",
    # Sangramento: negação que não é negação
    "Não sei se é sangue, mas a calcinha ficou manchada",
    "Não é muito sangue, mas está saindo",
    "Não para de sangrar",
    "Não aguento mais esse sangramento",
    "Hoje de manhã não tive nada, mas agora à tarde sangrou um pouco",
    "Tô sangrando",
    "sangrano muito desde cedo",
    "Saiu um coágulo",
    "Tive um escape de sangue hoje",
    # Líquido
    "A bolsa estourou",
    "Acho que rompeu a bolsa",
    "Minha calcinha está molhada e não foi xixi",
    "Estou perdendo líquido",
    "Saiu uma água pela vagina",
    # Movimentos do bebê
    "O bebê não mexe desde ontem",
    "n sinto o bb mecher",
    "O bebê está bem paradinho hoje",
    "Ele está mexendo bem menos que ontem",
    "Parou de mexer",
    "Quase não sinto mais o bebê",
    "Faz 12 horas que não sinto ele",
    # Contrações e parto
    "Contrações fortes e ritmadas",
    "Estou com muitas contrações",
    "Acho que entrei em trabalho de parto",
    # Pressão e pré-eclâmpsia
    "Minha pressão deu 15 por 10",
    "Medi a pressão: 140/95",
    "Minha pressão está alta",
    "A pressão subiu de novo",
    "Pressão 14x9",
    "Dor forte na boca do estômago",
    "Estou com uma dor em barra",
    "Minha visão está embaçada",
    "Estou vendo estrelinhas",
    "Dor de cabeça muito forte",
    # Febre
    "Estou com febre de 38,5",
    "Estou com febre",
    "Termômetro marcou 38 graus",
    # Neurológico, ar, peito
    "Tive uma convulsão",
    "Desmaiei no banheiro",
    "Não consigo respirar direito",
    "Estou com dor no peito",
    # Dor abdominal forte
    "Dor muito forte na barriga",
    "Cólica forte que não passa",
    # Trauma
    "Levei um tombo na escada",
    "Caí da escada hoje",
    "Meu marido me bateu",
    "Bati a barriga na mesa",
    # Vômitos e glicemia
    "Vomitando sem parar, não consigo segurar nem água",
    "Minha glicemia deu 45",
    # Saúde emocional
    "Penso em me matar",
    "Não quero mais viver",
    # Segunda rodada de exploração (15/10)
    "molhou tudo a cama e não é xixi",
    "faz tempo que ele nao mexe",
    "sinto ele bem fraquinho",
    "ele não está se mexendo",
    "dor de parto",
    "cabeça explodindo de dor",
    "dor embaixo das costelas",
    "levei um soco na barriga",
    "to tendo contração atrás de contração",
    "não estou bem, estou sangrando",
    "Não sinto dor, mas estou sangrando",
    "Sem dor, só sangramento",
    "Nem sei o que fazer, estou sangrando",
    "não consigo sentir o bebê",
    "não tô sentindo nada do bebê",
    "Nenhum movimento do bebê hoje",
    "Não tenho sentido o bebê",
    "ele ta mais quieto hj",
    "Minha barriga está muito dura e dói",
    "Estou com sangramento pelo nariz e na calcinha também",
    "minha pressão tá 14/9",
    "Meu filho me passou febre",
    "Meu marido está com febre e eu também",
    "meu marido quer me matar",
    "Estou com medo porque estou sangrando",
    "O bebê mexe menos à noite, é normal?",
    # Versão anterior já pegava e continua pegando
    "hemorragia",
    "Visão turva desde cedo",
    "escotoma",
    "Perda de líquido",
    "Calafrio intenso e febre alta",
    "Perda de consciência",
]

NENHUM = [
    # Falsos positivos da versão anterior (auditoria 15/10)
    "Hoje não tive nenhum sangramento, graças a Deus",
    "Estou sem dor de cabeça forte hoje",
    "Fui à palestra sobre hemorragia pós-parto",
    "O bebê mexeu muito hoje, sem movimento estranho",
    # Contexto de exame, nariz, gengiva
    "Fiz exame de sangue hoje",
    "Minha glicemia deu 95 no exame de sangue, será que tá alta?",
    "Sangrou meu nariz hoje de manhã",
    "Minha gengiva sangra quando escovo os dentes",
    # Negação clara
    "Não estou com febre",
    "Não estou sangrando, só com um pouco de enjoo",
    "Pressão 12 por 8, estou com 14 semanas",
    # Bebê mexendo muito é bom sinal
    "O bebê não para de mexer",
    # Dúvida hipotética
    "O que fazer se a bolsa estourar?",
    # Expressões do dia a dia
    "Estou morrendo de fome",
    "Estou com muita azia e queimação hoje",
    "Hoje me sinto muito bem e disposta.",
    "Tenho dúvidas sobre como prevenir toxoplasmose e os gatos",
    "Oi, como você funciona?",
    "Dia calmo, sentindo apenas leve cansaço habitual.",
    # Segunda rodada de exploração (15/10)
    "doei sangue antes de engravidar",
    "sangue bom esse pessoal da comunidade",
    "assisti um vídeo sobre pré-eclâmpsia",
    "meu marido está com febre",
    "minha filha teve febre ontem",
    "A pressão da minha mãe deu 15 por 10",
    "Minha mãe desmaiou",
    "Não tive sangramento nem perda de líquido",
    "Sem sangramento, sem perda de líquido, bebê mexendo bem",
    "Senti o bebê mexer pela primeira vez!",
    "estou com medo de sangrar",
    "tenho medo da bolsa estourar",
    "o médico disse que posso ter pré-eclâmpsia",
    "pressão normal 11 por 7",
    "como saber se a bolsa estourou?",
]

ATENCAO = [
    "Estou com dor de cabeça",
    "Senti umas contrações hoje",
    "Tenho ardência ao urinar",
    "Estou com corrimento amarelado",
    "Estou com um pouco de falta de ar quando subo escada",
    "Estou com tontura",
    "Estou com dor no estômago",
    "Minhas mãos estão inchadas",
    "Estou com 37,6 de temperatura",
]


@pytest.mark.parametrize("frase", URGENTES)
def test_frase_urgente_gera_alerta(frase):
    resultado = avaliar(frase)
    assert resultado.nivel == "urgente", f"FALSO NEGATIVO: {frase!r} -> {resultado}"
    assert "192" in resultado.orientacao


@pytest.mark.parametrize("frase", NENHUM)
def test_frase_sem_sinal_nao_gera_alerta(frase):
    resultado = avaliar(frase)
    assert resultado.nivel == "nenhum", f"FALSO POSITIVO: {frase!r} -> {resultado}"


@pytest.mark.parametrize("frase", ATENCAO)
def test_frase_de_atencao(frase):
    resultado = avaliar(frase)
    assert resultado.nivel == "atencao", f"{frase!r} -> {resultado}"
    assert "pré-natal" in resultado.orientacao


# --- Opções marcadas no check-in ---

@pytest.mark.parametrize("opcao", [
    "Sangramento vaginal", "Perda de líquido", "Visão embaçada", "Bebê mexendo menos",
    "Contrações ritmadas ou dolorosas", "Febre (37,8 °C ou mais)", "Dor de cabeça forte",
    "Pressão 14 por 9 ou mais", "Falta de ar forte",
])
def test_opcao_urgente(opcao):
    assert avaliar("", [opcao]).nivel == "urgente"


def test_dor_no_estomago_marcada_sozinha_e_atencao_e_nao_urgencia():
    # Na versão anterior, marcar "Dor no estômago" disparava urgência sempre
    assert avaliar("", ["Dor no estômago"]).nivel == "atencao"


@pytest.mark.parametrize("opcao", ["Náusea / Enjoo", "Azia / Queimação", "Inchaço nas pernas",
                                   "Cólicas leves", "Cansaço excessivo"])
def test_opcoes_comuns_nao_alertam(opcao):
    assert avaliar("", [opcao]).nivel == "nenhum"


def test_dois_sinais_de_pre_eclampsia_juntos_viram_urgencia():
    resultado = avaliar("", ["Dor de cabeça", "Inchaço no rosto ou nas mãos"])
    assert resultado.nivel == "urgente"
    assert "conjunto_pre_eclampsia" in resultado.codigos


def test_texto_livre_soma_com_opcao_marcada():
    resultado = avaliar("estou vendo uns pontinhos", ["Dor de cabeça"])
    assert resultado.nivel == "urgente"


def test_ardencia_com_dor_nas_costas_vira_urgencia():
    assert avaliar("estou com dor nas costas", ["Ardência ao urinar"]).nivel == "urgente"


def test_opcao_desconhecida_e_lida_como_texto():
    assert avaliar("", ["sangramento"]).nivel == "urgente"


# --- Números ---

def test_pressao_em_centimetros_e_convertida():
    resultado = avaliar("pressão 15 por 10")
    assert "pressão 150/100 mmHg" in resultado.leituras


def test_data_com_barra_nao_vira_pressao():
    assert avaliar("Minha consulta é dia 15/10").nivel == "nenhum"


def test_sofrimento_emocional_traz_cvv():
    resultado = avaliar("Penso em me matar")
    assert "188" in resultado.orientacao


# --- Interface antiga continua funcionando ---

def test_interface_antiga_analyze_urgency():
    urgente, alertas, orientacao = analyze_urgency("Estou sangrando muito")
    assert urgente is True
    assert alertas
    assert "ALERTA CLÍNICO DE URGÊNCIA" in orientacao
    assert analyze_urgency("Estou com dor de cabeça") == (False, [], "")


def test_normalizacao():
    assert normalizar("Tô com DOR de CABEÇA") == "estou com dor de cabeca"
    assert normalizar("n sinto o bb mecher") == "nao sinto o bebe mexer"


def test_opcoes_do_frontend_batem_com_o_motor():
    """Cada opção de sintoma da tela de check-in precisa existir no motor de regras."""
    import re
    from pathlib import Path
    from app.services.rules_engine import SINTOMAS_ESTRUTURADOS

    tela = Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "gestante" / "DailyCheckin.jsx"
    if not tela.exists():
        pytest.skip("frontend não está neste checkout")
    fonte = tela.read_text(encoding="utf-8")
    opcoes = []
    for nome in ("SINAIS_DE_ALERTA", "OUTROS_SINTOMAS"):
        bloco = re.search(nome + r" = \[(.*?)\];", fonte, re.S).group(1)
        opcoes += re.findall(r"'([^']+)'", bloco)
    assert len(opcoes) >= 15
    faltando = [o for o in opcoes if normalizar(o) not in SINTOMAS_ESTRUTURADOS]
    assert faltando == [], f"Opções da tela sem regra no motor: {faltando}"
    alerta = re.search(r"SINAIS_DE_ALERTA = \[(.*?)\];", fonte, re.S).group(1)
    for opcao in re.findall(r"'([^']+)'", alerta):
        assert SINTOMAS_ESTRUTURADOS[normalizar(opcao)][2] == "urgente", opcao
