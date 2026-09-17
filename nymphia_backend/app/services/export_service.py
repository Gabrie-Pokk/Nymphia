import io
from typing import Dict, Any
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.auth import Gestante
from app.models.clinical import PerfilClinico, HistoricoFamiliar, CheckinRegistro, Exame
from app.models.interaction import EventoAgenda, Mensagem, EventoEmergencia
from app.models.relations import LogAcesso, Vinculo

def export_gestante_json(gestante_id: str, db: Session) -> Dict[str, Any]:
    gestante = db.query(Gestante).filter(Gestante.id == gestante_id).first()
    if not gestante:
        return {}

    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante_id).first()
    historico = db.query(HistoricoFamiliar).filter(HistoricoFamiliar.gestante_id == gestante_id).all()
    checkins = db.query(CheckinRegistro).filter(CheckinRegistro.gestante_id == gestante_id).order_by(CheckinRegistro.data_hora.desc()).all()
    agenda = db.query(EventoAgenda).filter(EventoAgenda.gestante_id == gestante_id).all()
    exames = db.query(Exame).filter(Exame.gestante_id == gestante_id).all()
    emergencias = db.query(EventoEmergencia).filter(EventoEmergencia.gestante_id == gestante_id).all()

    return {
        "titular": {
            "id": gestante.id,
            "nome": gestante.nome,
            "email": gestante.email,
            "recusa_ia": gestante.recusa_ia,
            "criado_em": gestante.criado_em.isoformat()
        },
        "perfil_clinico": {
            "idade": perfil.idade if perfil else None,
            "dum": perfil.dum.isoformat() if perfil and perfil.dum else None,
            "dpp": perfil.dpp.isoformat() if perfil and perfil.dpp else None,
            "dpp_editada_manualmente": perfil.dpp_editada_manualmente if perfil else False,
            "gestacoes_anteriores": perfil.gestacoes_anteriores if perfil else 0,
            "partos_normais": perfil.partos_normais if perfil else 0,
            "partos_cesareos": perfil.partos_cesareos if perfil else 0,
            "perdas_gestacionais": perfil.perdas_gestacionais if perfil else 0,
            "maternidade_referencia": perfil.maternidade_nome if perfil else None,
            "maternidade_telefone": perfil.maternidade_telefone if perfil else None
        } if perfil else None,
        "historico_familiar": [
            {"parente": h.parente, "condicao": h.condicao} for h in historico
        ],
        "checkins": [
            {
                "id": c.id,
                "data_hora": c.data_hora.isoformat(),
                "humor": c.humor,
                "descricao": c.descricao,
                "sintomas": c.sintomas,
                "movimentos_bebe": c.movimentos_bebe,
                "alertas": c.alerta_sintoma_fisico
            } for c in checkins
        ],
        "agenda": [
            {
                "id": a.id,
                "tipo": a.tipo,
                "titulo": a.titulo,
                "data_hora": a.data_hora.isoformat(),
                "concluido": a.concluido
            } for a in agenda
        ],
        "exames": [
            {
                "id": e.id,
                "tipo": e.tipo,
                "data_realizacao": e.data_realizacao.isoformat(),
                "valores_extraidos": e.valores_extraidos
            } for e in exames
        ],
        "eventos_emergencia": [
            {
                "id": em.id,
                "data_hora": em.data_hora.isoformat(),
                "profissional_notificado": em.profissional_notificado
            } for em in emergencias
        ]
    }

def export_gestante_pdf(gestante_id: str, db: Session) -> bytes:
    data = export_gestante_json(gestante_id, db)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#5C1A2A'),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#C2185B'),
        alignment=1
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#5C1A2A'),
        spaceBefore=12,
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'DocNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2C3E50')
    )

    elements = []
    elements.append(Paragraph("Nymphia — Caderneta Digital de Pré-Natal", title_style))
    elements.append(Paragraph("Portabilidade de Dados Pessoais de Saúde (Art. 18, LGPD)", subtitle_style))
    elements.append(Spacer(1, 15))

    titular = data.get("titular", {})
    perfil = data.get("perfil_clinico", {}) or {}

    elements.append(Paragraph("Identificação da Gestante", h2_style))
    ident_data = [
        ["Nome:", titular.get("nome", ""), "E-mail:", titular.get("email", "")],
        ["Idade:", str(perfil.get("idade", "Não informada")), "Data de Início:", titular.get("criado_em", "")[:10]],
        ["DUM:", str(perfil.get("dum", "N/A")), "DPP:", str(perfil.get("dpp", "N/A"))],
        ["Maternidade Ref.:", str(perfil.get("maternidade_referencia", "N/A")), "Tel. Maternidade:", str(perfil.get("maternidade_telefone", "N/A"))]
    ]
    t_ident = Table(ident_data, colWidths=[90, 180, 90, 180])
    t_ident.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#2C3E50')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FDF0F2')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_ident)
    elements.append(Spacer(1, 12))

    # Histórico de Check-ins (últimos 10)
    elements.append(Paragraph("Registros Recentes de Check-in", h2_style))
    checkins = data.get("checkins", [])[:10]
    if checkins:
        ck_data = [["Data/Hora (Servidor)", "Humor", "Sintomas", "Chutes", "Alertas"]]
        for c in checkins:
            sintomas_str = ", ".join(c.get("sintomas", [])) or "Sem sintomas"
            alertas_str = ", ".join(c.get("alertas", [])) or "Nenhum"
            ck_data.append([
                c.get("data_hora", "")[:16].replace("T", " "),
                f"Nível {c.get('humor', '')}",
                sintomas_str[:30],
                str(c.get("movimentos_bebe", 0)),
                alertas_str[:30]
            ])
        t_ck = Table(ck_data, colWidths=[100, 50, 150, 50, 180])
        t_ck.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5C1A2A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0D0D5')),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t_ck)
    else:
        elements.append(Paragraph("Nenhum registro de check-in efetuado.", normal_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
