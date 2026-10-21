"""
Relatório para a consulta (18/10/2026).

PDF que a profissional vinculada gera no prontuário da gestante antes da
consulta. Reúne o que a gestante registrou no app no período (desde a última
consulta da agenda) e o que a própria profissional anotou.

Regras:
  - a lista de pontos de atenção aponta fatos registrados, nunca conduta: a
    avaliação e a decisão são do profissional (Resolução CFM nº 2.454/2026, art. 4º);
  - se a gestante recusou a IA (art. 5º, § 3º), o relatório não traz as
    estimativas dos modelos;
  - conversas com a IA só entram se a gestante autorizou o compartilhamento;
  - as anotações são só as da profissional que gera o relatório.
"""
import io
import re
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models.auth import Gestante, Profissional
from app.models.clinical import (
    CheckinRegistro, Exame, HistoricoFamiliar, PerfilClinico, RegistroAntropometrico, TriagemEPDS,
)
from app.models.governance import ObservacaoProfissional
from app.models.interaction import EventoAgenda, EventoEmergencia, Mensagem
from app.services.ai_risk_service import CARIMBO_PRONTUARIO, calculate_maternal_risks, perfil_para_modelos

# O banco guarda UTC sem fuso; o relatório mostra o horário de Brasília (sem
# horário de verão desde 2019).
FUSO_BRASILIA = timedelta(hours=-3)
DIAS_SEM_CONSULTA_NA_AGENDA = 30
DIAS_MAXIMOS_DESDE_A_CONSULTA = 60
DIAS_MINIMOS_DO_PERIODO = 7
DIAS_SEM_CHECKIN_PARA_AVISAR = 7
CORTE_EPDS = 10
LIMITE_CHECKINS = 40
LIMITE_RELATOS = 15
LIMITE_CONVERSAS = 15
LIMITE_ANOTACOES = 10

ROTULO_NIVEL = {"alto": "Alto", "moderado": "Aumentado", "baixo": "Habitual"}
ROTULO_EPDS = {
    "urgente": "Pergunta 10 positiva",
    "atencao": "Triagem positiva",
    "sem_sinais": "Abaixo do corte",
}

# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------


def _local(instante: datetime) -> datetime:
    return instante + FUSO_BRASILIA


def _data(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, datetime):
        valor = _local(valor)
    return valor.strftime("%d/%m/%Y")


def _dia_mes(valor: datetime) -> str:
    return _local(valor).strftime("%d/%m")


def _data_hora(valor: datetime) -> str:
    return _local(valor).strftime("%d/%m/%Y %H:%M")


def _numero(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _texto(valor: Any, limite: Optional[int] = None) -> str:
    """Texto do usuário pronto para o PDF: sem marcação e só com o que a fonte desenha."""
    texto = " ".join(str(valor or "").split())
    if limite and len(texto) > limite:
        texto = texto[: limite - 3].rstrip() + "..."
    texto = texto.encode("cp1252", "ignore").decode("cp1252")
    return escape(texto)


def _vezes(datas: List[datetime]) -> str:
    dias = [_dia_mes(d) for d in datas]
    if len(dias) == 1:
        return f"1 vez, em {dias[0]}"
    mostradas = dias[:5]
    resto = len(dias) - len(mostradas)
    lista = ", ".join(mostradas[:-1]) + " e " + mostradas[-1] if resto == 0 else ", ".join(mostradas)
    sufixo = f" e mais {resto}" if resto else ""
    return f"{len(dias)} vezes: {lista}{sufixo}"


def _pressao(valor: Optional[str]) -> Optional[Tuple[int, int]]:
    achado = re.search(r"(\d{2,3})\s*[x/X]\s*(\d{2,3})", valor or "")
    return (int(achado.group(1)), int(achado.group(2))) if achado else None


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------


def periodo_do_relatorio(db: Session, gestante_id: str, agora: datetime) -> Tuple[datetime, str]:
    """Desde a última consulta da agenda (no mínimo 7 dias); sem consulta recente, os últimos 30 dias."""
    ultima = (
        db.query(EventoAgenda)
        .filter(EventoAgenda.gestante_id == gestante_id, EventoAgenda.tipo == "consulta",
                EventoAgenda.data_hora < agora)
        .order_by(EventoAgenda.data_hora.desc())
        .first()
    )
    if ultima and agora - ultima.data_hora <= timedelta(days=DIAS_MAXIMOS_DESDE_A_CONSULTA):
        inicio = min(ultima.data_hora, agora - timedelta(days=DIAS_MINIMOS_DO_PERIODO))
        return inicio, f"desde a última consulta registrada na agenda, em {_data(ultima.data_hora)}"
    return (agora - timedelta(days=DIAS_SEM_CONSULTA_NA_AGENDA),
            "últimos 30 dias, porque não há consulta recente na agenda")


def montar_relatorio(db: Session, gestante_id: str, profissional: Profissional,
                     agora: Optional[datetime] = None) -> Dict[str, Any]:
    agora = agora or datetime.utcnow()
    gestante = db.query(Gestante).filter(Gestante.id == gestante_id).first()
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante_id).first()
    inicio, origem_periodo = periodo_do_relatorio(db, gestante_id, agora)

    def no_periodo(modelo, coluna):
        return (db.query(modelo)
                .filter(modelo.gestante_id == gestante_id, coluna >= inicio, coluna <= agora)
                .order_by(coluna.desc()).all())

    checkins = no_periodo(CheckinRegistro, CheckinRegistro.data_hora)
    triagens = no_periodo(TriagemEPDS, TriagemEPDS.data_hora)
    emergencias = no_periodo(EventoEmergencia, EventoEmergencia.data_hora)
    medidas = (db.query(RegistroAntropometrico)
               .filter(RegistroAntropometrico.gestante_id == gestante_id,
                       RegistroAntropometrico.data_registro >= _local(inicio).date())
               .order_by(RegistroAntropometrico.data_registro.desc()).all())
    exames = (db.query(Exame)
              .filter(Exame.gestante_id == gestante_id, Exame.criado_em >= inicio)
              .order_by(Exame.data_realizacao.desc()).all())
    alertas_no_chat = (db.query(Mensagem)
                       .filter(Mensagem.gestante_id == gestante_id, Mensagem.alerta_emergencia == True,  # noqa: E712
                               Mensagem.data_hora >= inicio).count())
    conversas = (db.query(Mensagem)
                 .filter(Mensagem.gestante_id == gestante_id, Mensagem.autorizado_compartilhar == True,  # noqa: E712
                         Mensagem.data_hora >= inicio)
                 .order_by(Mensagem.data_hora.desc()).limit(LIMITE_CONVERSAS).all())
    agenda = (db.query(EventoAgenda)
              .filter(EventoAgenda.gestante_id == gestante_id,
                      EventoAgenda.data_hora >= inicio,
                      EventoAgenda.data_hora <= agora + timedelta(days=30))
              .order_by(EventoAgenda.data_hora.asc()).all())
    proxima_consulta = (db.query(EventoAgenda)
                        .filter(EventoAgenda.gestante_id == gestante_id, EventoAgenda.tipo == "consulta",
                                EventoAgenda.data_hora >= agora)
                        .order_by(EventoAgenda.data_hora.asc()).first())
    ultimo_checkin = (db.query(CheckinRegistro)
                      .filter(CheckinRegistro.gestante_id == gestante_id)
                      .order_by(CheckinRegistro.data_hora.desc()).first())
    anotacoes = (db.query(ObservacaoProfissional)
                 .filter(ObservacaoProfissional.gestante_id == gestante_id,
                         ObservacaoProfissional.profissional_id == profissional.id)
                 .order_by(ObservacaoProfissional.criado_em.desc()).limit(LIMITE_ANOTACOES).all())

    rastreio = None
    recusa_ia = bool(gestante.recusa_ia) if gestante else False
    if perfil and not recusa_ia:
        historico = db.query(HistoricoFamiliar).filter(HistoricoFamiliar.gestante_id == gestante_id).all()
        rastreio = calculate_maternal_risks(
            perfil_para_modelos(perfil), [{"parente": h.parente, "condicao": h.condicao} for h in historico]
        )

    dados = {
        "agora": agora,
        "inicio": inicio,
        "origem_periodo": origem_periodo,
        "gestante": gestante,
        "perfil": perfil,
        "profissional": profissional,
        "recusa_ia": recusa_ia,
        "checkins": checkins,
        "triagens": triagens,
        "emergencias": emergencias,
        "medidas": medidas,
        "exames": exames,
        "alertas_no_chat": alertas_no_chat,
        "conversas": conversas,
        "agenda": agenda,
        "proxima_consulta": proxima_consulta,
        "ultimo_checkin": ultimo_checkin,
        "anotacoes": anotacoes,
        "rastreio": rastreio,
    }
    dados["pontos"] = pontos_de_atencao(dados)
    return dados


def pontos_de_atencao(dados: Dict[str, Any]) -> List[str]:
    """Fatos do período que merecem ser vistos na consulta, do mais urgente ao mais simples."""
    pontos: List[str] = []
    agora = dados["agora"]
    checkins = sorted(dados["checkins"], key=lambda c: c.data_hora)

    urgentes: "OrderedDict[str, List[datetime]]" = OrderedDict()
    atencao: "OrderedDict[str, List[datetime]]" = OrderedDict()
    for c in checkins:
        for sinal in c.alerta_sintoma_fisico or []:
            urgentes.setdefault(str(sinal), []).append(c.data_hora)
        for sinal in c.sinais_atencao or []:
            atencao.setdefault(str(sinal), []).append(c.data_hora)

    for sinal, datas in urgentes.items():
        pontos.append(f"Sinal de urgência relatado no check-in: {_texto(sinal, 120)} ({_vezes(datas)}).")

    for e in sorted(dados["emergencias"], key=lambda e: e.data_hora):
        avisada = "sim" if e.profissional_notificado else "não"
        pontos.append(f"Botão de emergência acionado em {_data_hora(e.data_hora)}; equipe avisada por e-mail: {avisada}.")

    for t in sorted(dados["triagens"], key=lambda t: t.data_hora):
        if t.nivel == "urgente":
            pontos.append(f"Escala de Edimburgo em {_dia_mes(t.data_hora)}: {t.pontuacao} pontos e resposta positiva "
                          f"na pergunta 10 (pensamento de se machucar).")
        elif t.nivel == "atencao":
            pontos.append(f"Escala de Edimburgo em {_dia_mes(t.data_hora)}: {t.pontuacao} pontos "
                          f"(corte de triagem: {CORTE_EPDS}).")

    if dados["alertas_no_chat"]:
        n = dados["alertas_no_chat"]
        pontos.append(f"{n} {'mensagem' if n == 1 else 'mensagens'} da gestante no chat "
                      f"{'acionou' if n == 1 else 'acionaram'} o alerta de urgência. O conteúdo só aparece aqui "
                      f"se ela autorizar o compartilhamento.")

    pressoes = [(p, m.data_registro) for m in dados["medidas"] if (p := _pressao(m.pressao_arterial))]
    if pressoes:
        (sist, diast), dia = max(pressoes, key=lambda x: x[0])
        pontos.append(f"Maior pressão arterial registrada no período: {sist}/{diast} mmHg, em {_data(dia)}.")

    for sinal, datas in atencao.items():
        pontos.append(f"Sinal de atenção relatado no check-in: {_texto(sinal, 120)} ({_vezes(datas)}).")

    humor_baixo = [c for c in checkins if c.humor is not None and c.humor <= 2]
    if humor_baixo:
        pontos.append(f"Humor 1 ou 2 (escala de 1 a 5) em {len(humor_baixo)} dos {len(checkins)} check-ins do período.")

    for evento in dados["agenda"]:
        if evento.tipo in ("exame", "vacina") and evento.data_hora < agora and not evento.concluido:
            pontos.append(f"{'Exame' if evento.tipo == 'exame' else 'Vacina'} da agenda com data passada e não "
                          f"marcado como feito: {_texto(evento.titulo, 80)} ({_data(evento.data_hora)}).")

    medidas = sorted(dados["medidas"], key=lambda m: m.data_registro)
    if len(medidas) >= 2:
        primeiro, ultimo = medidas[0], medidas[-1]
        diferenca = ultimo.peso_atual_kg - primeiro.peso_atual_kg
        sinal = "+" if diferenca >= 0 else ""
        pontos.append(f"Peso registrado: de {_numero(primeiro.peso_atual_kg)} kg ({_data(primeiro.data_registro)}) "
                      f"para {_numero(ultimo.peso_atual_kg)} kg ({_data(ultimo.data_registro)}), "
                      f"diferença de {sinal}{_numero(diferenca)} kg.")

    if not checkins:
        pontos.append("Nenhum check-in no período.")
    elif dados["ultimo_checkin"] and (agora - dados["ultimo_checkin"].data_hora).days >= DIAS_SEM_CHECKIN_PARA_AVISAR:
        dias = (agora - dados["ultimo_checkin"].data_hora).days
        pontos.append(f"Último check-in há {dias} dias.")

    return pontos


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

VINHO = colors.HexColor("#5C1A2A")
ROSA_CLARO = colors.HexColor("#FDF0F2")
CINZA = colors.HexColor("#5F6B76")
TEXTO = colors.HexColor("#22313F")
LINHA = colors.HexColor("#E3D3D8")

ESTILOS = {
    "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=VINHO),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CINZA),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=VINHO,
                         spaceBefore=10, spaceAfter=4),
    "normal": ParagraphStyle("normal", fontName="Helvetica", fontSize=9, leading=12.5, textColor=TEXTO),
    "ponto": ParagraphStyle("ponto", fontName="Helvetica", fontSize=9, leading=12.5, textColor=TEXTO,
                            leftIndent=10, bulletIndent=0, spaceAfter=2),
    "pequeno": ParagraphStyle("pequeno", fontName="Helvetica", fontSize=7.5, leading=10, textColor=CINZA),
    "celula": ParagraphStyle("celula", fontName="Helvetica", fontSize=8, leading=10, textColor=TEXTO),
    "celula_cab": ParagraphStyle("celula_cab", fontName="Helvetica-Bold", fontSize=8, leading=10,
                                 textColor=colors.white),
}
LARGURA_UTIL = A4[0] - 36 * mm


def _p(texto: str, estilo: str = "normal") -> Paragraph:
    return Paragraph(texto, ESTILOS[estilo])


def _tabela(cabecalho: List[str], linhas: Iterable[List[str]], proporcoes: List[float]) -> Table:
    larguras = [LARGURA_UTIL * p / sum(proporcoes) for p in proporcoes]
    dados = [[_p(c, "celula_cab") for c in cabecalho]] + [[_p(str(c), "celula") for c in linha] for linha in linhas]
    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), VINHO),
        ("GRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(2, len(dados), 2):
        estilo.append(("BACKGROUND", (0, i), (-1, i), ROSA_CLARO))
    tabela.setStyle(TableStyle(estilo))
    return tabela


def _semana(perfil: Optional[PerfilClinico], agora: datetime) -> Optional[int]:
    if not perfil or not perfil.dum:
        return None
    return max(0, (_local(agora).date() - perfil.dum).days // 7)


def _identificacao(dados: Dict[str, Any]) -> List:
    gestante, perfil, prof = dados["gestante"], dados["perfil"], dados["profissional"]
    semana = _semana(perfil, dados["agora"])
    linhas = [["Gestante", _texto(gestante.nome if gestante else "")]]
    if perfil:
        linhas += [
            ["Idade", f"{perfil.idade} anos"],
            ["Semana gestacional", f"{semana} semanas (pela DUM de {_data(perfil.dum)})" if semana is not None else ""],
            ["Data provável do parto", _data(perfil.dpp)],
            ["Gestações anteriores", f"{perfil.gestacoes_anteriores or 0}; partos normais: {perfil.partos_normais or 0}; "
                                     f"cesáreas: {perfil.partos_cesareos or 0}; perdas: {perfil.perdas_gestacionais or 0}"],
        ]
        if perfil.numero_fetos:
            linhas.append(["Fetos", {1: "1 (único)", 2: "2 (gêmeos)"}.get(perfil.numero_fetos, f"{perfil.numero_fetos}")])
        if perfil.maternidade_nome:
            telefone = f" ({_texto(perfil.maternidade_telefone)})" if perfil.maternidade_telefone else ""
            linhas.append(["Maternidade de referência", _texto(perfil.maternidade_nome) + telefone])
    else:
        linhas.append(["Cadastro clínico", "Ainda não preenchido pela gestante."])
    linhas.append(["Uso de IA", "Recusado pela gestante" if dados["recusa_ia"] else "Aceito pela gestante"])
    registro = f"{prof.registro_tipo or 'CRM'} {prof.registro_numero}/{prof.registro_uf}" if prof.registro_numero else ""
    linhas.append(["Profissional", f"{_texto(prof.nome)}{', ' + registro if registro else ''}"])
    return [_tabela(["Identificação", ""], linhas, [1.1, 3.2])]


def _secao_pontos(dados: Dict[str, Any]) -> List:
    itens = [_p("Pontos de atenção do período", "h2")]
    if dados["pontos"]:
        itens += [Paragraph(p, ESTILOS["ponto"], bulletText="•") for p in dados["pontos"]]
    else:
        itens.append(_p("Nada fora do comum foi registrado no período."))
    itens.append(Spacer(1, 3))
    itens.append(_p("Lista gerada automaticamente a partir dos registros do app. Ela aponta fatos; a avaliação "
                    "clínica e a conduta são do profissional.", "pequeno"))
    return itens


def _secao_checkins(dados: Dict[str, Any]) -> List:
    checkins = dados["checkins"]
    itens = [_p("Check-ins diários", "h2")]
    if not checkins:
        return itens + [_p("Nenhum check-in no período.")]
    linhas = []
    for c in checkins[:LIMITE_CHECKINS]:
        sinais = list(c.alerta_sintoma_fisico or []) + list(c.sinais_atencao or [])
        linhas.append([
            _data_hora(c.data_hora),
            f"{c.humor}/5" if c.humor is not None else "",
            _texto(", ".join(str(s) for s in (c.sintomas or [])) or "Nenhum", 90),
            str(c.movimentos_bebe if c.movimentos_bebe is not None else ""),
            _texto(", ".join(str(s) for s in sinais) or "Nenhum", 90),
        ])
    itens.append(_tabela(["Data e hora", "Humor", "Sintomas marcados", "Movimentos do bebê", "Sinais pelas regras"],
                         linhas, [1.25, 0.6, 2.0, 0.9, 2.0]))
    if len(checkins) > LIMITE_CHECKINS:
        itens.append(_p(f"Mostrando os {LIMITE_CHECKINS} mais recentes de {len(checkins)} check-ins.", "pequeno"))
    relatos = [c for c in checkins if (c.descricao or "").strip()][:LIMITE_RELATOS]
    if relatos:
        itens.append(Spacer(1, 4))
        itens.append(_p("<b>Relatos escritos no check-in</b>"))
        for c in relatos:
            itens.append(Paragraph(f"{_dia_mes(c.data_hora)}: {_texto(c.descricao, 300)}", ESTILOS["ponto"],
                                   bulletText="•"))
    return itens


def _secao_epds(dados: Dict[str, Any]) -> List:
    itens = [_p("Triagem emocional (Escala de Edimburgo)", "h2")]
    if not dados["triagens"]:
        return itens + [_p("Nenhuma triagem respondida no período.")]
    linhas = [[
        _data_hora(t.data_hora),
        str(t.semana_gestacional or ""),
        str(t.pontuacao),
        ROTULO_EPDS.get(t.nivel, t.nivel),
        "Sim" if t.profissional_notificado else "Não",
    ] for t in dados["triagens"]]
    itens.append(_tabela(["Data e hora", "Semana", "Pontos (0 a 30)", "Resultado", "Equipe avisada"],
                         linhas, [1.3, 0.7, 1.0, 1.6, 1.0]))
    itens.append(_p(f"Corte de triagem: {CORTE_EPDS} pontos (Santos et al., 2007). A escala aponta quem deve ser "
                    f"avaliado; não é diagnóstico.", "pequeno"))
    return itens


def _secao_medidas(dados: Dict[str, Any]) -> List:
    itens = [_p("Medidas registradas pela gestante", "h2")]
    if not dados["medidas"]:
        return itens + [_p("Nenhuma medida registrada no período.")]
    linhas = [[
        _data(m.data_registro),
        str(m.semana_gestacional or ""),
        f"{_numero(m.peso_atual_kg)} kg" if m.peso_atual_kg is not None else "",
        f"{_numero(m.altura_uterina_cm)} cm" if m.altura_uterina_cm is not None else "",
        f"{_numero(m.circunferencia_abdominal_cm)} cm" if m.circunferencia_abdominal_cm is not None else "",
        _texto(m.pressao_arterial or ""),
        _texto(m.edema or ""),
    ] for m in dados["medidas"]]
    itens.append(_tabela(["Data", "Semana", "Peso", "Altura uterina", "Circ. abdominal", "Pressão", "Edema"],
                         linhas, [1.0, 0.6, 0.8, 0.9, 0.9, 0.8, 0.8]))
    return itens


def _secao_exames_e_agenda(dados: Dict[str, Any]) -> List:
    itens = [_p("Exames enviados e agenda", "h2")]
    if dados["exames"]:
        itens.append(_tabela(["Data do exame", "Tipo", "Observações"],
                             [[_data(e.data_realizacao), _texto(e.tipo, 60), _texto(e.observacoes or "", 160)]
                              for e in dados["exames"]],
                             [1.0, 1.6, 3.4]))
    else:
        itens.append(_p("Nenhum exame enviado no período."))
    itens.append(Spacer(1, 4))
    prox = dados["proxima_consulta"]
    itens.append(_p(f"Próxima consulta na agenda: {_data_hora(prox.data_hora)} ({_texto(prox.titulo, 80)})."
                    if prox else "Nenhuma consulta futura registrada na agenda."))
    futuros = [e for e in dados["agenda"] if e.data_hora >= dados["agora"] and e.tipo in ("exame", "vacina", "consulta")]
    if futuros:
        itens.append(_tabela(["Data", "Tipo", "Item da agenda"],
                             [[_data_hora(e.data_hora), e.tipo.capitalize(), _texto(e.titulo, 90)] for e in futuros],
                             [1.3, 0.9, 3.8]))
    return itens


def _secao_rastreio(dados: Dict[str, Any]) -> List:
    itens = [_p("Rastreio estatístico com IA", "h2")]
    if dados["recusa_ia"]:
        return itens + [_p("A gestante recusou o uso de IA (Resolução CFM nº 2.454/2026, art. 5º, § 3º). "
                           "Este relatório não traz estimativas dos modelos.")]
    rastreio = dados["rastreio"]
    if not rastreio:
        return itens + [_p("Sem cadastro clínico, não há estimativas.")]
    linhas = []
    for c in rastreio.get("condicoes", {}).values():
        nivel = ROTULO_NIVEL.get(c.get("nivel"), "Sem estimativa")
        relativo = c.get("risco_relativo")
        media = f"{_numero(relativo)} {'vez' if relativo < 2 else 'vezes'} a média" if relativo else ""
        notas = []
        if c.get("probabilidade") is not None and c.get("media_populacional") is not None:
            notas.append(f"chance estimada de {_numero(c['probabilidade'] * 100)}% (média: "
                         f"{_numero(c['media_populacional'] * 100)}%)")
        if c.get("simulado"):
            notas.append("simulação com estudos publicados")
        if c.get("motivo_nivel") == "diretriz":
            notas.append("nível elevado pelo critério das diretrizes")
        if c.get("motivo") and not c.get("nivel"):
            notas.append(_texto(c["motivo"], 260))
        linhas.append([_texto(c.get("nome", "")), nivel, media, "; ".join(notas)])
    itens.append(_tabela(["Condição", "Nível", "Em relação à média", "Observação"], linhas, [1.6, 0.8, 1.0, 2.6]))
    fatores = rastreio.get("fatores_clinicos") or []
    if fatores:
        itens.append(Spacer(1, 4))
        itens.append(_p("<b>Fatores clínicos informados pela gestante</b>"))
        for f in fatores:
            itens.append(Paragraph(_texto(f.get("fator", ""), 140), ESTILOS["ponto"], bulletText="•"))
    prevencao = rastreio.get("prevencao_pre_eclampsia")
    if prevencao:
        itens.append(_p(f"Critério das diretrizes para conversar sobre prevenção da pré-eclâmpsia: atingido "
                        f"({prevencao['altos']} fator alto, {prevencao['moderados']} moderados)."))
    itens.append(Spacer(1, 3))
    itens.append(_p(_texto(CARIMBO_PRONTUARIO), "pequeno"))
    return itens


def _secao_conversas(dados: Dict[str, Any]) -> List:
    itens = [_p("Conversas que a gestante autorizou compartilhar", "h2")]
    if not dados["conversas"]:
        return itens + [_p("Nenhuma conversa compartilhada no período.")]
    # Em ordem de conversa: a pergunta antes da resposta
    for m in sorted(dados["conversas"], key=lambda m: m.data_hora):
        autor = "Gestante" if m.papel == "gestante" else "Assistente (IA)"
        itens.append(Paragraph(f"<b>{autor}, {_data_hora(m.data_hora)}:</b> {_texto(m.conteudo, 500)}",
                               ESTILOS["ponto"], bulletText="•"))
    return itens


def _secao_anotacoes(dados: Dict[str, Any]) -> List:
    itens = [_p("Suas anotações", "h2")]
    if not dados["anotacoes"]:
        return itens + [_p("Nenhuma anotação registrada.")]
    for a in dados["anotacoes"]:
        itens.append(Paragraph(f"<b>{_data_hora(a.criado_em)}:</b> {_texto(a.observacao, 600)}",
                               ESTILOS["ponto"], bulletText="•"))
    return itens


def _rodape(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CINZA)
    canvas.drawString(18 * mm, 10 * mm, "Nymphia, relatório para a consulta. Documento com dados de saúde: "
                                        "guarde com sigilo (LGPD).")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Página {doc.page}")
    canvas.restoreState()


def gerar_pdf(dados: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
        title="Relatório para a consulta", author="Nymphia",
    )
    elementos = [
        _p("Relatório para a consulta", "titulo"),
        _p(f"Gerado automaticamente pela Nymphia em {_data_hora(dados['agora'])} (horário de Brasília). "
           f"Período: de {_data(dados['inicio'])} a {_data(dados['agora'])}, {dados['origem_periodo']}.", "sub"),
        _p("Reúne o que a gestante registrou no app no período e as suas anotações. Não é laudo nem diagnóstico.",
           "sub"),
        Spacer(1, 6),
        *_identificacao(dados),
        *_secao_pontos(dados),
        *_secao_checkins(dados),
        KeepTogether(_secao_epds(dados)),
        KeepTogether(_secao_medidas(dados)),
        *_secao_exames_e_agenda(dados),
        *_secao_rastreio(dados),
        *_secao_conversas(dados),
        *_secao_anotacoes(dados),
    ]
    doc.build(elementos, onFirstPage=_rodape, onLaterPages=_rodape)
    return buffer.getvalue()


def gerar_relatorio_consulta(db: Session, gestante_id: str, profissional: Profissional,
                             agora: Optional[datetime] = None) -> bytes:
    return gerar_pdf(montar_relatorio(db, gestante_id, profissional, agora))
