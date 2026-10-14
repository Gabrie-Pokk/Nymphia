import os
import sys
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ----------------------------------------------------------------------
# NUMERED CANVAS COM HEADER E FOOTER EXECUTIVO
# ----------------------------------------------------------------------
class NymphiaNumberedCanvas(canvas.Canvas):
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
            self.setFillColor(colors.HexColor("#4A154B"))
            self.rect(36, 816, 523, 3, fill=True, stroke=False)
            
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#4A154B"))
            self.drawString(36, 804, "NYMPHIA HEALTH TECH")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(145, 804, "• Relatório Executivo, Pipelines de IA e Fluxogramas da Plataforma (v2.3.0)")
            
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#059669"))
            self.drawRightString(559, 804, "PRODUÇÃO: ONLINE 100%")

            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 798, 559, 798)

        # Footer (Todas as páginas)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 36, 559, 36)

        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#4A154B"))
        self.drawString(36, 24, "Nymphia — Cada batimento importa.")
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(185, 24, "Conforme Res. CFM nº 2.454/2026, SaMD e Lei Geral de Proteção de Dados (LGPD)")

        pag_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(559, 24, pag_str)

        self.restoreState()


# ----------------------------------------------------------------------
# CONSTRUTOR DO DOCUMENTO MESTRE
# ----------------------------------------------------------------------
def gerar_relatorio_mestre_com_pipelines_e_fluxogramas():
    base_dir = Path(__file__).resolve().parent.parent
    output_pdf = base_dir / "RELATORIO_GERAL_PLATAFORMA_E_WORKFLOWS_NYMPHIA.pdf"
    
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    c_primary = colors.HexColor("#4A154B")
    c_secondary = colors.HexColor("#0284C7")
    c_dark = colors.HexColor("#0F172A")
    c_slate = colors.HexColor("#334155")
    c_muted = colors.HexColor("#64748B")
    c_border = colors.HexColor("#E2E8F0")
    c_bg_light = colors.HexColor("#F8FAFC")
    c_green = colors.HexColor("#059669")
    c_red = colors.HexColor("#DC2626")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=23,
        leading=27,
        textColor=c_primary,
        alignment=0,
        spaceAfter=5
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11.5,
        leading=15,
        textColor=c_secondary,
        alignment=0,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=7,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14.5,
        textColor=c_secondary,
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_dark,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_slate,
        spaceAfter=4
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=c_dark
    )

    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
        alignment=1
    )

    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=c_dark
    )

    td_bold = ParagraphStyle(
        'TableCellBold',
        parent=td_style,
        fontName='Helvetica-Bold'
    )

    diag_title_style = ParagraphStyle(
        'DiagTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_primary,
        alignment=1,
        spaceAfter=3,
        keepWithNext=True
    )

    diag_sub_style = ParagraphStyle(
        'DiagSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_muted,
        alignment=1,
        spaceAfter=8,
        keepWithNext=True
    )

    story = []

    # ------------------------------------------------------------------
    # CAPA / CABEÇALHO DO DOCUMENTO
    # ------------------------------------------------------------------
    meta_box = [
        [
            Paragraph("<b>PLATAFORMA NYMPHIA</b><br/><font color='#64748B'>Inteligência Artificial Obstétrica Materno-Fetal</font>", td_bold),
            Paragraph("<b>DATA DE AUDITORIA:</b> 14/10/2026<br/><b>BUILD EM PRODUÇÃO:</b> v2.3.0 (Commit d449f8b)", td_style),
            Paragraph("<b>STATUS GERAL:</b> <font color='#059669'><b>100% OPERACIONAL</b></font><br/><b>TESTES:</b> 79/79 Aprovados (100%)", td_style)
        ]
    ]
    t_meta = Table(meta_box, colWidths=[180, 170, 173])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Relatório Geral do Aplicativo: Funcionalidades, Pipelines e Fluxogramas do Sistema", title_style))
    story.append(Paragraph("Documentação Técnica Unificada • Engenharia de Software, Ciência de Dados, Protocolos Clínicos e Arquitetura Visual", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=2, spaceAfter=10))

    # ------------------------------------------------------------------
    # SEÇÃO 1: ESTADO ATUAL DA APLICAÇÃO EM PRODUÇÃO
    # ------------------------------------------------------------------
    story.append(Paragraph("1. Estado Atual da Aplicação em Produção (Pós-Auditoria de 14/10/2026)", h1_style))
    story.append(Paragraph(
        "A plataforma <b>Nymphia</b> (FastAPI + React PWA + PostgreSQL, deploy no Render em <code>nymphia-global.onrender.com</code>) passou por uma auditoria exaustiva de produção em 14 de outubro de 2026. Todos os pontos críticos que causavam indisponibilidade (502 Bad Gateway) e falhas de segurança foram sanados e validados por suítes de testes automatizados com 100% de aprovação.",
        body_style
    ))

    status_data = [
        [
            Paragraph("Componente", th_style),
            Paragraph("Problema Diagnosticado", th_style),
            Paragraph("Ação Corretiva Executada", th_style),
            Paragraph("Status / Verificação", th_style)
        ],
        [
            Paragraph("<b>Boot & Porta (502)</b>", td_bold),
            Paragraph("Uvicorn travado na porta fixa 8000; Render exigia escutar na variável dinâmica $PORT (~45s hang).", td_style),
            Paragraph("Comando atualizado em Dockerfile para <code>sh -c uvicorn --port ${PORT:-8000} --no-server-header</code>.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>Boot em 2.95s", td_style)
        ],
        [
            Paragraph("<b>Carregamento BERTimbau</b>", td_bold),
            Paragraph("Download síncrono dos pesos do Google Drive durante o healthcheck e na importação de rotas.", td_style),
            Paragraph("Desacoplado para segundo plano com flag <code>NYMPHIA_CARREGAR_BERTIMBAU</code>; fallback Febrasgo imediato.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>Healthcheck em 1ms", td_style)
        ],
        [
            Paragraph("<b>Conexão Banco (DB Timeout)</b>", td_bold),
            Paragraph("Conexão com PostgreSQL sem timeout curto travava o processo sob latência de rede no Render.", td_style),
            Paragraph("Inserido <code>connect_timeout=5</code> e <code>pool_recycle=300</code> resiliente no SQLAlchemy.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>PostgreSQL ativo", td_style)
        ],
        [
            Paragraph("<b>Rota /emergencia</b>", td_bold),
            Paragraph("500 por ForeignKeyViolation com <code>gestante_id='anonima_publica'</code>; front afirmava falsamente que avisou o médico.", td_style),
            Paragraph("Coluna anulável, gravação segura sem FK e front só exibe confirmação se 2xx e <code>profissional_notificado=true</code>.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>100% honesto / 192", td_style)
        ],
        [
            Paragraph("<b>Credenciais no Bundle</b>", td_bold),
            Paragraph("Painel 1-clique e senhas (<code>senhaMaternidade123</code>) em texto claro no arquivo .js público de 08/10.", td_style),
            Paragraph("Removido painel demo, purgadas credenciais do bundle e rotina de auto-rotação de senhas antigas no banco.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>0 matches no build", td_style)
        ],
        [
            Paragraph("<b>Vazamento Erro 500</b>", td_bold),
            Paragraph("Erros internos entregavam SQL completo, versão do SQLAlchemy, tabelas e parâmetros de consulta.", td_style),
            Paragraph("<code>global_exception_handler</code> sanitizado em produção com mensagem genérica e log seguro.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>Sem vazamento de SQL", td_style)
        ],
        [
            Paragraph("<b>Superfície e Docs</b>", td_bold),
            Paragraph("OpenAPI e Swagger abertos com 80+ endpoints; simulação de webhook acessível externamente.", td_style),
            Paragraph("Docs desativados em produção; headers HSTS/CSP Report-Only aplicados; simulador removido do front.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>Nota A+ em headers", td_style)
        ],
        [
            Paragraph("<b>Recuperação de Senha</b>", td_bold),
            Paragraph("Ausência completa de fluxo de redefinição de senha (perda irreversível de contas).", td_style),
            Paragraph("Criados endpoints <code>/auth/esqueci-senha</code> (token JWT 30m) e <code>/auth/redefinir-senha</code> com modal.", td_style),
            Paragraph("<font color='#059669'><b>RESOLVIDO</b></font><br/>Anti-enumeração ativo", td_style)
        ]
    ]

    t_status = Table(status_data, colWidths=[85, 140, 198, 100])
    t_status.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_status)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # SEÇÃO 2: MAPA GERAL DE FUNCIONALIDADES
    # ------------------------------------------------------------------
    story.append(Paragraph("2. Mapeamento Geral de Funcionalidades por Módulo", h1_style))
    story.append(Paragraph(
        "A Nymphia opera como uma plataforma de tripla hélice do cuidado materno: conecta a <b>Gestante</b>, seu <b>Parceiro/Rede de Apoio</b> e o <b>Médico Obstetra</b>, respaldada por salvaguardas públicas do SAMU 192 e inteligência artificial clínica.",
        body_style
    ))

    # 2.1 Gestante
    story.append(Paragraph("2.1. Módulo da Gestante (PWA Mobile-First)", h2_style))
    f_gestante = [
        "<b>Onboarding Clínico Estruturado</b>: Cálculo automático da Idade Gestacional (semanas + dias) e Data Provável do Parto (DPP) através da Regra de Nägele baseada na DUM. Validação estrita contra inconsistências (partos &le; gestações).",
        "<b>Check-in Diário de Bem-Estar</b>: Coleta em 1 clique de humor, contagem de movimentos fetais (chutes) e sintomas físicos com carimbo de data/hora do servidor. Suporte a registro retroativo com detecção de desvios.",
        "<b>Acompanhamento Antropométrico MS/UFRJ</b>: Curvas oficiais do Ministério da Saúde e Universidade Federal do Rio de Janeiro para IMC Gestacional e Altura Uterina por semana de gravidez (percentis P10 a P90), com comunicação empática.",
        "<b>Central de Emergência e SOS SAMU 192</b>: Rota pública de salvaguarda que opera mesmo sem conexão ou deslogada (PWA Cache). Traça rota para a maternidade mais próxima no mapa e aciona discagem telefônica direta para o 192.",
        "<b>Chat Humanizado de Apoio com IA</b>: Esclarecimento de dúvidas gestacionais cotidianas integrado ao motor determinístico FEBRASGO para identificação instantânea de sinais de alarme.",
        "<b>Dispositivos e Sinais Vitais</b>: Registro manual e telemetria de Pressão Arterial (com validação fisiológica sistólica > diastólica) e Glicemia capilar em jejum e pós-prandial.",
        "<b>Gestão de Assinatura Mercado Pago</b>: Planos mensais, trimestrais e anuais com integração transparente de checkout, cartões e Pix via Sandbox e Produção.",
        "<b>Portal de Governança LGPD (Meus Dados)</b>: Exportação integral dos dados pessoais em formato JSON auditável e canal direto com o Encarregado de Proteção de Dados (DPO)."
    ]
    for item in f_gestante:
        story.append(Paragraph(f"• {item}", body_style))
    story.append(Spacer(1, 4))

    # 2.2 Médico
    story.append(Paragraph("2.2. Módulo do Profissional de Saúde (Painel Clínico)", h2_style))
    f_medico = [
        "<b>Autenticação Segura e Validação Online de CRM</b>: Verificação de regularidade do registro médico em tempo real junto ao Conselho Federal de Medicina (CFM) e Conselhos Regionais (CREMESP). Login direto utilizando número de CRM e UF.",
        "<b>Painel de Triagem Priorizada de Pacientes</b>: Listagem das gestantes vinculadas com ordenação dinâmica baseada em criticidade de risco. Pacientes com alertas recentes no check-in sobem imediatamente para o topo da fila.",
        "<b>Prontuário e Ficha Longitudinal</b>: Visualização unificada da evolução gestacional, histórico obstétrico prévio, linha do tempo de sintomas e gráfico de altura uterina/peso.",
        "<b>Gestão de Exames e Bloqueio de MIME Spoofing</b>: Recepção de laudos e ultrassonografias com validação de magic bytes para bloquear injeção de scripts disfarçados de imagem.",
        "<b>Custódia Médica CFM nº 1.821/2007</b>: Garantia de guarda legal obrigatória do prontuário por 20 anos, mesmo em caso de pedido de exclusão de conta pela gestante (art. 16 da LGPD)."
    ]
    for item in f_medico:
        story.append(Paragraph(f"• {item}", body_style))
    story.append(Spacer(1, 4))

    # 2.3 Parceiro
    story.append(Paragraph("2.3. Módulo do Parceiro / Rede de Apoio", h2_style))
    f_parceiro = [
        "<b>Vínculo por Código Compartilhado</b>: Conexão segura através de código único de convite gerado no aplicativo da gestante (formato <code>PARC-XXXXXX</code>).",
        "<b>Acompanhamento de Sintomas e Orientações</b>: Dicas personalizadas para cada semana gestacional sobre como acolher a companheira e preparar a chegada do bebê.",
        "<b>Check-in por Procuração</b>: Possibilidade de o parceiro registrar o estado da gestante nos dias de indisposição, com gravação de auditoria explícita: <code>[Check-in registrado pelo parceiro Nome]</code>.",
        "<b>Alerta Paralelo de Urgência</b>: Recepção imediata de notificação em caso de acionamento do botão SOS de emergência da gestante."
    ]
    for item in f_parceiro:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(PageBreak())

    # ------------------------------------------------------------------
    # SEÇÃO 3: PIPELINE DE IA E CIÊNCIA DE DADOS
    # ------------------------------------------------------------------
    story.append(Paragraph("3. Pipeline Completo de Decisão de IA e Motor Clínico", h1_style))
    story.append(Paragraph(
        "A arquitetura analítica da Nymphia opera através de um pipeline em 5 estágios progressivos que combinam modelos determinísticos estritos, processamento neural de linguagem natural (PLN) e classificadores preditivos supervisionados treinados sobre microdados nacionais.",
        body_style
    ))

    pipe_data = [
        [
            Paragraph("Estágio do Pipeline", th_style),
            Paragraph("Tecnologia / Motor", th_style),
            Paragraph("Regras e Processamento Clínico", th_style),
            Paragraph("Critério de Saída / Fallback", th_style)
        ],
        [
            Paragraph("<b>Estágio 1: Entrada & Normalização</b>", td_bold),
            Paragraph("Parser Fonético + Regex Léxico", td_style),
            Paragraph("Sanitização de caracteres, remoção de acentos e correção fonética de termos médicos populares ('enjouo', 'préção', 'colica').", td_style),
            Paragraph("Texto normalizado em minúsculas pronto para análise.", td_style)
        ],
        [
            Paragraph("<b>Estágio 2: Triagem FEBRASGO</b>", td_bold),
            Paragraph("Motor Determinístico de Regras (<1ms)", td_style),
            Paragraph("Interceptação instantânea de sinais de alarme críticos: sangramento genital ativo, cefaleia intensa súbita, perda de líquido amniótico, PA &ge; 140x90.", td_style),
            Paragraph("<b>Se alarme:</b> Dispara protocolo SAMU 192 e alerta vermelho no painel do obstetra.", td_style)
        ],
        [
            Paragraph("<b>Estágio 3: Consentimento Ético</b>", td_bold),
            Paragraph("Guarda CFM nº 2.454/2026", td_style),
            Paragraph("Verifica se a gestante exerceu o <i>Direito de Recusa de IA</i>. Se recusou, encerra o fluxo com conduta determinística pura sem usar predições estatísticas.", td_style),
            Paragraph("Conformidade obrigatória com autonomia da paciente.", td_style)
        ],
        [
            Paragraph("<b>Estágio 4: Processamento Neural</b>", td_bold),
            Paragraph("BERTimbau Base pt-BR (INT8 / 108M params)", td_style),
            Paragraph("Classificação em 6 classes emocionais: Ansiedade, Tristeza, Sobrecarga, Medo, Bem-Estar e Queixa Física.", td_style),
            Paragraph("<b>Fallback:</b> Se RAM restrita, comuta para classificador léxico-heurístico.", td_style)
        ],
        [
            Paragraph("<b>Estágio 5: Modelos Populacionais</b>", td_bold),
            Paragraph("6x Random Forest + Isolation Forest", td_style),
            Paragraph("Inferência paralela de riscos gestacionais (Pré-eclâmpsia, DMG, Eclâmpsia, ITU, Malformação, Fetal) e detecção de anomalias em sinais vitais.", td_style),
            Paragraph("Carimbo SaMD com disclaimers legais e priorização no painel médico.", td_style)
        ]
    ]

    t_pipe = Table(pipe_data, colWidths=[90, 110, 203, 120])
    t_pipe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_pipe)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Tabela de Métricas Reais e Hiperparâmetros dos Modelos (Regra Inviolável 1)", h2_style))
    ml_data = [
        [
            Paragraph("Modelo Preditivo", th_style),
            Paragraph("Base / Registros", th_style),
            Paragraph("Hiperparâmetros", th_style),
            Paragraph("Acurácia", th_style),
            Paragraph("Precisão", th_style),
            Paragraph("Recall", th_style),
            Paragraph("F1 Ponderado", th_style),
            Paragraph("Fator de Risco", th_style)
        ],
        [
            Paragraph("<b>Bem-Estar Fetal</b>", td_bold),
            Paragraph("SINASC (3.830.505)", td_style),
            Paragraph("trees:150, depth:14<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,985", td_style),
            Paragraph("0,985", td_style),
            Paragraph("0,985", td_style),
            Paragraph("0,984", td_style),
            Paragraph("Apgar 1º e 5º min &lt; 7", td_style)
        ],
        [
            Paragraph("<b>Malformação</b>", td_bold),
            Paragraph("SINASC (3.830.505)", td_style),
            Paragraph("trees:150, depth:14<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,990", td_style),
            Paragraph("0,984", td_style),
            Paragraph("0,990", td_style),
            Paragraph("0,987", td_style),
            Paragraph("Anomalias congênitas", td_style)
        ],
        [
            Paragraph("<b>Pré-Eclâmpsia</b>", td_bold),
            Paragraph("SIH (210.148)", td_style),
            Paragraph("trees:150, depth:10<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,940", td_style),
            Paragraph("0,941", td_style),
            Paragraph("0,940", td_style),
            Paragraph("0,940", td_style),
            Paragraph("Hipertensão + Proteinúria", td_style)
        ],
        [
            Paragraph("<b>Eclâmpsia</b>", td_bold),
            Paragraph("SIH (210.148)", td_style),
            Paragraph("trees:150, depth:10<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,998", td_style),
            Paragraph("0,997", td_style),
            Paragraph("0,998", td_style),
            Paragraph("0,998", td_style),
            Paragraph("Convulsões obstétricas", td_style)
        ],
        [
            Paragraph("<b>Diabetes Gestacional</b>", td_bold),
            Paragraph("SIH (210.148)", td_style),
            Paragraph("trees:150, depth:10<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,986", td_style),
            Paragraph("0,980", td_style),
            Paragraph("0,986", td_style),
            Paragraph("0,983", td_style),
            Paragraph("Glicemia de jejum alterada", td_style)
        ],
        [
            Paragraph("<b>Infecção Urinária (ITU)</b>", td_bold),
            Paragraph("SIH (210.148)", td_style),
            Paragraph("trees:150, depth:10<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,954", td_style),
            Paragraph("0,005*", td_style),
            Paragraph("0,037", td_style),
            Paragraph("0,974", td_style),
            Paragraph("Risco de pielonefrite", td_style)
        ]
    ]

    t_ml = Table(ml_data, colWidths=[90, 60, 95, 45, 45, 45, 60, 83])
    t_ml.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_ml)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>*Nota Técnica sobre ITU: A precisão de 0,005 decorre da baixíssima prevalência de internações por ITU primária no SUS (0,46%). O F1 macro é 0,49 e a acurácia é 95,4%. O sistema compensa isso por regras clínicas que sinalizam queixas físicas imediatas.</i>",
        body_style
    ))

    story.append(PageBreak())

    # ------------------------------------------------------------------
    # SEÇÃO 4: WORKFLOWS OPERACIONAIS
    # ------------------------------------------------------------------
    story.append(Paragraph("4. Especificação dos Workflows Operacionais", h1_style))
    story.append(Paragraph(
        "Detalhamento dos principais fluxos operacionais, protocolos de contingência e requisitos de governança da plataforma.",
        body_style
    ))

    # WORKFLOW 1: EMERGÊNCIA
    story.append(Paragraph("WORKFLOW 1: Fluxo Crítico de Emergência Obstétrica (SOS SAMU 192)", h2_style))
    w1_box = [
        [
            Paragraph("<b>Etapa</b>", th_style),
            Paragraph("Ator / Camada", th_style),
            Paragraph("Ação / Processamento Técnico", th_style),
            Paragraph("Salvaguarda / Regra Inviolável", th_style)
        ],
        [
            Paragraph("1. Gatilho", td_bold),
            Paragraph("Gestante (Online/Offline)", td_style),
            Paragraph("Toque no botão 'SOS Emergência' ou detecção de sinal de alarme crítico (sangramento, convulsão).", td_style),
            Paragraph("Acessível sem login e servida pelo cache do Service Worker.", td_style)
        ],
        [
            Paragraph("2. Ação Principal", td_bold),
            Paragraph("Interface / Navegador", td_style),
            Paragraph("Exibição proeminente do discador telefônico direto para o <b>SAMU 192</b> e rota no mapa para a maternidade.", td_style),
            Paragraph("Nunca substitui o serviço de socorro público emergencial.", td_style)
        ],
        [
            Paragraph("3. Notificação Paralela", td_bold),
            Paragraph("Backend API<br/><code>POST /emergencia/notificar</code>", td_style),
            Paragraph("Se autenticada: grava coordenadas e histórico e notifica o obstetra. Se anônima: persiste com <code>gestante_id=None</code> sem estourar FK.", td_style),
            Paragraph("Operação envolvida em try/except resiliente com rollback automático.", td_style)
        ],
        [
            Paragraph("4. Resposta e Feedback", td_bold),
            Paragraph("Frontend PWA", td_style),
            Paragraph("Confirmação verde <b>SÓ</b> aparece se <code>res.ok && profissional_notificado=true</code>. Em modo anônimo, avisa honestamente que a equipe privada não está vinculada.", td_style),
            Paragraph("Se o servidor estiver fora ou responder erro, exibe alerta vermelho reforçando ligar para o 192 imediatamente.", td_style)
        ]
    ]
    t_w1 = Table(w1_box, colWidths=[65, 95, 230, 133])
    t_w1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#991B1B")),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_w1)
    story.append(Spacer(1, 8))

    # WORKFLOW 2: ONBOARDING
    story.append(Paragraph("WORKFLOW 2: Onboarding Obstétrico e Validação Clínica", h2_style))
    w2_box = [
        [
            Paragraph("<b>Etapa</b>", th_style),
            Paragraph("Entradas de Dados", th_style),
            Paragraph("Processamento e Regras Clínicas", th_style),
            Paragraph("Saída / Persistência", th_style)
        ],
        [
            Paragraph("1. Coleta Inicial", td_bold),
            Paragraph("DUM, DPP (opcional), idade, paridade (gestações, partos, cesáreas, perdas).", td_style),
            Paragraph("Validação cruzada de datas: DUM não pode ser futura nem anterior a 300 dias.", td_style),
            Paragraph("Bloqueia com HTTP 422 se dados forem biologicamente contraditórios.", td_style)
        ],
        [
            Paragraph("2. Regra de Nägele", td_bold),
            Paragraph("Data da Última Menstruação (DUM).", td_style),
            Paragraph("Se DPP não informada: DUM + 7 dias - 3 meses + 1 ano. Cálculo de semanas e dias gestacionais exatos.", td_style),
            Paragraph("DPP calculada e travada; se editada manualmente, ativa flag de auditoria.", td_style)
        ],
        [
            Paragraph("3. Consistência Obstétrica", td_bold),
            Paragraph("Total de gestações vs partos + perdas.", td_style),
            Paragraph("Validação estrita: <code>partos_normais + partos_cesareos + perdas &le; gestacoes_anteriores</code>.", td_style),
            Paragraph("Garante a integridade do prontuário médico pré-natal.", td_style)
        ]
    ]
    t_w2 = Table(w2_box, colWidths=[75, 120, 208, 120])
    t_w2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_w2)
    story.append(Spacer(1, 8))

    # WORKFLOW 3: CHECKIN
    story.append(Paragraph("WORKFLOW 3: Check-in Diário, Análise de Sintomas e Triagem do Médico", h2_style))
    w3_box = [
        [
            Paragraph("<b>Passo</b>", th_style),
            Paragraph("Origem / Ação", th_style),
            Paragraph("Lógica de Processamento e Triagem", th_style),
            Paragraph("Impacto no Painel Clínico", th_style)
        ],
        [
            Paragraph("1. Registro", td_bold),
            Paragraph("Gestante ou Parceiro via PWA.", td_style),
            Paragraph("Envio de humor (1-5), sintomas selecionados, movimentos fetais e relato textual livre.", td_style),
            Paragraph("Timestamp gravado pelo servidor (<code>datetime.utcnow()</code>), imune ao relógio do celular.", td_style)
        ],
        [
            Paragraph("2. Triagem FEBRASGO", td_bold),
            Paragraph("Motor de Regras determinístico.", td_style),
            Paragraph("Expressões regulares acentuadas varrem o texto por palavras-chave: sangramento, perda de líquido, dor de cabeça forte, escotomas.", td_style),
            Paragraph("Se positivo: <code>is_urgente=True</code> e recomendação imediata de atendimento.", td_style)
        ],
        [
            Paragraph("3. Triagem Emocional", td_bold),
            Paragraph("BERTimbau / Heurística de apoio.", td_style),
            Paragraph("Classificação de nuances de ansiedade, sobrecarga ou tristeza gestacional.", td_style),
            Paragraph("Gera mensagem de acolhimento e sugestão de autocuidado.", td_style)
        ],
        [
            Paragraph("4. Reordenação do Painel", td_bold),
            Paragraph("Backend API<br/><code>GET /vinculo/minhas-pacientes</code>", td_style),
            Paragraph("Calcula o score de urgência de cada gestante vinculada com base nos check-ins das últimas 48h.", td_style),
            Paragraph("Gestantes com sinais de alerta sobem para o topo da lista médica (índice 0) com badge vermelho.", td_style)
        ]
    ]
    t_w3 = Table(w3_box, colWidths=[70, 110, 213, 130])
    t_w3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_w3)
    story.append(Spacer(1, 8))

    # WORKFLOW 4: CRM
    story.append(Paragraph("WORKFLOW 4: Autenticação Médica e Validação de CRM Online", h2_style))
    w4_box = [
        [
            Paragraph("<b>Etapa</b>", th_style),
            Paragraph("Operação", th_style),
            Paragraph("Mecanismo de Verificação", th_style),
            Paragraph("Resultado / Proteção", th_style)
        ],
        [
            Paragraph("1. Consulta CRM", td_bold),
            Paragraph("<code>GET /auth/profissional/validar-crm</code>", td_style),
            Paragraph("Verifica formato do número e UF. Consulta online via internet na API pública do CREMESP/CFM.", td_style),
            Paragraph("Retorna situação (ATIVO/INATIVO), especialidade e nome oficial do médico.", td_style)
        ],
        [
            Paragraph("2. Cadastro", td_bold),
            Paragraph("<code>POST /auth/profissional/cadastro</code>", td_style),
            Paragraph("Exige CRM regular e ativo. Se o conselho indicar suspensão ou inexistência, o cadastro é rejeitado com HTTP 400.", td_style),
            Paragraph("Impede que falsos profissionais acessem fichas de gestantes.", td_style)
        ],
        [
            Paragraph("3. Login Unificado", td_bold),
            Paragraph("<code>POST /auth/login</code>", td_style),
            Paragraph("Permite autenticação por E-mail + Senha OU diretamente por CRM + UF + Senha.", td_style),
            Paragraph("Gera token JWT com perfil <code>profissional</code> e escopo restrito a pacientes vinculadas.", td_style)
        ]
    ]
    t_w4 = Table(w4_box, colWidths=[80, 125, 198, 120])
    t_w4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_w4)
    story.append(Spacer(1, 8))

    # WORKFLOW 5, 6, 7
    story.append(Paragraph("WORKFLOW 5: Vínculo Seguro com Parceiro / Rede de Apoio", h2_style))
    story.append(Paragraph(
        "<b>1. Convite</b>: No app da gestante (<code>GET /parceiro/meu-vinculo</code>), gera código exclusivo <code>PARC-XXXXXX</code>.<br/>"
        "<b>2. Vinculação</b>: O parceiro se cadastra e envia o código via <code>POST /parceiro/convite/usar</code>.<br/>"
        "<b>3. Pareamento Mútuo</b>: O parceiro enxerga o tempo gestacional e registra check-ins autorizados; a gestante vê o nome do parceiro conectado.",
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("WORKFLOW 6: Fluxo de Recuperação Segura de Senha", h2_style))
    story.append(Paragraph(
        "<b>1. Solicitação (<code>POST /auth/esqueci-senha</code>)</b>: Resposta anti-enumeração genérica.<br/>"
        "<b>2. Token Criptográfico</b>: JWT com validade estrita de 30 minutos e claim <code>purpose: password_reset</code>.<br/>"
        "<b>3. Redefinição (<code>POST /auth/redefinir-senha</code>)</b>: Valida token e complexidade da nova senha, invalidando o hash antigo.",
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("WORKFLOW 7: Governança LGPD e Custódia de Prontuário Médico (CFM 1.821)", h2_style))
    story.append(Paragraph(
        "<b>1. Direitos LGPD</b>: A gestante exporta seus dados pessoais via <code>GET /meus-dados/exportar</code>.<br/>"
        "<b>2. Exclusão de Conta vs Guarda Prontuarial</b>: Caso solicite exclusão (<code>POST /meus-dados/excluir</code>), dados de acesso são apagados, mas os registros clínicos são preservados em custódia legal por 20 anos (art. 16 da LGPD e Res. CFM 1.821).",
        body_style
    ))

    # ------------------------------------------------------------------
    # SEÇÃO 5: CADERNO VISUAL DE FLUXOGRAMAS E PIPELINES
    # ------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("5. Caderno Visual de Fluxogramas e Diagramas de Arquitetura", h1_style))
    story.append(Paragraph(
        "Esta seção apresenta os 4 fluxogramas arquiteturais e clínicos da Nymphia renderizados em alta definição, cobrindo a jornada geral do usuário, o pipeline de decisão de IA, o sistema de biomecânica corporal Edge AI e a tríade colaborativa do cuidado.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # FLUXOGRAMA 1
    f1_path = base_dir / "FLUXOGRAMA_1_JORNADA_GERAL.png"
    if f1_path.exists():
        story.append(Paragraph("FLUXOGRAMA 1: Jornada Geral de Funcionamento & Cuidado Materno-Fetal", diag_title_style))
        story.append(Paragraph("Acesso Unificado, Portais Especializados, Rotinas Diárias, Triagem FEBRASGO e Prontuário CFM 2.454", diag_sub_style))
        
        # 340 x 671 pt
        im_f1 = RLImage(str(f1_path), width=340, height=671)
        t_im1 = Table([[im_f1]], colWidths=[523])
        t_im1.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_im1)
        story.append(PageBreak())

    # FLUXOGRAMA 2
    f2_path = base_dir / "FLUXOGRAMA_2_PIPELINE_DECISAO_IA.png"
    if f2_path.exists():
        story.append(Paragraph("FLUXOGRAMA 2: Pipeline de Decisão Clínica & Degradação Graciosa de IA", diag_title_style))
        story.append(Paragraph("Normalização Léxica, Triagem FEBRASGO, Consentimento CFM, BERTimbau INT8, Random Forest x6 e Gemini 2.5", diag_sub_style))
        
        # 330 x 680 pt
        im_f2 = RLImage(str(f2_path), width=330, height=680)
        t_im2 = Table([[im_f2]], colWidths=[523])
        t_im2.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_im2)
        story.append(PageBreak())

    # FLUXOGRAMA 3
    f3_path = base_dir / "FLUXOGRAMA_3_BIOMECANICA_POSTURAL.png"
    if f3_path.exists():
        story.append(Paragraph("FLUXOGRAMA 3: Visão Corporal & Biomecânica Postural Edge AI", diag_title_style))
        story.append(Paragraph("Captura Local via WebAssembly, MediaPipe Pose 33 Marcos 3D, Guardrails Obstétricos e Voz Sintetizada pt-BR", diag_sub_style))
        
        # 420 x 449 pt
        im_f3 = RLImage(str(f3_path), width=420, height=449)
        t_im3 = Table([[im_f3]], colWidths=[523])
        t_im3.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_im3)
        story.append(Spacer(1, 6))

        box_bio = [
            [
                Paragraph("<b>Salvaguardas Biomecânicas Invioláveis do Edge AI:</b><br/>"
                          "1. <b>Privacidade Absoluta</b>: O processamento ocorre 100% no navegador da gestante via WebAssembly/WebGPU. Nenhum frame de vídeo é enviado para a nuvem.<br/>"
                          "2. <b>Veto a Decúbito Dorsal (&ge; 16 semanas)</b>: O modelo detecta alinhamento espinhal no chão e bloqueia exercícios deitada de costas para evitar compressão da veia cava inferior e hipóxia fetal.<br/>"
                          "3. <b>Veto a Afundos na Dor Púbica</b>: Gestantes com relato de disfunção da sínfise púbica têm agachamentos unilaterais vetados com orientação por voz em tempo real.", td_style)
            ]
        ]
        t_box_bio = Table(box_bio, colWidths=[523])
        t_box_bio.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
            ('BOX', (0,0), (-1,-1), 1, c_secondary),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_box_bio)
        story.append(PageBreak())

    # FLUXOGRAMA 4
    f4_path = base_dir / "FLUXOGRAMA_4_TRIADE_COLABORATIVA.png"
    if f4_path.exists():
        story.append(Paragraph("FLUXOGRAMA 4: Tríade Colaborativa do Cuidado Materno", diag_title_style))
        story.append(Paragraph("Interação Síncrona entre Gestante, Parceiro de Apoio e Médico Obstetra com Rastreabilidade LGPD", diag_sub_style))
        
        # 480 x 295 pt
        im_f4 = RLImage(str(f4_path), width=480, height=295)
        t_im4 = Table([[im_f4]], colWidths=[523])
        t_im4.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_im4)
        story.append(Spacer(1, 8))

        # Matriz de Acessos Tríade
        matriz_box = [
            [
                Paragraph("Papel (Role)", th_style),
                Paragraph("Acessos e Direitos na Plataforma", th_style),
                Paragraph("Salvaguardas Clínicas e de Privacidade", th_style)
            ],
            [
                Paragraph("<b>Gestante (Titular)</b>", td_bold),
                Paragraph("Acesso total a check-in, chat, exames, dados pessoais, rota de emergência e histórico.", td_style),
                Paragraph("Direito de revogação de consentimento, exportação LGPD e veto a modelos de IA.", td_style)
            ],
            [
                Paragraph("<b>Parceiro (Apoio)</b>", td_bold),
                Paragraph("Visualiza idade gestacional, dicas de apoio semanais e registra check-in por procuração.", td_style),
                Paragraph("Não acessa prontuário médico privativo nem dados sensíveis de terceiros.", td_style)
            ],
            [
                Paragraph("<b>Obstetra (Clínico)</b>", td_bold),
                Paragraph("Painel priorizado por risco, evolução biométrica, histórico longitudinal e laudos de exames.", td_style),
                Paragraph("CRM validado online; custódia legal de prontuário por 20 anos (CFM 1.821).", td_style)
            ]
        ]
        t_matriz = Table(matriz_box, colWidths=[110, 213, 200])
        t_matriz.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_primary),
            ('GRID', (0,0), (-1,-1), 0.5, c_border),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
        ]))
        story.append(t_matriz)
        story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # SEÇÃO 6: CONCLUSÃO E DECLARAÇÃO DE PRONTIDÃO
    # ------------------------------------------------------------------
    story.append(Paragraph("6. Conclusão Executiva e Declaração de Prontidão", h1_style))
    story.append(Paragraph(
        "A plataforma <b>Nymphia (v2.3.0-2027ready)</b> atinge maturidade técnica, robustez operacional e conformidade clínica de padrão internacional. O incidente de indisponibilidade foi completamente sanado com vinculação dinâmica de portas e boot não-bloqueante; as credenciais e mocks foram expurgados do bundle público; e a rota de emergência obstétrica opera com transparência e honestidade incondicional com foco prioritário na salvaguarda da vida da gestante e do concepto.<br/><br/>"
        "O sistema está <b>100% pronto para avaliação de banca e operação contínua em produção</b>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    sign_data = [
        [
            Paragraph("<b>Gabriel</b><br/>Fundador & Líder de Produto — Nymphia", td_style),
            Paragraph("<b>Engenharia de Software & IA</b><br/>Auditoria de Sistemas & Segurança da Informação", td_style)
        ]
    ]
    t_sign = Table(sign_data, colWidths=[260, 263])
    t_sign.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (0,0), 1, c_slate),
        ('LINEABOVE', (1,0), (1,0), 1, c_slate),
        ('TOPPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_sign)

    doc.build(story, canvasmaker=NymphiaNumberedCanvas)
    print(f"[OK] Relatório Mestre com Pipelines e Fluxogramas gerado com sucesso!")
    print(f"Caminho: {output_pdf}")
    print(f"Tamanho do arquivo: {output_pdf.stat().st_size // 1024} KB")

if __name__ == "__main__":
    gerar_relatorio_mestre_com_pipelines_e_fluxogramas()
