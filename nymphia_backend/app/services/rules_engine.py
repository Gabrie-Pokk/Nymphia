"""
Nymphia -- Motor de regras de sinais de alerta na gestação (versão 2, 15/10/2026).

PRINCÍPIO: o erro mais grave aqui é o FALSO NEGATIVO (a gestante relata um
sinal de perigo e o app não alerta). Por isso, na dúvida, o motor alerta.
O falso positivo é reduzido só nos casos em que dá para ter certeza de que a
frase NÃO relata o sinal: negação explícita ("não tive sangramento"), contexto
de exame ("exame de sangue"), sangramento de nariz ou gengiva, ou assunto
apenas informativo ("palestra sobre hemorragia").

Três níveis de resposta:
  urgente   procurar a maternidade agora ou ligar 192 (SAMU)
  atencao   falar com o pré-natal hoje; se piorar, maternidade
  nenhum    nada encontrado

Base clínica dos sinais (a ser validada pela equipe médica do projeto):
  Caderneta da Gestante (Ministério da Saúde) e manuais de gestação de alto
  risco do MS e da FEBRASGO: sangramento vaginal, perda de líquido,
  contrações regulares, diminuição dos movimentos do bebê, febre, dor de
  cabeça forte, alterações visuais, dor forte no estômago ou abdome, inchaço
  repentino do rosto e das mãos, pressão a partir de 140/90, falta de ar,
  convulsão, desmaio, trauma e sofrimento emocional grave.

Este motor não faz diagnóstico. Ele só decide quando orientar a procurar
atendimento.

Como funciona, em ordem:
  1. normaliza o texto (minúsculas, sem acento, gírias e erros comuns);
  2. procura cada sinal com expressões amplas (para não perder relatos);
  3. descarta uma ocorrência só se ela estiver negada de forma explícita,
     for contexto de exame, de nariz ou gengiva, ou for assunto informativo;
  4. combina sinais (ex.: dor de cabeça + inchaço no rosto = urgente);
  5. lê números: pressão "14 por 9", febre "38,5", glicemia "45".
"""
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 1. Normalização
# ---------------------------------------------------------------------------

_SUBSTITUICOES = [
    (r"\bmech", "mex"),                          # mecher, mecheu -> mexer
    (r"\bcabe(?:ss|s|c|ç)a\b", "cabeca"),
    (r"\b(?:nene|nenem|bb|bebezinh[oa]|bebezao|neneca|bebes?)\b", "bebe"),
    (r"\b(?:presao|precao|preção|presão)\b", "pressao"),
    (r"\bnaum\b", "nao"),
    (r"\bn\b", "nao"),
    (r"\b(?:mto|mt|mtu)\b", "muito"),
    (r"\bpq\b", "porque"),
    (r"\bq\b", "que"),
    (r"\bta\b", "esta"),
    (r"\bto\b", "estou"),
    (r"\bvc\b", "voce"),
    (r"\bhj\b", "hoje"),
    (r"\bagr\b", "agora"),
    (r"\bdps\b", "depois"),
    (r"\bxixi\b", "urina"),
    (r"\bfazer urina\b", "urinar"),
    # "não para de sangrar" quer dizer que CONTINUA sangrando: não é negação
    (r"\bnao (?:para|parou|paro|parava|consigo parar|consegue parar|pode parar) de\b", "continua a"),
    (r"\bnao (?:passa|passou|melhora|melhorou|diminui|diminuiu|alivia|aliviou)\b", "persistente"),
]

_SUBSTITUICOES_COMPILADAS = [(re.compile(p), s) for p, s in _SUBSTITUICOES]


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[\"“”'`´]", " ", t)
    t = re.sub(r"(?<=[a-z])-(?=[a-z])", " ", t)
    t = re.sub(r"[ \t]+", " ", t)
    for padrao, substituto in _SUBSTITUICOES_COMPILADAS:
        t = padrao.sub(substituto, t)
    return t.strip()


# ---------------------------------------------------------------------------
# 2. Contexto de cada ocorrência: negação, informativo, pergunta hipotética
# ---------------------------------------------------------------------------

_FIM_DE_ORACAO = re.compile(r"[.!?;,\n]| mas | porem | so que | contudo | entretanto | e sim ")
_FIM_DE_FRASE = re.compile(r"[.!?\n]")

NEGACOES = {"nao", "nem", "sem", "nenhum", "nenhuma", "nunca", "jamais", "zero", "nada"}

# Palavras que, entre a negação e o sinal, mostram que a frase NÃO está negando
# o sinal: "não sei se é sangue", "não aguento mais esse sangramento",
# "não é muito sangue", "nada além de sangramento".
NEUTRALIZADORES = {
    "sei", "sabia", "certeza", "parece", "acho", "sera", "entendo", "aguento",
    "aguentando", "consigo", "porque", "normal", "so", "apenas", "somente",
    "muito", "tanto", "tanta", "bastante", "pouco", "pouquinho", "pouca", "tao",
    "alem", "exceto", "fora", "continua", "persistente", "quero", "posso",
    "gosto", "gostei", "lembro",
}

JANELA_NEGACAO = 4

_INFORMATIVO = re.compile(
    r"\b(?:palestra|aula|curso|video|artigo|reportagem|livro|documentario|podcast|post|"
    r"texto|pesquisa|materia|filme|novela|serie|li|vi|ouvi|assisti|estudei|aprendi|pesquisei)\b"
    r"(?: \w+){0,3} (?:sobre|a respeito d\w+|que fala\w* (?:de|sobre))(?: \w+){0,3} ?$"
)

_HIPOTESE = re.compile(r"\b(?:se|caso|quando)\b(?: \w+){0,4} ?$")

# Medo, risco ou possibilidade logo antes do sinal: "tenho medo de sangrar",
# "risco de pré-eclâmpsia", "posso ter pré-eclâmpsia". Não é relato do sinal.
_NAO_RELATO = re.compile(
    r"\b(?:medo|receio|risco|chance|chances|possibilidade|prevenir|evitar|prevencao) (?:de|da|do|das|dos)(?: \w+){0,2} ?$"
    r"|\bposso (?:ter|estar|vir a ter)(?: \w+){0,1} ?$"
)


def _inicio_da_oracao(texto: str, posicao: int) -> int:
    inicio = 0
    for m in _FIM_DE_ORACAO.finditer(texto, 0, posicao):
        inicio = m.end()
    return inicio


def _negado(texto: str, posicao: int) -> bool:
    trecho = texto[_inicio_da_oracao(texto, posicao):posicao]
    tokens = re.findall(r"[a-z0-9]+", trecho)[-JANELA_NEGACAO:]
    for i, token in enumerate(tokens):
        if token in NEGACOES:
            if any(t in NEUTRALIZADORES for t in tokens[i + 1:]):
                continue
            return True
    return False


def _informativo(texto: str, posicao: int) -> bool:
    trecho = texto[_inicio_da_oracao(texto, posicao):posicao]
    return bool(_INFORMATIVO.search(trecho) or _NAO_RELATO.search(trecho))


_TERCEIRO = re.compile(
    r"\b(?:meu|minha|meus|minhas|o|a|seu|sua) (?:marido|esposo|namorado|noivo|companheir[oa]|filh[oa]s?|"
    r"mae|pai|irma|irmao|sogr[oa]|amig[oa]s?|vizinh[oa]|cachorr[oa]|gat[oa]|cunhad[oa]|prim[oa]|ti[oa]|"
    r"avo|colega|chefe|sobrinh[oa]|entead[oa])\b"
)
_PRIMEIRA_PESSOA = re.compile(r"\b(?:eu|estou|tive|tenho|me|comigo|em mim|minha barriga|meu corpo)\b")
_EU_TAMBEM = re.compile(r"\b(?:eu tambem|e eu|eu e (?:ele|ela)|nos dois|nos duas|nos tres|nos estamos|ambos|ambas)\b")


def _de_terceiro(texto: str, posicao: int) -> bool:
    """'Minha filha teve febre' fala de outra pessoa. 'Meu filho me passou febre' não."""
    inicio = _inicio_da_oracao(texto, posicao)
    trecho = texto[inicio:posicao]
    ultimo = None
    for m in _TERCEIRO.finditer(trecho):
        ultimo = m
    if ultimo is None or _PRIMEIRA_PESSOA.search(trecho[ultimo.end():]):
        return False
    fim = _FIM_DE_FRASE.search(texto, posicao)
    frase = texto[inicio:fim.start() if fim else len(texto)]
    return not _EU_TAMBEM.search(frase)


def _pergunta_hipotetica(texto: str, posicao: int, fim: int) -> bool:
    """'O que fazer se a bolsa estourar?' é dúvida, não relato."""
    proximo = _FIM_DE_FRASE.search(texto, fim)
    if not proximo or proximo.group() != "?":
        return False
    trecho = texto[_inicio_da_oracao(texto, posicao):posicao]
    return bool(_HIPOTESE.search(trecho))


# ---------------------------------------------------------------------------
# 3. Sinais
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sinal:
    codigo: str
    descricao: str
    nivel: str                      # urgente | atencao
    padroes: Tuple[str, ...]
    negavel: bool = True            # False: a negação faz parte do sinal ("não sinto o bebê")
    excecoes_locais: Tuple[str, ...] = ()   # se aparecerem perto, a ocorrência não conta
    raio_excecao: int = 40
    terceiros_excluem: bool = True  # "minha filha teve febre" não é sinal da gestante
    anula_excecao: Tuple[str, ...] = ()  # se aparecerem na oração, a exceção local não vale


_SANGUE_LABORATORIO = (
    r"exame\w*(?: \w+){0,2} (?:de |do )?sangue", r"coleta\w*(?: \w+){0,2} (?:de )?sangue",
    r"amostra\w* (?:de )?sangue", r"tipo sangu", r"tipo (?:de )?sangue", r"tubo (?:de )?sangue",
    r"pressao (?:do )?sangue", r"(?:acucar|glicose|ferro|hemoglobina|plaqueta\w*) no sangue",
    r"doa\w* (?:de )?sangue", r"\bdo(?:ei|ou|ar|ando|amos) (?:de )?sangue", r"tirar sangue", r"tirei sangue", r"tiraram sangue",
    r"sangue bom", r"sangue frio", r"sangue quente", r"sangue nos olhos",
    r"furar o dedo", r"exame de sangue",
)

_SANGUE_FORA_DO_UTERO = (
    r"nariz", r"gengiva", r"dente", r"escov\w*", r"boca", r"machuc\w* (?:o|a|no|na) (?:dedo|mao|joelho|pe|perna)",
    r"vomit\w*", r"toss\w*", r"cusp\w*", r"escarr\w*", r"fezes", r"\bcoco\b", r"evacu\w*", r"hemorroid\w*",
    r"cort\w* (?:o|a|no|na) (?:dedo|mao)", r"espinha", r"unha",
)

SINAIS: Tuple[Sinal, ...] = (
    # --- Sangramento -------------------------------------------------------
    Sinal(
        "sangramento", "Sangramento vaginal", "urgente",
        (r"\bsangr\w*", r"\bsangue\b", r"\bhemorragi\w*", r"\bcoagulos?\b",
         r"\bescape\b", r"\bborra de cafe\b", r"\bmancha\w*(?: \w+){0,2} (?:de )?sangue",
         r"\bcalcinha(?: \w+){0,2} (?:suja|manchada|vermelha)"),
        excecoes_locais=_SANGUE_LABORATORIO + _SANGUE_FORA_DO_UTERO,
        anula_excecao=(r"vagin\w*", r"calcinha", r"absorvente", r"parte intima", r"partes intimas",
                       r"por baixo", r"la embaixo", r"\butero\b", r"placenta", r"bebe"),
    ),
    Sinal(
        "sangue_urina_fezes", "Sangue na urina ou nas fezes", "atencao",
        (r"\bsangue(?: \w+){0,2} (?:na|no|nas|nos) (?:urina|fezes|coco)",
         r"\b(?:urina|fezes|coco)(?: \w+){0,2} com sangue", r"\bhemorroida\w*(?: \w+){0,3} sangr\w*"),
    ),

    # --- Perda de líquido --------------------------------------------------
    Sinal(
        "liquido", "Perda de líquido (possível rompimento da bolsa)", "urgente",
        (r"\bbolsa(?: \w+){0,3} (?:romp\w*|estour\w*|estor\w*|fur\w*|vaz\w*|quebr\w*)",
         r"\b(?:romp\w*|estour\w*|fur\w*) (?:a |minha )?bolsa",
         r"\bperd\w*(?: \w+){0,2} (?:de )?(?:liquido|agua)\b",
         r"\bliquido(?: \w+){0,4} (?:escorr\w*|sai\w*|vaz\w*|desc\w*|molh\w*|pelas? pernas?)",
         r"\b(?:escorr\w*|sai\w*|vaz\w*|desc\w*)(?: \w+){0,4} (?:liquido|agua)\b",
         r"\bagua(?: \w+){0,3} (?:escorr\w*|pelas? pernas?)",
         r"\bescorr\w*(?: \w+){0,4} pelas? pernas?",
         r"\b(?:calcinha|roupa|cama|lencol)(?: \w+){0,2} (?:molhad\w*|encharcad\w*)(?! de suor)",
         r"\bmolh\w*(?: \w+){0,3} sem (?:fazer|ter feito) urina",
         r"\bmolh\w*(?: \w+){0,4} (?:e )?(?:nao|nem) (?:e|foi|era|parece) urina",
         r"\bmolh\w*(?: \w+){0,2} (?:a |toda a |toda |tudo a )?(?:cama|calcinha|lencol|roupa|sofa)"),
    ),

    # --- Movimentos do bebê (a negação FAZ parte do sinal) -----------------
    Sinal(
        "movimentos", "Bebê mexendo menos ou parado", "urgente",
        (r"\b(?:nao|nem)(?: \w+){0,3} (?:sinto|senti|sentindo|sentiu|sente|sentido|sentir|percebo|percebi|percebendo|percebido|perceber)(?: \w+){0,3} (?:o bebe|bebe|ele|ela|mexer|mexendo|mexe|chute\w*|chutar|movimento\w*)",
         r"\bbebe(?: \w+){0,3} (?:nao|nem)(?: \w+){0,2} (?:mex\w*|se mex\w*|chut\w*|movimen\w*)",
         r"\bbebe(?: \w+){0,2} (?:parad[oa]|quiet[oa]|paradinh[oa]|quietinh[oa]|parou)\b",
         r"\bparou de (?:se )?(?:mex\w*|chut\w*|movimen\w*)",
         r"\b(?:mex\w*|chut\w*|movimen\w*)(?: \w+){0,3} (?:pouco|pouquinho|menos|fraco|fracos|fraquinho|diminu\w*|reduz\w*|quase nada)\b",
         r"\b(?:diminu\w*|reduz\w*|menos|poucos?|fraco\w*)(?: \w+){0,2} (?:mex\w*|chut\w*|movimen\w*)",
         r"\bfaz (?:um dia|\d+ ?h\w*|\d+ dias?|horas|muito tempo|desde ontem|desde cedo|desde manha)(?: \w+){0,3} (?:que )?(?:nao|nem) (?:sinto|senti|percebo|mex\w*)",
         r"\bsem (?:sentir|perceber)(?: \w+){0,2} (?:o bebe|bebe|ele|ela|mex\w*|movimento\w*|chute\w*)",
         r"\b(?:ausencia|falta) de movimento\w*",
         r"\b(?:ele|ela)(?: \w+){0,2} (?:nao|nem)(?: \w+){0,2} (?:mex\w*|se mex\w*|chut\w*|movimen\w*)",
         r"\b(?:nao|nem)(?: esta| ta| tem| anda| estava)? (?:se mex\w*|mexendo|chutando|se movimentando)",
         r"\b(?:nao|nem) (?:mexe|mexeu|chuta|chutou)\b(?: \w+){0,2} (?:mais|desde|ha|faz|hoje|direito|nada)",
         r"\bsinto (?:o bebe|ele|ela|os? movimentos?|os? chutes?)(?: \w+){0,2} (?:fraco\w*|fraquinh\w*|pouco|menos|diferente|estranho)",
         r"\b(?:nenhum|zero|sem) (?:movimento\w*|chute\w*|mexid\w*)\b(?! (?:estranh|diferent|anormal|esquisit|brusc))",
         r"\b(?:ele|ela)(?: \w+){0,2} (?:parad[oa]|quiet[oa]|paradinh[oa]|quietinh[oa])\b"),
        negavel=False,
        terceiros_excluem=False,
    ),

    # --- Contrações / trabalho de parto -----------------------------------
    Sinal(
        "contracoes", "Contrações regulares ou dolorosas (possível trabalho de parto)", "urgente",
        (r"\bcontra\w*(?: \w+){0,4} (?:de|a cada) \d{1,2}(?: em \d{1,2})? ?min",
         r"\bcontra\w*(?: \w+){0,3} (?:ritmad\w*|regular\w*|forte\w*|doloros\w*|seguid\w*|frequent\w*|toda hora|continua\w*|persistente|cada vez mais)",
         r"\b(?:muitas|varias|vindo|com) contra\w*",
         r"\btrabalho de parto\b", r"\bdor(?:es)? de parto\b", r"\bentrei em trabalho\b",
         r"\bcontra\w* atras de contra\w*", r"\buma contra\w*(?: \w+){0,2} atras da outra\b",
         r"\bcontra\w*(?: \w+){0,2} (?:o tempo todo|sem parar|uma atras da outra)",
         r"\bbarriga(?: \w+){0,2} (?:dura|endurec\w*)(?: \w+){0,3} (?:com dor|e dor|doendo|doi|doe|dolorida|toda hora|varias vezes|de \d+ em \d+)",
         r"\b(?:pressao|peso|dor) (?:muito )?forte (?:no|na) (?:pe da barriga|vagina|pelve|bacia)"),
    ),
    Sinal(
        "contracoes_leves", "Contrações ou barriga endurecendo", "atencao",
        (r"\bcontra\w*", r"\bbarriga(?: \w+){0,2} (?:dura|endurec\w*)"),
    ),

    # --- Pré-eclâmpsia: dor de cabeça, visão, estômago, inchaço, pressão ---
    Sinal(
        "cefaleia_forte", "Dor de cabeça forte ou que não passa", "urgente",
        (r"\b(?:dor de cabeca|cefaleia|enxaqueca)(?: \w+){0,4} (?:forte\w*|fortissim\w*|intens\w*|insuportave\w*|horrive\w*|terrive\w*|persistente|continua|latejante|pulsatil|subit\w*|o dia todo|desde ontem|ha \d+|faz \d+|muito)",
         r"\b(?:forte\w*|intens\w*|insuportave\w*|horrive\w*|terrive\w*|pior) dor de cabeca",
         r"\bcabeca(?: \w+){0,2} (?:explodindo|estourando|vai explodir|latejando muito|doendo muito|doendo demais)"),
    ),
    Sinal(
        "cefaleia", "Dor de cabeça", "atencao",
        (r"\bdor de cabeca\b", r"\bcefaleia\b", r"\benxaqueca\b", r"\bcabeca(?: \w+){0,2} doendo\b"),
    ),
    Sinal(
        "visao", "Alteração na visão (embaçada, escura, pontos brilhantes)", "urgente",
        (r"\b(?:visao|vista)(?: \w+){0,2} (?:embac\w*|turv\w*|escur\w*|dupla|borrad\w*|estranh\w*|ruim|falhando|piscando)",
         r"\b(?:embac\w*|escurec\w*|turv\w*)(?: \w+){0,2} (?:a )?(?:visao|vista)",
         r"\bpont(?:os?|inhos?)(?: \w+){0,2} (?:brilhantes?|luminosos?|pretos?|escuros?|de luz)",
         r"\b(?:vendo|enxergando|aparecendo|aparecem|aparece|surgindo|surgem)(?: \w+){0,2} (?:pontinhos|pontos|estrelinhas|luzes|brilhos|flashes|manchas|tudo embac\w*|tudo escuro|tudo turvo)",
         r"\b(?:pontinhos|pontos|manchas|estrelinhas|brilhos)(?: \w+){0,3} (?:na vista|na visao|nos olhos|no olho|na frente dos olhos)",
         r"\bestrelinhas\b", r"\bescotomas?\b", r"\bflashes de luz\b", r"\bluzes piscando\b",
         r"\bperdi a visao\b", r"\bnao (?:estou |consigo )?enxergar\b"),
        negavel=True,
    ),
    Sinal(
        "epigastrica_forte", "Dor forte na boca do estômago ou em barra", "urgente",
        (r"\bdor(?: \w+){0,2} (?:forte\w*|intens\w*|insuportave\w*|muito forte|horrive\w*)(?: \w+){0,3} (?:estomago|boca do estomago|epigastri\w*|costelas)",
         r"\b(?:estomago|boca do estomago|epigastri\w*)(?: \w+){0,3} (?:forte\w*|intens\w*|insuportave\w*|persistente)",
         r"\bdor em barra\b", r"\bdor(?: \w+){0,2} (?:abaixo|embaixo|debaixo) das costelas\b",
         r"\bdor(?: \w+){0,3} lado direito(?: \w+){0,2} (?:costelas|figado|barriga de cima)"),
    ),
    Sinal(
        "epigastrica", "Dor no estômago", "atencao",
        (r"\bdor(?: \w+){0,2} (?:no|na) (?:estomago|boca do estomago)", r"\bestomago doendo\b",
         r"\bdor epigastri\w*"),
    ),
    Sinal(
        "edema_subito", "Inchaço repentino no rosto ou nas mãos", "urgente",
        (r"\b(?:inch\w*|edema)(?: \w+){0,4} (?:de repente|do nada|repentin\w*|subit\w*|de uma hora pra outra|muito rapido)",
         r"\b(?:de repente|do nada|subitamente)(?: \w+){0,4} (?:inch\w*|edema)"),
    ),
    Sinal(
        "edema_face_maos", "Inchaço no rosto ou nas mãos", "atencao",
        (r"\b(?:inch\w*|edema)(?: \w+){0,4} (?:rosto|face|cara|olhos|palpebras?|maos|dedos)",
         r"\b(?:rosto|face|cara|olhos|palpebras?|maos|dedos)(?: \w+){0,3} (?:inch\w*)"),
    ),
    Sinal(
        "pressao_alta", "Pressão alta relatada", "urgente",
        (r"\bpressao(?: \w+){0,3} (?:alta|subiu|subindo|elevad\w*|nas alturas|altissima|descontrolad\w*)",
         r"\bhipertens\w*(?: \w+){0,2} (?:hoje|agora|de novo|subiu|alta)", r"\bpico de pressao\b",
         r"\bpre ?eclampsia\b", r"\beclampsia\b", r"\bsindrome hellp\b|\bhellp\b"),
    ),

    # --- Infecção / febre --------------------------------------------------
    Sinal(
        "febre", "Febre", "urgente",
        (r"\bfebre\b", r"\bfebril\b", r"\bcalafrio\w*(?: \w+){0,2} (?:forte\w*|intens\w*|muito|tremendo)",
         r"\bqueimando de febre\b"),
    ),
    Sinal(
        "urinario", "Ardência ou dor ao urinar", "atencao",
        (r"\b(?:ardencia|ardor|queima\w*|dor|incomodo)(?: \w+){0,3} (?:ao|pra|para|quando|na hora de) (?:urinar|fazer urina)",
         r"\burina(?: \w+){0,2} (?:ardendo|queimando|doendo|com cheiro forte|turva|escura)",
         r"\binfeccao urinaria\b", r"\bcistite\b"),
    ),
    Sinal(
        "dor_lombar", "Dor nas costas (lombar)", "atencao",
        (r"\bdor(?: \w+){0,3} (?:nas costas|na lombar|no rim|nos rins|lombar)",),
    ),
    Sinal(
        "corrimento", "Corrimento diferente (cor, cheiro ou coceira)", "atencao",
        (r"\bcorrimento(?: \w+){0,3} (?:verde\w*|amarel\w*|cinza|marrom|com cheiro|fedido|mau cheiro|forte|coceira|grosso|aguado|transparente|abundante)",
         r"\bcorrimento\b"),
    ),

    # --- Dor abdominal, falta de ar, peito ---------------------------------
    Sinal(
        "dor_abdominal_forte", "Dor forte na barriga", "urgente",
        (r"\bdor(?: \w+){0,2} (?:forte\w*|intens\w*|insuportave\w*|muito forte|horrive\w*|aguda|absurda)(?: \w+){0,3} (?:barriga|abdome|abdomen|ventre|pe da barriga|utero)",
         r"\b(?:barriga|abdome|abdomen|ventre|utero)(?: \w+){0,3} (?:doendo muito|dor forte|dor intensa|dor insuportavel|dura e doendo)",
         r"\bcolica\w*(?: \w+){0,2} (?:forte\w*|intens\w*|insuportave\w*|muito forte)"),
    ),
    Sinal(
        "dor_abdominal", "Dor na barriga", "atencao",
        (r"\bdor(?: \w+){0,2} (?:na|no) (?:barriga|abdome|abdomen|ventre|pe da barriga)", r"\bbarriga doendo\b"),
    ),
    Sinal(
        "falta_de_ar_grave", "Falta de ar forte ou dor no peito", "urgente",
        (r"\bfalta de ar(?: \w+){0,3} (?:forte|muito|intens\w*|deitada|parada|em repouso|de repente|piorando)",
         r"\b(?:muita|forte|grande) falta de ar\b",
         r"\bnao (?:estou |to )?consigo respirar\b", r"\bnao consigo respirar\b", r"\bdificuldade (?:para|pra|de) respirar\b",
         r"\bsufoc\w*", r"\blabios? (?:roxos?|azulad\w*)", r"\bdor no peito\b", r"\baperto no peito\b", r"\bdor toracica\b"),
        negavel=True,
    ),
    Sinal(
        "falta_de_ar", "Falta de ar", "atencao",
        (r"\bfalta de ar\b", r"\bcansaco para respirar\b", r"\bofegante\b"),
    ),

    # --- Neurológico, consciência, trauma ----------------------------------
    Sinal(
        "convulsao", "Convulsão ou desmaio", "urgente",
        (r"\bconvuls\w*", r"\bataque epilept\w*", r"\bdesmai\w*", r"\bperdi (?:os sentidos|a consciencia)\b",
         r"\bperda de (?:consciencia|sentidos)\b", r"\bdesacordad\w*", r"\bapaguei\b"),
    ),
    Sinal(
        "tontura", "Tontura ou quase desmaio", "atencao",
        (r"\btontur\w*", r"\bquase desmai\w*", r"\bvista (?:rodando|girando)\b", r"\bmundo girando\b"),
    ),
    Sinal(
        "trauma", "Queda, batida na barriga ou agressão", "urgente",
        (r"\b(?:levei|tomei|sofri|tive) (?:um |uma )?(?:tombo|queda)\b",
         r"\b(?:escorreguei|tropecei|desequilibrei)(?: \w+){0,2} (?:e )?cai\b",
         r"\bcai (?:da|de|na|no|em) (?:escada|cama|chao|rua|calcada|bicicleta|moto|cadeira|banheiro|altura|costas|bunda|barriga|joelho\w*|sofa)",
         r"\b(?:bati|batida|pancada)(?: \w+){0,2} (?:a |na |minha )?barriga",
         r"\bacidente (?:de carro|de moto|de transito|de onibus)\b", r"\bbateram no (?:meu )?carro\b",
         r"\b(?:me )?(?:bateu|bateram|socou|chutou|empurrou|agrediu|agrediram|espancou)(?: \w+){0,2} (?:em mim|na minha barriga|na barriga|me derrubou)",
         r"\bapanhei\b",
         r"\b(?:levei|tomei|recebi) (?:um |uma )?(?:soco|chute|tapa|pancada|empurrao|murro|pontape|cotovelada)",
         r"\b(?:soco|chute|murro|pancada|pontape|cotovelada)(?: \w+){0,2} (?:na|minha) barriga", r"\b(?:sofri|sofrendo) (?:violencia|agressao)\b", r"\bme (?:bateu|bateram|agrediu|agrediram|empurrou|empurraram)\b",
         r"\b(?:quer|querendo|ameac\w*|vai|disse que vai) me (?:matar|bater|machucar|agredir|espancar)"),
        terceiros_excluem=False,
    ),

    # --- Vômitos, glicemia, coceira ----------------------------------------
    Sinal(
        "vomito_grave", "Vômitos que não param ou com sangue", "urgente",
        (r"\bvomit\w*(?: \w+){0,3} (?:com sangue|sangue|sem parar|o dia todo|continua\w*|tudo que (?:como|bebo))",
         r"\bnao (?:consigo|paro de|para de) (?:segurar|manter|beber)(?: \w+){0,2} (?:nada|nem agua|agua)",
         r"\bnem agua para no estomago\b", r"\bdesidrat\w*"),
    ),
    Sinal(
        "vomito", "Vômitos", "atencao",
        (r"\bvomit\w*",),
    ),
    Sinal(
        "hipoglicemia", "Hipoglicemia (açúcar baixo)", "atencao",
        (r"\bhipoglicemia\b", r"\bacucar (?:muito )?baixo\b", r"\bglicemia (?:muito )?baixa\b"),
    ),
    Sinal(
        "coceira", "Coceira forte nas mãos ou nos pés", "atencao",
        (r"\bcoceira(?: \w+){0,3} (?:maos|palmas|pes|solas|corpo todo)", r"\bcoca\w*(?: \w+){0,3} (?:maos|palmas|pes|solas)"),
    ),

    # --- Saúde emocional grave ---------------------------------------------
    Sinal(
        "sofrimento_grave", "Sofrimento emocional intenso com risco à vida", "urgente",
        (r"\b(?:quero|queria|vontade de|penso em|pensando em|pensei em|vou|pensamentos? de)(?: \w+){0,2} (?:me matar|morrer(?! de)|sumir de vez|acabar com (?:tudo|a minha vida|minha vida))",
         r"\bnao (?:quero|aguento) mais viver\b", r"\btirar (?:a )?minha (?:propria )?vida\b",
         r"\bsuicid\w*", r"\bme (?:machucar|cortar|ferir)\b", r"\b(?:machucar|fazer mal (?:a|ao|pro|para o)) (?:o )?bebe\b",
         r"\bmelhor (?:eu )?morrer\b", r"\bmelhor se eu nao existisse\b"),
        negavel=False,
        terceiros_excluem=False,
    ),
)

_SINAIS_COMPILADOS = [
    (s, [re.compile(p) for p in s.padroes], [re.compile(e) for e in s.excecoes_locais],
     [re.compile(a) for a in s.anula_excecao])
    for s in SINAIS
]

# Sinais de atenção cobertos por um sinal urgente mais específico
_COBERTO_POR = {
    "contracoes_leves": "contracoes",
    "cefaleia": "cefaleia_forte",
    "epigastrica": "epigastrica_forte",
    "edema_face_maos": "edema_subito",
    "dor_abdominal": "dor_abdominal_forte",
    "falta_de_ar": "falta_de_ar_grave",
    "vomito": "vomito_grave",
}

# Combinações que viram urgentes mesmo com cada sinal sozinho sendo "atenção"
_GRUPO_PRE_ECLAMPSIA = {"cefaleia", "cefaleia_forte", "visao", "epigastrica", "epigastrica_forte",
                        "edema_face_maos", "edema_subito", "pressao_alta", "pressao_numerica"}


# ---------------------------------------------------------------------------
# 4. Números: pressão, temperatura, glicemia
# ---------------------------------------------------------------------------

_PRESSAO_POR = re.compile(r"\b(\d{2,3})(?:[.,]\d)? ?(?:por|x) ?(\d{1,3})(?:[.,]\d)?\b")
_PRESSAO_BARRA = re.compile(r"\b(?:pressao|pa|mmhg)\b[^\d\n]{0,25}(\d{2,3}) ?/ ?(\d{1,3})\b")
_TEMPERATURA = re.compile(r"\b(3[5-9]|4[0-2])(?:[.,](\d))? ?(?:graus|°|ºc|°c|c\b)")
_TEMPERATURA_CONTEXTO = re.compile(r"\b(?:febre|temperatura|termometro)\b[^\d\n]{0,25}(3[5-9]|4[0-2])(?:[.,](\d))?\b")
_TEMPERATURA_DEPOIS = re.compile(r"\b(3[5-9]|4[0-2])(?:[.,](\d))? (?:de )?(?:temperatura|febre)\b")
_GLICEMIA = re.compile(r"\b(?:glicemia|glicose|dextro|hgt|glicosimetro|ponta de dedo)(?: \w+){0,3} (\d{2,3})\b")


def _pressao_em_mmhg(sistolica: int, diastolica: int) -> Optional[Tuple[int, int]]:
    if 9 <= sistolica <= 26 and 5 <= diastolica <= 16:      # "14 por 9" (cmHg)
        return sistolica * 10, diastolica * 10
    if 70 <= sistolica <= 260 and 40 <= diastolica <= 160:  # "140 por 90" (mmHg)
        return sistolica, diastolica
    return None


def pressao_em_mmhg(sistolica: int, diastolica: int) -> Optional[Tuple[int, int]]:
    """Versão pública: "14 por 9" (cmHg) ou "140/90" (mmHg) viram (140, 90). None se não fizer sentido."""
    leitura = _pressao_em_mmhg(sistolica, diastolica)
    if leitura and leitura[0] > leitura[1]:
        return leitura
    return None


def _ler_numeros(texto: str) -> Tuple[List[Tuple[str, str, str]], List[str]]:
    """Devolve (sinais [(codigo, descricao, nivel)], números lidos para registro)."""
    achados: List[Tuple[str, str, str]] = []
    leituras: List[str] = []

    pares = [(m.start(), m.group(1), m.group(2)) for m in _PRESSAO_POR.finditer(texto)]
    pares += [(m.start(), m.group(1), m.group(2)) for m in _PRESSAO_BARRA.finditer(texto)]
    for posicao, s, d in pares:
        mmhg = _pressao_em_mmhg(int(s), int(d))
        if not mmhg or _negado(texto, posicao) or _de_terceiro(texto, posicao):
            continue
        sis, dia = mmhg
        leituras.append(f"pressão {sis}/{dia} mmHg")
        if sis >= 160 or dia >= 110:
            achados.append(("pressao_numerica", f"Pressão muito alta ({sis}/{dia})", "urgente"))
        elif sis >= 140 or dia >= 90:
            achados.append(("pressao_numerica", f"Pressão alta ({sis}/{dia})", "urgente"))

    temperaturas = [(m.start(), m.group(1), m.group(2)) for m in _TEMPERATURA.finditer(texto)]
    temperaturas += [(m.start(), m.group(1), m.group(2)) for m in _TEMPERATURA_CONTEXTO.finditer(texto)]
    temperaturas += [(m.start(), m.group(1), m.group(2)) for m in _TEMPERATURA_DEPOIS.finditer(texto)]
    for posicao, inteiro, decimal in temperaturas:
        valor = float(f"{inteiro}.{decimal or 0}")
        if _negado(texto, posicao) or _de_terceiro(texto, posicao):
            continue
        leituras.append(f"temperatura {valor:.1f} °C")
        if valor >= 37.8:
            achados.append(("febre", f"Febre ({valor:.1f} °C)", "urgente"))
        elif valor >= 37.5:
            achados.append(("febricula", f"Temperatura um pouco alta ({valor:.1f} °C)", "atencao"))

    for m in _GLICEMIA.finditer(texto):
        if _de_terceiro(texto, m.start()):
            continue
        valor = int(m.group(1))
        leituras.append(f"glicemia {valor} mg/dL")
        if valor < 60:
            achados.append(("hipoglicemia_numerica", f"Glicemia baixa ({valor} mg/dL)", "urgente"))
        elif valor >= 250:
            achados.append(("hiperglicemia", f"Glicemia muito alta ({valor} mg/dL)", "atencao"))

    return achados, leituras


# ---------------------------------------------------------------------------
# 5. Avaliação
# ---------------------------------------------------------------------------

@dataclass
class Avaliacao:
    nivel: str = "nenhum"                      # urgente | atencao | nenhum
    urgentes: List[str] = field(default_factory=list)
    atencoes: List[str] = field(default_factory=list)
    codigos: List[str] = field(default_factory=list)
    leituras: List[str] = field(default_factory=list)
    orientacao: str = ""

    @property
    def urgente(self) -> bool:
        return self.nivel == "urgente"


def _ocorrencia_valida(sinal: Sinal, excecoes, anuladores, texto: str, m: re.Match) -> bool:
    if excecoes:
        ini = max(0, m.start() - sinal.raio_excecao)
        fim = min(len(texto), m.end() + sinal.raio_excecao)
        # A exceção só vale dentro da mesma oração
        ini = max(ini, _inicio_da_oracao(texto, m.start()))
        proximo = _FIM_DE_ORACAO.search(texto, m.end())
        if proximo:
            fim = min(fim, proximo.start())
        vizinhanca = texto[ini:fim]
        if any(e.search(vizinhanca) for e in excecoes) and not any(a.search(vizinhanca) for a in anuladores):
            return False
    if sinal.negavel and _negado(texto, m.start()):
        return False
    if sinal.terceiros_excluem and _de_terceiro(texto, m.start()):
        return False
    if _informativo(texto, m.start()):
        return False
    if _pergunta_hipotetica(texto, m.start(), m.end()):
        return False
    return True


def _encontrar_sinais(texto: str) -> List[Tuple[str, str, str]]:
    achados = []
    for sinal, padroes, excecoes, anuladores in _SINAIS_COMPILADOS:
        for padrao in padroes:
            if any(_ocorrencia_valida(sinal, excecoes, anuladores, texto, m) for m in padrao.finditer(texto)):
                achados.append((sinal.codigo, sinal.descricao, sinal.nivel))
                break
    return achados


# Mapa das opções de marcar do check-in. Cada opção vira um sinal sem passar
# por interpretação de texto. Opção que não está aqui é lida como texto livre.
SINTOMAS_ESTRUTURADOS = {
    "sangramento vaginal": ("sangramento", "Sangramento vaginal", "urgente"),
    "perda de liquido": ("liquido", "Perda de líquido (possível rompimento da bolsa)", "urgente"),
    "bebe mexendo menos": ("movimentos", "Bebê mexendo menos ou parado", "urgente"),
    "contracoes ritmadas ou dolorosas": ("contracoes", "Contrações regulares ou dolorosas (possível trabalho de parto)", "urgente"),
    "febre (37,8 °c ou mais)": ("febre", "Febre", "urgente"),
    "febre": ("febre", "Febre", "urgente"),
    "dor de cabeca forte": ("cefaleia_forte", "Dor de cabeça forte ou que não passa", "urgente"),
    "visao embacada": ("visao", "Alteração na visão (embaçada, escura, pontos brilhantes)", "urgente"),
    "pressao 14 por 9 ou mais": ("pressao_numerica", "Pressão alta (14 por 9 ou mais)", "urgente"),
    "falta de ar forte": ("falta_de_ar_grave", "Falta de ar forte ou dor no peito", "urgente"),
    "inchaco no rosto ou nas maos": ("edema_face_maos", "Inchaço no rosto ou nas mãos", "atencao"),
    "dor de cabeca": ("cefaleia", "Dor de cabeça", "atencao"),
    "dor no estomago": ("epigastrica", "Dor no estômago", "atencao"),
    "ardencia ao urinar": ("urinario", "Ardência ou dor ao urinar", "atencao"),
    "coceira forte nas maos ou pes": ("coceira", "Coceira forte nas mãos ou nos pés", "atencao"),
    "dor nas costas": ("dor_lombar", "Dor nas costas (lombar)", "atencao"),
    # Opções comuns que não são sinal de alerta por si só
    "nausea / enjoo": None,
    "azia / queimacao": None,
    "inchaco nas pernas": None,
    "colicas leves": None,
    "cansaco excessivo": None,
}

ORIENTACAO_URGENTE = (
    "ALERTA CLÍNICO DE URGÊNCIA: o que você descreveu ({sinais}) precisa de avaliação agora. "
    "Isto não é um diagnóstico. Vá imediatamente à maternidade ou ao pronto-socorro obstétrico "
    "mais próximo, ou ligue 192 (SAMU)."
)
ORIENTACAO_SOFRIMENTO = (
    " Você não está sozinha. Se estiver pensando em se machucar, ligue agora para o CVV no 188 "
    "(gratuito, 24 horas) ou para o SAMU no 192, e peça para alguém de confiança ficar com você."
)
ORIENTACAO_ATENCAO = (
    "ATENÇÃO: registramos {sinais}. Fale hoje com a equipe do seu pré-natal ou com a unidade de saúde. "
    "Se piorar, ou se aparecer sangramento, perda de líquido, dor forte, febre, visão embaçada, "
    "dor de cabeça forte ou o bebê mexer menos, vá à maternidade ou ligue 192 (SAMU)."
)


def avaliar(texto: str = "", sintomas: Optional[Iterable[str]] = None) -> Avaliacao:
    """Avalia texto livre e opções marcadas. Usada pelo check-in, chat e comunidade."""
    achados: List[Tuple[str, str, str]] = []
    textos_livres = [texto or ""]

    for sintoma in sintomas or []:
        chave = normalizar(sintoma)
        if chave in SINTOMAS_ESTRUTURADOS:
            item = SINTOMAS_ESTRUTURADOS[chave]
            if item:
                achados.append(item)
        else:
            textos_livres.append(sintoma)

    leituras: List[str] = []
    for bruto in textos_livres:
        normal = normalizar(bruto)
        if not normal:
            continue
        # Números primeiro: "Febre (38.5 °C)" é mais útil para a equipe do que "Febre"
        numeros, lidos = _ler_numeros(normal)
        achados.extend(numeros)
        leituras.extend(lidos)
        achados.extend(_encontrar_sinais(normal))

    codigos = {c for c, _, _ in achados}

    # Combinações
    sinais_pre_eclampsia = codigos & _GRUPO_PRE_ECLAMPSIA
    if len(sinais_pre_eclampsia) >= 2:
        achados.append(("conjunto_pre_eclampsia",
                        "Conjunto de sinais de pré-eclâmpsia (dor de cabeça, visão, estômago, inchaço ou pressão)",
                        "urgente"))
    if "urinario" in codigos and ({"febre", "dor_lombar"} & codigos):
        achados.append(("infeccao_urinaria_alta", "Ardência ao urinar com febre ou dor nas costas", "urgente"))

    avaliacao = Avaliacao(leituras=leituras)
    vistos = set()
    codigos_urgentes = {c for c, _, n in achados if n == "urgente"}
    for codigo, descricao, nivel in achados:
        if codigo in vistos:
            continue
        if nivel == "atencao" and _COBERTO_POR.get(codigo) in codigos_urgentes:
            continue
        vistos.add(codigo)
        avaliacao.codigos.append(codigo)
        (avaliacao.urgentes if nivel == "urgente" else avaliacao.atencoes).append(descricao)

    if avaliacao.urgentes:
        avaliacao.nivel = "urgente"
        avaliacao.orientacao = ORIENTACAO_URGENTE.format(sinais=", ".join(avaliacao.urgentes))
        if "sofrimento_grave" in avaliacao.codigos:
            avaliacao.orientacao += ORIENTACAO_SOFRIMENTO
    elif avaliacao.atencoes:
        avaliacao.nivel = "atencao"
        avaliacao.orientacao = ORIENTACAO_ATENCAO.format(sinais=", ".join(a.lower() for a in avaliacao.atencoes))
    return avaliacao


def analyze_urgency(text: str) -> Tuple[bool, List[str], str]:
    """
    Interface antiga, mantida para o chat, a comunidade e a prévia do check-in.
    Devolve (é urgente, sinais urgentes, orientação).
    """
    resultado = avaliar(text)
    if resultado.urgente:
        return True, resultado.urgentes, resultado.orientacao
    return False, [], ""
