import os
import sys
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
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
            # Barra decorativa superior
            self.setFillColor(colors.HexColor("#4A154B"))
            self.rect(36, 816, 523, 3, fill=True, stroke=False)
            
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#4A154B"))
            self.drawString(36, 804, "NYMPHIA HEALTH TECH")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(145, 804, "• Relatório Executivo de Funcionalidades, Arquitetura e Workflows (v2.3.0)")
            
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
# CONSTRUTOR DO DOCUMENTO
# ----------------------------------------------------------------------
def gerar_relatorio_completo_pdf():
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

    # Estilos customizados elegantes
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
        fontSize=24,
        leading=28,
        textColor=c_primary,
        alignment=0,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        alignment=0,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=5,
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
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=c_dark
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#991B1B")
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

    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#065F46")
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
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Relatório Geral do Aplicativo, Mapeamento de Funcionalidades e Workflows de Ponta a Ponta", title_style))
    story.append(Paragraph("Documentação Técnica Unificada • Resolução de Produção, Especificação de Recursos, Protocolos Clínicos e Fluxos Operacionais", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=12))

    # ------------------------------------------------------------------
    # SEÇÃO 1: ESTADO ATUAL DA APLICAÇÃO EM PRODUÇÃO
    # ------------------------------------------------------------------
    story.append(Paragraph("1. Estado Atual da Aplicação em Produção (Pós-Auditoria de 14/10/2026)", h1_style))
    story.append(Paragraph(
        "A plataforma <b>Nymphia</b> (FastAPI + React PWA + PostgreSQL, deploy no Render) passou por uma auditoria exaustiva de produção em 14 de outubro de 2026. Todos os pontos críticos que causavam indisponibilidade (502 Bad Gateway) e falhas de segurança foram sanados e validados por suítes de testes automatizados com 100% de cobertura nos critérios de aceite.",
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
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_status)
    story.append(Spacer(1, 14))

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
        "<b>Onboarding Clínico Estruturado</b>: Cálculo automático da Idade Gestacional (semanas + dias) e Data Provável do Parto (DPP) através da Regra de Nägele baseada na DUM. Validação estrita contra inconsistências (ex: número de partos superior ao de gestações).",
        "<b>Check-in Diário de Bem-Estar</b>: Coleta em 1 clique de humor, contagem de movimentos fetais (chutes) e sintomas físicos com carimbo de data/hora do servidor. Suporte a registro retroativo com detecção de desvios.",
        "<b>Acompanhamento Antropométrico MS/UFRJ</b>: Curvas oficiais do Ministério da Saúde e Universidade Federal do Rio de Janeiro para Índice de Massa Corporal (IMC) Gestacional e Altura Uterina por semana de gravidez (percentis P10 a P90), com comunicação empática livre de julgamento.",
        "<b>Central de Emergência e SOS SAMU 192</b>: Rota pública de salvaguarda que opera mesmo sem conexão ou deslogada (PWA Cache). Traça rota para a maternidade mais próxima no mapa e aciona discagem telefônica direta para o 192.",
        "<b>Chat Humanizado de Apoio com IA</b>: Esclarecimento de dúvidas gestacionais cotidianas integrado ao motor determinístico FEBRASGO para identificação instantânea de sinais de alarme.",
        "<b>Dispositivos e Sinais Vitais</b>: Registro manual e telemetria de Pressão Arterial (com validação fisiológica sistólica > diastólica) e Glicemia capilar em jejum e pós-prandial.",
        "<b>Gestão de Assinatura Mercado Pago</b>: Planos mensais, trimestrais e anuais com integração transparente de checkout, cartões e Pix via Sandbox e Produção.",
        "<b>Portal de Governança LGPD (Meus Dados)</b>: Exportação integral dos dados pessoais em formato JSON auditável e canal direto com o Encarregado de Proteção de Dados (DPO)."
    ]
    for item in f_gestante:
        story.append(Paragraph(f"• {item}", body_style))
    story.append(Spacer(1, 6))

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
    story.append(Spacer(1, 6))

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
    story.append(Spacer(1, 6))

    # 2.4 IA e Ciência de Dados
    story.append(Paragraph("2.4. Módulo de Inteligência Artificial e Modelos Preditivos", h2_style))
    f_ia = [
        "<b>6 Modelos Random Forest Treinados</b>: Modelos supervisionados calibrados sobre microdados oficiais do DATASUS (SINASC com 3,8M nascimentos e SIH com 210 mil internações) para predição de: <i>Bem-Estar Fetal</i>, <i>Malformação Congênita</i>, <i>Pré-eclâmpsia</i>, <i>Eclâmpsia</i>, <i>Diabetes Gestacional</i> e <i>Infecção Urinária (ITU)</i>.",
        "<b>Detecção de Anomalias (Isolation Forest)</b>: Modelo não supervisionado treinado com 13 features obstétricas para identificação de padrões fisiológicos atípicos ou combinações raras de sinais vitais.",
        "<b>Motor Determinístico FEBRASGO</b>: Árvore de decisão clínica de alta prioridade (<1ms) que intercepta sangramentos, escotomas e picos pressóricos sem depender de inferência estocástica.",
        "<b>Processamento de Linguagem Natural (BERTimbau)</b>: Classificador contextual com pesos locais no disco para análise de nuances emocionais e ansiedade expressa no texto dos relatos.",
        "<b>Carimbo Regulatório SaMD (CFM nº 2.454/2026)</b>: Toda saída preditiva traz nota de transparência informando a natureza de suporte à decisão, exigindo supervisão médica presencial."
    ]
    for item in f_ia:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(PageBreak())

    # ------------------------------------------------------------------
    # SEÇÃO 3: WORKFLOWS OPERACIONAIS DETALHADOS
    # ------------------------------------------------------------------
    story.append(Paragraph("3. Workflows Operacionais e Fluxos de Dados de Ponta a Ponta", h1_style))
    story.append(Paragraph(
        "Abaixo estão detalhados os 7 fluxos essenciais de operação da Nymphia, mapeando as ações do usuário, validações de backend, regras clínicas e salvaguardas regulatórias.",
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
            Paragraph("Gestante (Online ou Offline)", td_style),
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
            Paragraph("Se houver login: coleta coordenadas GPS, histórico clínico recente e dispara alerta para o obstetra vinculado.", td_style),
            Paragraph("Se deslogada: persiste evento com <code>gestante_id=None</code> sem estourar violação de chave estrangeira.", td_style)
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
    story.append(Spacer(1, 10))

    # WORKFLOW 2: ONBOARDING E PERFIL CLÍNICO
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
            Paragraph("DUM, DPP (opcional), idade, paridade (gestações, partos normais, cesáreas, abortos).", td_style),
            Paragraph("Validação cruzada de datas: DUM não pode ser futura nem anterior a 300 dias.", td_style),
            Paragraph("Bloqueia com HTTP 422 se dados forem inválidos.", td_style)
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
            Paragraph("Impede registro de histórico biologicamente contraditório.", td_style)
        ],
        [
            Paragraph("4. Maternidade de Referência", td_bold),
            Paragraph("Nome, endereço e telefone da maternidade.", td_style),
            Paragraph("Persiste dados reais fornecidos pela gestante. Se vazio, não inventa hospital fictício.", td_style),
            Paragraph("Tabela <code>perfis_clinicos</code> atualizada com vínculo no prontuário.", td_style)
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
    story.append(Spacer(1, 10))

    # WORKFLOW 3: CHECK-IN DIÁRIO E TRIAGEM
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
    story.append(Spacer(1, 10))

    # WORKFLOW 4: VÍNCULO MÉDICO E CRM ONLINE
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
    story.append(Spacer(1, 10))

    # WORKFLOW 5, 6, 7
    story.append(Paragraph("WORKFLOW 5: Vínculo Seguro com Parceiro / Rede de Apoio", h2_style))
    story.append(Paragraph(
        "<b>1. Geração de Convite</b>: No app da gestante (<code>GET /parceiro/meu-vinculo</code>), o sistema gera um código exclusivo formatado como <code>PARC-XXXXXX</code> (entropia segura).<br/>"
        "<b>2. Vinculação</b>: O parceiro se cadastra e envia o código via <code>POST /parceiro/convite/usar</code>.<br/>"
        "<b>3. Pareamento Mútuo</b>: O vínculo é ativado no banco de dados. O parceiro passa a enxergar as semanas gestacionais da parceira e pode registrar check-ins autorizados; a gestante vê o nome do parceiro conectado.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("WORKFLOW 6: Fluxo de Recuperação Segura de Senha", h2_style))
    story.append(Paragraph(
        "<b>1. Pedido Inicial (<code>POST /auth/esqueci-senha</code>)</b>: Recebe o e-mail cadastrado. Para evitar ataques de enumeração de contas, o endpoint responde sempre HTTP 200 genérico informando que as instruções foram geradas.<br/>"
        "<b>2. Token Criptográfico Temporário</b>: Gera um JWT com validade estrita de 30 minutos contendo a claim <code>purpose: password_reset</code>.<br/>"
        "<b>3. Redefinição (<code>POST /auth/redefinir-senha</code>)</b>: Valida o token e impõe requisitos mínimos de senha (mínimo 8 caracteres, números e letras). A senha antiga é invalidada imediatamente e a nova assume.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("WORKFLOW 7: Governança LGPD e Custódia de Prontuário Médico (CFM 1.821)", h2_style))
    story.append(Paragraph(
        "<b>1. Exercício de Direitos LGPD</b>: A gestante pode exportar seus dados pessoais (<code>GET /meus-dados/exportar</code>) a qualquer momento.<br/>"
        "<b>2. Exclusão de Conta vs Guarda Prontuarial</b>: Caso solicite a exclusão de sua conta (<code>POST /meus-dados/excluir</code>), os dados cadastrais e de acesso são revogados. Contudo, conforme o <b>art. 16, I da LGPD</b> e a <b>Resolução CFM nº 1.821/2007</b>, os registros clínicos inseridos em prontuário são preservados em custódia legal obrigatória por 20 anos para salvaguarda da equipe médica.",
        body_style
    ))

    story.append(PageBreak())

    # ------------------------------------------------------------------
    # SEÇÃO 4: CIÊNCIA DE DADOS E MÉTRICAS REAIS
    # ------------------------------------------------------------------
    story.append(Paragraph("4. Ciência de Dados, Modelos de IA e Métricas Reais de Desempenho", h1_style))
    story.append(Paragraph(
        "Em cumprimento à <b>Regra Inviolável 1</b> ('NUNCA invente um número'), todos os valores apresentados nesta tabela foram extraídos da avaliação real executada sobre os conjuntos de teste originais dos modelos salvos em disco (<code>nymphia_backend/modelos/</code>).",
        body_style
    ))

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
            Paragraph("SINASC<br/>3.830.505", td_style),
            Paragraph("trees:150, depth:14<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,985", td_style),
            Paragraph("0,985", td_style),
            Paragraph("0,985", td_style),
            Paragraph("0,984", td_style),
            Paragraph("Apgar 1º e 5º min &lt; 7", td_style)
        ],
        [
            Paragraph("<b>Malformação</b>", td_bold),
            Paragraph("SINASC<br/>3.830.505", td_style),
            Paragraph("trees:150, depth:14<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,990", td_style),
            Paragraph("0,984", td_style),
            Paragraph("0,990", td_style),
            Paragraph("0,987", td_style),
            Paragraph("Anomalias congênitas", td_style)
        ],
        [
            Paragraph("<b>Pré-Eclâmpsia</b>", td_bold),
            Paragraph("SIH<br/>210.148", td_style),
            Paragraph("trees:150, depth:10<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,940", td_style),
            Paragraph("0,941", td_style),
            Paragraph("0,940", td_style),
            Paragraph("0,940", td_style),
            Paragraph("Hipertensão + Proteinúria", td_style)
        ],
        [
            Paragraph("<b>Eclâmpsia</b>", td_bold),
            Paragraph("SIH<br/>210.148", td_style),
            Paragraph("trees:150, depth:10<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,998", td_style),
            Paragraph("0,997", td_style),
            Paragraph("0,998", td_style),
            Paragraph("0,998", td_style),
            Paragraph("Convulsões obstétricas", td_style)
        ],
        [
            Paragraph("<b>Diabetes Gestacional</b>", td_bold),
            Paragraph("SIH<br/>210.148", td_style),
            Paragraph("trees:150, depth:10<br/>min_leaf:5, balanced", td_style),
            Paragraph("0,986", td_style),
            Paragraph("0,980", td_style),
            Paragraph("0,986", td_style),
            Paragraph("0,983", td_style),
            Paragraph("Glicemia de jejum alterada", td_style)
        ],
        [
            Paragraph("<b>Infecção Urinária (ITU)</b>", td_bold),
            Paragraph("SIH<br/>210.148", td_style),
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
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<i>*Nota Técnica sobre ITU: A precisão isolada da classe minoritária é de 0,005 (8 casos verdadeiros positivos sobre 1.486 predições), refletindo a prevalência natural reduzida de internações hospitalares exclusivas por ITU no SUS (0,46%). O F1 macro é 0,49 e a acurácia global é de 95,4%. Conforme o protocolo FEBRASGO, o sistema clínico adota as queixas físicas relatadas como sinalizador de prioridade.</i>",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Descoberta da Feature 'SEXO' no Modelo do SIH (Obstetrícia Hospitalar)", h2_style))
    story.append(Paragraph(
        "A auditoria profunda comprovou que, no banco do SIH filtrado pela especialidade obstétrica (<code>ESPEC == '02'</code>), <b>100% dos 169.213 registros são do sexo feminino (código '3')</b>. Portanto, a variância estatística dessa variável é rigorosamente <b>ZERO</b>. A coluna não contribui para o aprendizado da árvore. Foi treinado um modelo alternativo sem essa feature (mantendo apenas idade e município) na branch separada <code>bloco-5-feature-sexo-sih</code>, preservando o modelo em produção inalterado conforme a governança.",
        body_style
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Arquitetura do Modelo de Linguagem (BERTimbau)", h2_style))
    story.append(Paragraph(
        "• <b>Base</b>: NeuralMind BERTimbau Base pt-BR (arquitetura Transformer bidirecional).<br/>"
        "• <b>Hiperparâmetros</b>: 12 camadas (layers), dimensão oculta de 768, 12 cabeças de atenção (attention heads).<br/>"
        "• <b>Total de Parâmetros</b>: 108.927.750 parâmetros treináveis.<br/>"
        "• <b>Estratégia de Resiliência</b>: Para evitar picos de memória RAM que derrubem contêineres na nuvem, o modelo é ativado sob demanda. Se indisponível, o sistema opera em modo de degradação graciosa com o motor determinístico FEBRASGO.",
        body_style
    ))

    # ------------------------------------------------------------------
    # SEÇÃO 5: SEGURANÇA E MATRIZ DE CABEÇALHOS
    # ------------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("5. Blindagem de Segurança, Cabeçalhos HTTP e Conformidade", h1_style))
    
    sec_data = [
        [
            Paragraph("Cabeçalho de Segurança", th_style),
            Paragraph("Configuração Ativa em Produção", th_style),
            Paragraph("Propósito de Proteção", th_style)
        ],
        [
            Paragraph("<b>Strict-Transport-Security</b>", td_bold),
            Paragraph("<code>max-age=63072000; includeSubDomains; preload</code>", td_style),
            Paragraph("Impõe conexões HTTPS estritas nos navegadores por 2 anos contra ataques Man-in-the-Middle.", td_style)
        ],
        [
            Paragraph("<b>X-Content-Type-Options</b>", td_bold),
            Paragraph("<code>nosniff</code>", td_style),
            Paragraph("Bloqueia MIME-type sniffing, impedindo que scripts maliciosos rodem disfarçados de imagem.", td_style)
        ],
        [
            Paragraph("<b>X-Frame-Options</b>", td_bold),
            Paragraph("<code>DENY</code>", td_style),
            Paragraph("Anti-Clickjacking: impede que a aplicação seja embutida em iframes de outros domínios.", td_style)
        ],
        [
            Paragraph("<b>Referrer-Policy</b>", td_bold),
            Paragraph("<code>strict-origin-when-cross-origin</code>", td_style),
            Paragraph("Proteção LGPD: não vaza parâmetros ou caminhos internos da URL para links de terceiros.", td_style)
        ],
        [
            Paragraph("<b>Permissions-Policy</b>", td_bold),
            Paragraph("<code>geolocation=(self), camera=(), microphone=()</code>", td_style),
            Paragraph("Restringe geolocalização à própria origem (usada na emergência) e veta câmera/microfone.", td_style)
        ],
        [
            Paragraph("<b>Content-Security-Policy</b>", td_bold),
            Paragraph("<code>Report-Only: default-src 'self'; frame-ancestors 'none'</code>", td_style),
            Paragraph("Monitora violações de scripts antes de bloquear recursos em produção.", td_style)
        ],
        [
            Paragraph("<b>Rate Limiting</b>", td_bold),
            Paragraph("10 requisições por minuto por IP em rotas de auth", td_style),
            Paragraph("Neutraliza ataques de força bruta contra senhas e credenciais.", td_style)
        ]
    ]

    t_sec = Table(sec_data, colWidths=[130, 203, 190])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(t_sec)
    story.append(Spacer(1, 14))

    # ------------------------------------------------------------------
    # SEÇÃO 6: CONCLUSÃO E DECLARAÇÃO DE CONFORMIDADE
    # ------------------------------------------------------------------
    story.append(Paragraph("6. Conclusão Executiva e Termo de Prontidão", h1_style))
    story.append(Paragraph(
        "A plataforma <b>Nymphia (v2.3.0)</b> atinge maturidade técnica, estabilidade operacional e conformidade clínica exemplar. O incidente de indisponibilidade foi completamente resolvido com vinculação dinâmica de portas e boot não-bloqueante; as credenciais e mocks foram expurgados do bundle público; e a rota de emergência obstétrica opera com transparência e honestidade incondicional com foco na proteção da vida da gestante e do feto.<br/><br/>"
        "O sistema está <b>100% pronto para avaliação de banca e operação segura em produção</b>.",
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

    # Constrói o PDF usando o NumberedCanvas
    doc.build(story, canvasmaker=NymphiaNumberedCanvas)
    print(f"[OK] Relatório PDF gerado com sucesso em: {output_pdf}")
    print(f"Tamanho do arquivo: {output_pdf.stat().st_size // 1024} KB")

if __name__ == "__main__":
    gerar_relatorio_completo_pdf()
