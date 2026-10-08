import os
import sys
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Header (Páginas > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#5C1A2A"))
            self.drawString(40, 810, "NYMPHIA")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#666666"))
            self.drawString(88, 810, "• Documentação Técnica e de Arquitetura da Plataforma (v2.3.0)")
            
            self.setStrokeColor(colors.HexColor("#E5D4D8"))
            self.setLineWidth(0.6)
            self.line(40, 802, 555, 802)

        # Footer (Todas as páginas)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))
        self.drawString(40, 24, "Nymphia Health Tech • Cada batimento importa • Conforme CFM 2.454/2026 e CDC")
        
        pag_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(555, 24, pag_str)
        
        self.setStrokeColor(colors.HexColor("#E5D4D8"))
        self.setLineWidth(0.6)
        self.line(40, 34, 555, 34)
        
        self.restoreState()


def format_inline_markdown(text: str) -> str:
    """Substitui marcações de markdown por tags XML seguras para o ReportLab."""
    if not text:
        return ""
    
    t = text.replace("&", "&amp;")
    t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)
    t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\w)\*(.*?)\*(?!\w)', r'<i>\1</i>', t)
    
    def _rep_code(m):
        code_str = m.group(1).replace("<", "&lt;").replace(">", "&gt;")
        return f'<font color="#5C1A2A"><b>{code_str}</b></font>'
    t = re.sub(r'`([^`]+)`', _rep_code, t)
    
    t = t.replace(r'$\ge$', '&ge;').replace(r'\ge', '&ge;').replace('>=', '&ge;')
    t = t.replace(r'$\le$', '&le;').replace(r'\le', '&le;').replace('<=', '&le;')
    
    return t


def build_pdf():
    base_dir = Path(__file__).resolve().parent.parent
    md_path = base_dir / "DOCUMENTACAO_SISTEMA_NYMPHIA.md"
    pdf_path = base_dir / "DOCUMENTACAO_SISTEMA_NYMPHIA.pdf"

    if not md_path.exists():
        print(f"Erro: arquivo {md_path} não encontrado.")
        return

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Cores Nymphia
    c_vinho = colors.HexColor("#5C1A2A")
    c_rosa = colors.HexColor("#C2185B")
    c_texto = colors.HexColor("#2C2C2C")
    c_cinza_bg = colors.HexColor("#F9F4F5")
    c_borda = colors.HexColor("#E5D4D8")
    c_codigo = colors.HexColor("#333333")

    s_titulo = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_vinho,
        spaceAfter=4
    )

    s_subtitulo = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=c_rosa,
        spaceAfter=12
    )

    s_meta_box = ParagraphStyle(
        'MetaBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=12,
        textColor=c_texto
    )

    s_h1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_vinho,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    s_h2 = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=c_rosa,
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=True
    )

    s_h3 = ParagraphStyle(
        'SectionH3',
        parent=styles['Heading4'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=c_vinho,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    s_p = ParagraphStyle(
        'BodyP',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_texto,
        spaceAfter=4
    )

    s_bullet = ParagraphStyle(
        'BulletP',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=c_texto,
        leftIndent=10,
        spaceAfter=2.5
    )

    s_callout = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=c_vinho
    )

    s_code = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9.5,
        textColor=c_codigo
    )

    s_th = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    s_td = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=c_texto
    )

    s_td_code = ParagraphStyle(
        'TDCode',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7,
        leading=9.5,
        textColor=c_vinho
    )

    s_flow_step = ParagraphStyle(
        'FlowStep',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=c_vinho
    )

    s_flow_desc = ParagraphStyle(
        'FlowDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=c_texto
    )

    story = []

    # Cabeçalho da Capa
    story.append(Paragraph("Documentação Técnica e de Arquitetura", s_titulo))
    story.append(Paragraph("Plataforma Nymphia — Saúde Materno-Fetal & Inteligência Artificial Obstétrica", s_subtitulo))
    
    meta_html = (
        "<b>Versão da Plataforma:</b> 2.3.0 (Produção Cloud Ready & 2027 Ready)<br/>"
        "<b>Slogan Oficial:</b> <i>\"Cada batimento importa.\"</i><br/>"
        "<b>Diretrizes Clínicas:</b> Ministério da Saúde do Brasil, FEBRASGO, ACOG, CDC e Resolução CFM 2.454/2026<br/>"
        "<b>Ambiente de Produção (Render):</b> https://nymphia-plataforma-ia.onrender.com<br/>"
        "<b>Repositório Oficial:</b> https://github.com/Gabrie-Pokk/Nymphia.git"
    )
    
    t_meta = Table([[Paragraph(meta_html, s_meta_box)]], colWidths=[515])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_cinza_bg),
        ('BOX', (0,0), (-1,-1), 1, c_borda),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    lines = md_text.split('\n')
    
    i = 0
    in_code_block = False
    code_lang = ""
    code_lines = []
    
    last_heading = ""

    while i < len(lines) and not lines[i].startswith('## 1.'):
        i += 1

    while i < len(lines):
        line = lines[i].rstrip()
        
        # Bloco de Código / Mermaid / JSON
        if line.startswith('```'):
            if in_code_block:
                in_code_block = False
                
                # Se for diagrama Mermaid, converte para visualização esquemática elegante de etapas
                if code_lang == "mermaid":
                    # Gera tabela esquemática representativa das etapas do fluxo
                    mermaid_raw = "\n".join(code_lines)
                    flow_title = last_heading or "Fluxograma de Funcionamento"
                    
                    # Cria tabela estruturada do fluxo para o PDF
                    flow_steps = []
                    if "Jornada do Cuidado" in flow_title or "Fluxo Geral" in flow_title:
                        flow_steps = [
                            ("1. Acesso & Autenticação", "POST /auth/login (Login Unificado) detecta perfil automaticamente (Gestante, Parceiro, Obstetra). Rota /emergencia offline-first disponível sem sessão."),
                            ("2. Rotina da Gestante", "DailyCheckin (humor e sintomas), Antropometria (Curva de Atalah e Altura Uterina), BodyVision (Pose MediaPipe 33 landmarks) e AiChat (Gemini)."),
                            ("3. Co-participação do Parceiro", "POST /parceiro/checkin (registro em nome da gestante com tag de autoria), gestão da agenda de pré-natal e polling a cada 8s de alertas SAMU 192."),
                            ("4. Pipeline de IA & Guardrails", "Motor determinístico FEBRASGO avalia sinais de alarme. Se estável: classifica emoções via BERTimbau INT8 e calcula risco nos 6 modelos Random Forest."),
                            ("5. Prontuário & Governança", "DoctorDashboard com triagem por gravidade 30d, prontuário evolutivo com nota CFM 2.454/2026 e trilha de auditoria LGPD.")
                        ]
                    elif "Pipeline de Decisão" in flow_title:
                        flow_steps = [
                            ("Passo 1: Triagem de Urgência", "Verificação determinística de sintomas de alarme (sangramento, cefaleia intensa, perda líquida, PA >= 140x90). Se grave: protocolo SAMU 192 imediato."),
                            ("Passo 2: Consentimento de IA", "Validação do direito de recusa (Res. CFM 2.454/2026). Caso recuse, opera exclusivamente sob regras clínicas determinísticas do Ministério da Saúde."),
                            ("Passo 3: BERTimbau INT8", "Classificação neural em 6 categorias com modelo quantizado (~180MB RAM). Fallback léxico garantido caso memória seja restrita (<512MB)."),
                            ("Passo 4: Random Forest x6 & Isolation Forest", "Inferência simultânea de risco populacional (Pré-eclâmpsia, DMG, Eclâmpsia, ITU, Malformação, Bem-estar fetal) calibrados com DataSUS."),
                            ("Passo 5: Resposta Humanizada", "Google Gemini 2.5/1.5 Flash gera acolhimento sob temperatura 0.4 e guardrails rígidos; dados integrados ao prontuário médico.")
                        ]
                    elif "Biomecânica" in flow_title or "MediaPipe" in flow_title:
                        flow_steps = [
                            ("Entrada & Privacidade Edge AI", "Feed de vídeo capturado pela câmera do dispositivo e processado 100% no navegador via WebAssembly / GPU. Nenhum frame trafega para a nuvem."),
                            ("Rastreamento Anatômico 3D", "Identificação contínua de 33 marcos corporais a 30+ FPS (Google MediaPipe Pose)."),
                            ("Guardrails Clínicos Invioláveis", "Veto automático a posições em decúbito dorsal após 16 semanas (compressão de veia cava) e veto a afundos assimétricos se dor púbica/SPD."),
                            ("Métricas Posturais", "Avaliação em tempo real de lordose lombar, báscula pélvica e amplitude de agachamento seguro para gestantes."),
                            ("Feedback Sonoro Personalizado", "Web Speech Synthesis API gera instruções de voz imediatas em pt-BR (sem precisar olhar para a tela).")
                        ]
                    elif "Tríade" in flow_title or "Colaborativa" in flow_title:
                        flow_steps = [
                            ("Gestante (Centro do Cuidado)", "Mantém prontuário ativo, emite códigos temporários (PARC-XXXXX e token médico de 8 dígitos) e gerencia consentimentos."),
                            ("Parceiro (Rede de Apoio)", "Preenche check-in em nome da gestante, adiciona consultas na agenda, acompanha mimos no Quiz de Gostos e recebe alerta de emergência."),
                            ("Médico Obstetra (Supervisão)", "Visualiza painel priorizado por gravidade de alertas em 30 dias, avalia curvas evolutivas de peso e emite condutas com segurança jurídica.")
                        ]
                    else:
                        flow_steps = [
                            ("Fluxo Operacional Integrado", "Processamento assíncrono em camadas com regras determinísticas FEBRASGO e modelos preditivos de machine learning."),
                            ("Visualização Completa", "Consulte o arquivo DOCUMENTACAO_SISTEMA_NYMPHIA.html para o diagrama vetorial interativo renderizado via Mermaid.js.")
                        ]

                    t_flow_data = [
                        [Paragraph("<b>Etapa / Fase</b>", s_th), Paragraph("<b>Ações, Decisões e Regras de Negócio</b>", s_th)]
                    ]
                    for step_name, step_desc in flow_steps:
                        t_flow_data.append([
                            Paragraph(step_name, s_flow_step),
                            Paragraph(step_desc, s_flow_desc)
                        ])

                    t_flow = Table(t_flow_data, colWidths=[140, 375])
                    t_flow.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), c_rosa),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ('LEFTPADDING', (0,0), (-1,-1), 6),
                        ('RIGHTPADDING', (0,0), (-1,-1), 6),
                        ('GRID', (0,0), (-1,-1), 0.5, c_borda),
                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_cinza_bg]),
                    ]))
                    story.append(Spacer(1, 3))
                    story.append(t_flow)
                    story.append(Spacer(1, 5))

                else:
                    # Blocos de código normais (JSON, bash, etc.)
                    # Divide em pedaços de no máximo 20 linhas para evitar estouro de página
                    chunk_size = 20
                    for chunk_idx in range(0, len(code_lines), chunk_size):
                        sub_chunk = code_lines[chunk_idx:chunk_idx + chunk_size]
                        code_text = "<br/>".join([c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;") for c in sub_chunk])
                        t_code = Table([[Paragraph(code_text, s_code)]], colWidths=[515])
                        t_code.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
                            ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor("#D0D5DD")),
                            ('TOPPADDING', (0,0), (-1,-1), 4),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                            ('LEFTPADDING', (0,0), (-1,-1), 8),
                            ('RIGHTPADDING', (0,0), (-1,-1), 8),
                        ]))
                        story.append(t_code)
                        story.append(Spacer(1, 3))

                code_lines = []
            else:
                in_code_block = True
                code_lang = line[3:].strip()
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        if not line:
            i += 1
            continue

        # Separador Horizontal
        if line.strip() in ('---', '***', '___'):
            story.append(HRFlowable(width="100%", thickness=0.5, color=c_borda, spaceBefore=4, spaceAfter=6))
            i += 1
            continue

        # Título H1 (## )
        if line.startswith('## '):
            titulo_h1 = format_inline_markdown(line[3:].strip())
            last_heading = line[3:].strip()
            story.append(Paragraph(titulo_h1, s_h1))
            i += 1
            continue

        # Título H2 (### )
        if line.startswith('### '):
            titulo_h2 = format_inline_markdown(line[4:].strip())
            last_heading = line[4:].strip()
            story.append(Paragraph(titulo_h2, s_h2))
            i += 1
            continue

        # Título H3 (#### )
        if line.startswith('#### '):
            titulo_h3 = format_inline_markdown(line[5:].strip())
            last_heading = line[5:].strip()
            story.append(Paragraph(titulo_h3, s_h3))
            i += 1
            continue

        # Tabela Markdown (| Col 1 | Col 2 | ...)
        if line.startswith('|') and '|' in line[1:]:
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            
            rows = []
            for tl in table_lines:
                if re.match(r'^\|\s*[-:]+[-|\s:]*\|$', tl):
                    continue
                cols = [c.strip() for c in tl.strip('|').split('|')]
                rows.append(cols)

            if len(rows) > 0:
                num_cols = len(rows[0])
                if num_cols == 4:
                    if "Módulo" in rows[0][0] or "Prefixo" in rows[0][1]:
                        col_widths = [85, 130, 50, 250]
                    else:
                        col_widths = [105, 110, 90, 210]
                elif num_cols == 3:
                    col_widths = [135, 130, 250]
                elif num_cols == 2:
                    col_widths = [170, 345]
                else:
                    col_widths = [515 / num_cols] * num_cols

                formatted_table_data = []
                for r_idx, r in enumerate(rows):
                    row_cells = []
                    is_header = (r_idx == 0)
                    for c_idx, cell in enumerate(r):
                        c_formatted = format_inline_markdown(cell)
                        if is_header:
                            row_cells.append(Paragraph(f"<b>{c_formatted}</b>", s_th))
                        elif c_idx == 1 and ('/' in cell or 'GET' in cell or 'POST' in cell):
                            row_cells.append(Paragraph(c_formatted, s_td_code))
                        else:
                            row_cells.append(Paragraph(c_formatted, s_td))
                    formatted_table_data.append(row_cells)

                t_table = Table(formatted_table_data, colWidths=col_widths, repeatRows=1)
                t_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), c_vinho),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING', (0,0), (-1,-1), 3.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
                    ('LEFTPADDING', (0,0), (-1,-1), 4.5),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4.5),
                    ('GRID', (0,0), (-1,-1), 0.5, c_borda),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_cinza_bg]),
                ]))
                story.append(Spacer(1, 3))
                story.append(t_table)
                story.append(Spacer(1, 5))
            continue

        # Callouts (> ...)
        if line.startswith('> '):
            callout_raw = line[2:].strip()
            callout_text = format_inline_markdown(callout_raw)
            t_callout = Table([[Paragraph(f"<b>Aviso:</b> {callout_text}", s_callout)]], colWidths=[515])
            t_callout.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF0F2")),
                ('LEFTPADDING', (0,0), (-1,-1), 9),
                ('RIGHTPADDING', (0,0), (-1,-1), 9),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('BOX', (0,0), (-1,-1), 0.8, c_rosa),
            ]))
            story.append(t_callout)
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Bullets (* ou - ou números)
        if line.startswith('* ') or line.startswith('- ') or re.match(r'^\d+\.\s', line):
            is_num = bool(re.match(r'^\d+\.\s', line))
            num_match = re.match(r'^(\d+\.)\s+', line)
            prefix = f"<b>{num_match.group(1)}</b> " if is_num else "&bull; "
            raw_b = re.sub(r'^(\*|-|\d+\.)\s+', '', line).strip()
            b_text = format_inline_markdown(raw_b)
            story.append(Paragraph(f"{prefix}{b_text}", s_bullet))
            i += 1
            continue

        # Parágrafo normal
        p_text = format_inline_markdown(line)
        story.append(Paragraph(p_text, s_p))
        i += 1

    # Compilação do PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Sucesso: PDF gerado com sucesso em: {pdf_path}")
    print(f"Tamanho do arquivo: {pdf_path.stat().st_size} bytes")


if __name__ == "__main__":
    build_pdf()
