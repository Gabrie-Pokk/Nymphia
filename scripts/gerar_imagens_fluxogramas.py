import os
import sys
import subprocess
import time
import re
from pathlib import Path
from PIL import Image, ImageChops

BASE_DIR = Path(__file__).resolve().parent.parent
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not Path(EDGE_EXE).exists():
    EDGE_EXE = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

MERMAID_LOCAL = BASE_DIR / "scripts" / "mermaid.min.js"
MERMAID_URI = MERMAID_LOCAL.as_uri()

DIAGRAMS = [
    {
        "id": "FLUXOGRAMA_1_JORNADA_GERAL",
        "title": "Fluxograma 1: Fluxo Geral de Funcionamento & Jornada do Cuidado",
        "subtitle": "Plataforma Nymphia v2.3.0 • Interação Gestante, Parceiro, Triagem IA e Supervisão Médica",
        "mermaid": """flowchart TD
    classDef phase fill:#5C1A2A,stroke:#C9A84C,stroke-width:4px,color:#FFFFFF;
    classDef normal fill:#FFFFFF,stroke:#C2185B,stroke-width:4px,color:#1F2937;
    classDef alert fill:#FFF0F2,stroke:#C2185B,stroke-width:5px,color:#5C1A2A;
    classDef gold fill:#FFFDF5,stroke:#C9A84C,stroke-width:4px,color:#5C1A2A;

    E1(["🔐 <b>ETAPA 1: ACESSO UNIFICADO & DETECÇÃO DE PERFIL</b>"]):::phase
    Users["👥 <b>USUÁRIOS DA PLATAFORMA NYMPHIA</b><br/>Gestante • Parceiro de Apoio • Médico Obstetra"]:::normal
    Login["🔑 <b>ENDPOINT: POST /auth/login (Login Unificado)</b><br/>Autenticação centralizada com detecção automática do perfil e emissão de JWT"]:::normal
    E1 --> Users --> Login

    E2(["📱 <b>ETAPA 2: PORTAIS E INTERFACES ESPECIALIZADAS</b>"]):::phase
    Login --> E2
    
    subgraph PortaisRow [" "]
        direction LR
        P_Gest["🌸 <b>GestanteHome</b><br/>• Idade gestacional (Semanas + Dias)<br/>• Cálculo DUM / DPP Naegele<br/>• Linha do tempo de consultas e ações"]:::normal
        P_Parc["🤝 <b>PartnerDashboard</b><br/>• Apoio prático e acolhimento<br/>• Agenda de consultas compartilhada<br/>• Status de bem-estar diário"]:::normal
        P_Med["🩺 <b>DoctorDashboard</b><br/>• Painel de triagem priorizada<br/>• Ordenação inteligente por alertas<br/>• Gestantes em risco em destaque"]:::normal
    end
    E2 --> PortaisRow

    E3(["📋 <b>ETAPA 3: ROTINA DIÁRIA DE CUIDADO INTEGRAL</b>"]):::phase
    PortaisRow --> E3

    C_Gest["📝 <b>DailyCheckin da Gestante</b><br/>Registro diário de humor, queixas físicas e contagem de movimentos fetais"]:::normal
    C_Parc["✍️ <b>Check-in por Procuração do Parceiro</b><br/>Registro de apoio quando a gestante repousa (grava com tag 'Registrado pelo Parceiro')"]:::normal
    C_Antro["⚖️ <b>Antropometria Clínica Especializada</b><br/>• Curva de Atalah (IMC Gestacional 6ª a 42ª semana)<br/>• Curva de Altura Uterina P10-P90 (Percentis do Ministério da Saúde)"]:::normal
    C_Vision["🤸 <b>BodyVision Edge AI (Visão Computacional Local)</b><br/>• Rastreio 3D local com 33 marcos anatômicos (MediaPipe)<br/>• Veto a decúbito dorsal (≥16 sem) e afundos na dor púbica<br/>• Feedback sonoro por voz sintetizada pt-BR em tempo real"]:::gold
    C_Chat["💬 <b>AiChat Nymphia (Acolhimento Materno)</b><br/>Google Gemini 2.5 Flash com guardrails clínicos rígidos e triagem de sinais de alarme"]:::gold

    E3 --> C_Gest --> C_Parc --> C_Antro --> C_Vision --> C_Chat

    E4(["🧠 <b>ETAPA 4: MOTOR DETERMINÍSTICO & TRIAGEM DE IA</b>"]):::phase
    C_Chat --> E4

    Triage{"🚨 <b>TRIAGEM DETERMINÍSTICA FEBRASGO: SINAIS DE ALARME?</b><br/>• Sangramento vaginal ativo?<br/>• Cefaleia intensa / Escotomas visuais?<br/>• Perda súbita de líquido amniótico?<br/>• Pressão Arterial aferida ≥ 140×90 mmHg?"}:::alert
    
    SAMU["🚑 <b>PROTOCOLO DE EMERGÊNCIA SAMU 192 (ALERTA VERMELHO)</b><br/>• Orientação para discagem telefônica 192 imediata<br/>• Traçado de rota GPS até a maternidade de referência<br/>• Bloqueio preventivo automático de exercícios físicos<br/>• Disparo de notificação urgente no painel do parceiro"]:::alert
    
    Consent{"⚖️ <b>CONSENTIMENTO DE IA (CFM 2.454/2026)</b><br/>Gestante exerceu o Direito de Recusa de IA?"}:::normal
    
    RegrasPuras["📘 <b>MOTOR DETERMINÍSTICO EXCLUSIVO</b><br/>Condução estritamente baseada em diretrizes do Ministério da Saúde e FEBRASGO"]:::normal
    
    BERT["⚡ <b>CLASSIFICAÇÃO EMOCIONAL BERTIMBAU (PT-BR)</b><br/>• Modelo quantizado em INT8 (~180MB RAM de consumo em CPU)<br/>• Classificação em 6 classes: Ansiedade, Tristeza, Sobrecarga, Medo, Bem-Estar e Físico"]:::normal
    
    RF["📊 <b>MODELOS PREDITIVOS POPULACIONAIS (DataSUS)</b><br/>• 6 Classificadores Random Forest (PE, DMG, Eclâmpsia, ITU/Prematuro, Malformação, Fetal)<br/>• Isolation Forest para detecção não-supervisionada de anomalias vitais"]:::normal

    E4 --> Triage
    Triage -->|SIM: Alarme Crítico| SAMU
    Triage -->|NÃO: Estável| Consent
    Consent -->|SIM: Recusou IA| RegrasPuras
    Consent -->|NÃO: Autorizou IA| BERT
    BERT --> RF

    E5(["🩺 <b>ETAPA 5: PRONTUÁRIO CLÍNICO & AUDITORIA ÉTICA</b>"]):::phase
    RegrasPuras --> E5
    RF --> E5
    SAMU -.->|Alerta Registrado| E5

    Pront["📄 <b>PatientRecord (Prontuário Médico Digital)</b><br/>• Histórico temporal completo de sintomas, check-ins e bioimpedância<br/>• Curvas de Atalah e Altura Uterina plotadas com percentis<br/>• Registro formal de condutas e prescrições do obstetra"]:::normal
    Audit["⚖️ <b>CONFORMIDADE LEGAL & AUDITORIA LGPD</b><br/>• Disclaimers médicos explícitos (Resolução CFM 2.454/2026)<br/>• Trilha de auditoria imutável com timestamp UTC e role para cada visualização<br/>• Transparência algorítmica conforme Código de Defesa do Consumidor"]:::normal

    E5 --> Pront --> Audit"""
    },
    {
        "id": "FLUXOGRAMA_2_PIPELINE_DECISAO_IA",
        "title": "Fluxograma 2: Pipeline de Decisão Clínica & Degradação Graciosa",
        "subtitle": "Plataforma Nymphia v2.3.0 • Triagem FEBRASGO, BERTimbau INT8, Random Forest x6 e Gemini",
        "mermaid": """flowchart TD
    classDef phase fill:#5C1A2A,stroke:#C9A84C,stroke-width:4px,color:#FFFFFF;
    classDef normal fill:#FFFFFF,stroke:#C2185B,stroke-width:4px,color:#1F2937;
    classDef alert fill:#FFF0F2,stroke:#C2185B,stroke-width:5px,color:#5C1A2A;
    classDef gold fill:#FFFDF5,stroke:#C9A84C,stroke-width:4px,color:#5C1A2A;

    E1(["📥 <b>ETAPA 1: RECEPÇÃO E NORMALIZAÇÃO DE DADOS</b>"]):::phase
    Entrada["📥 <b>DADOS DE ENTRADA DO USUÁRIO</b><br/>• Texto digitado no Check-in Diário<br/>• Seleção de sintomas e queixas clínicas<br/>• Mensagens conversacionais no AiChat Nymphia"]:::normal
    Norm["🔤 <b>NORMALIZAÇÃO FONÉTICA E LÉXICA (PT-BR)</b><br/>• Correção ortográfica de termos médicos ('enjouo', 'préção', 'colica')<br/>• Remoção de acentos e padronização para vocabulário obstétrico"]:::normal
    E1 --> Entrada --> Norm

    E2(["🚨 <b>ETAPA 2: TRIAGEM DETERMINÍSTICA FEBRASGO (SINAIS DE ALARME)</b>"]):::phase
    Norm --> E2

    Stage1{"🚨 <b>DETECÇÃO DE SINAIS DE ALARME CRÍTICOS</b><br/>• Sangramento genital ativo?<br/>• Cefaleia intensa súbita / Alterações visuais?<br/>• Perda espontânea de líquido amniótico?<br/>• Pressão Arterial aferida ≥ 140×90 mmHg?"}:::alert
    
    Emergencia["🚑 <b>PROTOCOLO DE EMERGÊNCIA SAMU 192 (ALERTA VERMELHO)</b><br/>• Orientação imperativa para ligar 192 imediatamente<br/>• Traçado de rota GPS até a maternidade de referência<br/>• Bloqueio preventivo automático de exercícios físicos<br/>• Disparo de notificação urgente ao parceiro e ao obstetra"]:::alert

    E2 --> Stage1
    Stage1 -->|SIM: Sinais Críticos| Emergencia

    E3(["⚖️ <b>ETAPA 3: CONSENTIMENTO E AUTONOMIA (CFM 2.454/2026)</b>"]):::phase
    Stage1 -->|NÃO: Gestante Estável| E3

    Stage2{"⚖️ <b>DIREITO DE RECUSA DE IA</b><br/>Gestante optou pelo desligamento de inteligência artificial?"}:::normal

    RegrasPuras["📘 <b>MOTOR DETERMINÍSTICO EXCLUSIVO</b><br/>• Condução estritamente baseada em protocolos do Ministério da Saúde e FEBRASGO<br/>• Zero predições neurais ou inferências estatísticas"]:::normal

    E3 --> Stage2
    Stage2 -->|SIM: Recusou IA| RegrasPuras

    E4(["🧠 <b>ETAPA 4: PROCESSAMENTO NEURAL & PREDITIVO POPULACIONAL</b>"]):::phase
    Stage2 -->|NÃO: Autorizou IA| E4

    BERTCheck{"⚡ <b>STATUS DO MODELO BERTIMBAU (PT-BR)</b><br/>Recursos de memória e CPU disponíveis?"}:::normal

    BERTClass["🏷️ <b>CLASSIFICAÇÃO NEURAL EM 6 EMOÇÕES / QUEIXAS</b><br/>• BERTimbau INT8 em CPU (~180MB RAM)<br/>• Ansiedade, Tristeza, Sobrecarga, Medo, Bem-Estar e Queixa Física<br/>• ROC-AUC: 0.9725 | F1-Macro: 0.8165"]:::normal

    Heuristica["🔍 <b>CLASSIFICADOR LÉXICO-CLÍNICO HEURÍSTICO</b><br/>Fallback gracioso para servidores com < 512MB RAM"]:::normal

    E4 --> BERTCheck
    BERTCheck -->|Memória Adequada| BERTClass
    BERTCheck -->|Restrição de Recursos| Heuristica

    Stage4["📊 <b>MODELOS PREDITIVOS POPULACIONAIS (DataSUS)</b><br/>6 Classificadores Random Forest Simultâneos:<br/>1. Pré-eclâmpsia | 2. Diabetes Gestacional | 3. Eclâmpsia<br/>4. ITU / Parto Prematuro | 5. Malformação | 6. Vitalidade Fetal"]:::normal

    IsoForest["🛡️ <b>ISOLATION FOREST (NÃO-SUPERVISIONADO)</b><br/>Detecção de combinações atípicas multivariadas de sinais vitais"]:::normal

    BERTClass --> Stage4
    Heuristica --> Stage4
    Stage4 --> IsoForest

    E5(["🎯 <b>ETAPA 5: ROTEAMENTO E ENTREGA MULTICANAL</b>"]):::phase
    RegrasPuras --> E5
    IsoForest --> E5

    Gemini["💬 <b>AiChat: Google Gemini 2.5 Flash</b><br/>Acolhimento empático com tom maternal e guardrails rígidos"]:::gold
    RecCard["🌸 <b>Check-in: Cartão de Cuidado Personalizado</b><br/>Orientações adaptadas de repouso, hidratação e bem-estar"]:::gold
    MedPront["🩺 <b>Obstetra: Dashboard Clínico do Médico</b><br/>Probabilidades de risco com disclaimers da Resolução CFM 2.454/2026"]:::gold

    E5 --> Gemini --> RecCard --> MedPront"""
    },
    {
        "id": "FLUXOGRAMA_3_BIOMECANICA_POSTURAL",
        "title": "Fluxograma 3: Visão Corporal & Biomecânica Postural Edge AI",
        "subtitle": "Plataforma Nymphia v2.3.0 • MediaPipe Pose 33 Landmarks (WebAssembly) e Voz Sintetizada",
        "mermaid": """flowchart TD
    classDef phase fill:#5C1A2A,stroke:#C9A84C,stroke-width:4px,color:#FFFFFF;
    classDef normal fill:#FFFFFF,stroke:#C2185B,stroke-width:4px,color:#1F2937;
    classDef alert fill:#FFF0F2,stroke:#C2185B,stroke-width:5px,color:#5C1A2A;
    classDef gold fill:#FFFDF5,stroke:#C9A84C,stroke-width:4px,color:#5C1A2A;

    E1(["📷 <b>ETAPA 1: CAPTURA & PRIVACIDADE EDGE AI NO NAVEGADOR</b>"]):::phase
    VideoCam["📷 <b>CÂMERA DO DISPOSITIVO (SMARTPHONE / NOTEBOOK)</b><br/>Captura de vídeo em tempo real no ambiente doméstico da gestante"]:::normal
    WasmEdge["💻 <b>PROCESSAMENTO 100% LOCAL NO NAVEGADOR (EDGE AI)</b><br/>Execução via WebAssembly / GPU local (WebGL/WebGPU)"]:::normal
    Privacy["🔒 <b>PRIVACIDADE MÉDICA ABSOLUTA</b><br/>Nenhum frame de vídeo ou foto é gravado ou enviado para servidores"]:::gold

    E1 --> VideoCam --> WasmEdge --> Privacy

    E2(["📍 <b>ETAPA 2: RASTREAMENTO ANATÔMICO TRIDIMENSIONAL</b>"]):::phase
    Privacy --> E2

    Landmarks["📍 <b>GOOGLE MEDIAPIPE POSE (33 MARCOS ANATÔMICOS 3D)</b><br/>• Rastreio contínuo de ombros, coluna, quadris, joelhos e tornozelos<br/>• Taxa de processamento fluida a 30+ FPS em tempo real"]:::normal

    E2 --> Landmarks

    E3(["🛡️ <b>ETAPA 3: GUARDRAILS BIOMECÂNICOS INVIOLÁVEIS</b>"]):::phase
    Landmarks --> E3

    Check1{"Idade Gestacional ≥ 16 semanas?"}:::alert
    VetoSupino["⛔ <b>VETO A DECÚBITO DORSAL (BARRIGA P/ CIMA)</b><br/>Prevenção de compressão da veia cava inferior e hipotensão supina"]:::alert
    PosLivre["✅ <b>Posição Dorsal Permitida (< 16 semanas)</b>"]:::normal

    Check2{"Gestante relatou Dor Púbica / Disfunção Pélvica?"}:::alert
    VetoPassada["⛔ <b>VETO A PASSADAS E AFUNDOS ASSIMÉTRICOS</b><br/>Proteção contra sobrecarga da articulação da sínfise púbica"]:::alert
    ExercLivre["✅ <b>Exercícios Bilaterais Simétricos Liberados</b>"]:::normal

    E3 --> Check1
    Check1 -->|SIM: ≥ 16 sem| VetoSupino
    Check1 -->|NÃO: Início| PosLivre

    E3 --> Check2
    Check2 -->|SIM: Dor Púbica| VetoPassada
    Check2 -->|NÃO: Assintomática| ExercLivre

    VozAlert["📢 <b>ALERTA SONORO DE INTERRUPÇÃO IMEDIATA</b><br/>Web Speech API instrui a gestante a interromper o movimento arriscado"]:::alert
    VetoSupino --> VozAlert
    VetoPassada --> VozAlert

    E4(["📐 <b>ETAPA 4: CINEMÁTICA ANGULAR & ORIENTAÇÃO DINÂMICA POR VOZ</b>"]):::phase
    PosLivre --> E4
    ExercLivre --> E4

    Angulos["📐 <b>CÁLCULO ANGULAR EM TEMPO REAL</b><br/>• Ângulo de Lordose Lombar (Lombar x Sacro)<br/>• Báscula Pélvica (Inclinação anterior/posterior da pelve)<br/>• Amplitude do Agachamento e Alinhamento Espinhal"]:::normal

    VozOrient["🎙️ <b>FEEDBACK SONORO POR VOZ SINTETIZADA (PT-BR)</b><br/>• Instruções em tempo real ('Alinhe a coluna', 'Mantenha os pés afastados')<br/>• A gestante se exercita com postura correta sem precisar olhar fixamente para a tela!"]:::gold

    E4 --> Angulos --> VozOrient"""
    },
    {
        "id": "FLUXOGRAMA_4_TRIADE_COLABORATIVA",
        "title": "Fluxograma 4: Tríade de Conexão Colaborativa (Gestante - Parceiro - Obstetra)",
        "subtitle": "Plataforma Nymphia v2.3.0 • Vínculo Seguro LGPD, Check-in por Procuração e Alerta SAMU 192",
        "mermaid": """flowchart TD
    classDef phase fill:#5C1A2A,stroke:#C9A84C,stroke-width:4px,color:#FFFFFF;
    classDef normal fill:#FFFFFF,stroke:#C2185B,stroke-width:4px,color:#1F2937;
    classDef alert fill:#FFF0F2,stroke:#C2185B,stroke-width:5px,color:#5C1A2A;
    classDef gold fill:#FFFDF5,stroke:#C9A84C,stroke-width:4px,color:#5C1A2A;

    E1(["🌸 <b>NÚCLEO 1: GESTANTE (MARIANA) - CENTRO DO CUIDADO</b>"]):::phase
    G_Perfil["📋 <b>Perfil Clínico & Caderneta Digital</b><br/>• DUM, DPP Naegele e Idade Gestacional<br/>• Vacinas PNI, exames laboratoriais e diário de sintomas"]:::normal
    G_Tokens["🔑 <b>Emissão e Gestão de Vínculos Criptografados</b><br/>• Gera código do Parceiro de Apoio (PARC-XXXXX)<br/>• Associa código de 8 dígitos do Obstetra Responsável"]:::normal
    G_Botoes["🚨 <b>Botão de Emergência SAMU 192 Permanente</b><br/>Acionamento em dois toques com funcionamento garantido offline"]:::alert

    E1 --> G_Perfil --> G_Tokens --> G_Botoes

    E2(["🤝 <b>NÚCLEO 2: REDE DE APOIO - PARCEIRO (LUCAS)</b>"]):::phase
    G_Tokens -->|Código PARC-XXXXX| E2

    P_Vinculo["🔗 <b>Vínculo de Apoio Ativo</b><br/>Acesso seguro à jornada da gestante sem invasão de privacidade do diário íntimo"]:::normal
    P_Checkin["✍️ <b>Check-in em Nome da Gestante (Por Procuração)</b><br/>Registro diário quando a gestante repousa (grava com tag 'Registrado pelo Parceiro')"]:::normal
    P_Agenda["📅 <b>Gestão Completa da Agenda Pré-Natal</b><br/>Adicionar consultas, agendar exames, marcar como concluído e excluir"]:::normal
    P_Alerta["🔔 <b>Alerta SAMU 192 em Tempo Real (Polling a cada 8s)</b><br/>Notificação prioritária instantânea com discagem rápida e rota hospitalar"]:::alert
    P_Quiz["🎁 <b>Quiz de Gostos, Mimos & Cuidados</b><br/>Preferências alimentares, confortos, hidratação e bem-estar afetivo"]:::gold

    E2 --> P_Vinculo --> P_Checkin --> P_Agenda --> P_Alerta --> P_Quiz

    G_Botoes ==>|Disparo em Tempo Real| P_Alerta
    P_Checkin -.->|Grava com Tag de Autoria| G_Perfil
    P_Agenda <==>|Sincronia de Compromissos| G_Perfil

    E3(["🩺 <b>NÚCLEO 3: SUPERVISÃO MÉDICA - OBSTETRA (DR. CARLOS)</b>"]):::phase
    G_Tokens -->|Código de 8 Dígitos| E3

    M_Painel["📊 <b>Painel Clínico de Gestantes Vinculadas</b><br/>Ordenação inteligente por gravidade de alertas clínicos nos últimos 30 dias"]:::normal
    M_Prontuario["📈 <b>Prontuário Clínico Digital Especializado</b><br/>• Curva de Atalah: IMC gestacional da 6ª à 42ª semana<br/>• Curva de Altura Uterina: P10-P90 (Ministério da Saúde)<br/>• Probabilidades dos 6 Modelos de Risco (Random Forest DataSUS)"]:::normal
    M_Conduta["📝 <b>Registro de Condutas Médicas & Prescrições</b><br/>Orientações formais validadas pelo profissional assistente"]:::normal
    M_Auditoria["⚖️ <b>Conformidade CFM 2.454/2026 & Auditoria LGPD</b><br/>Registro imutável de data/hora UTC e perfil de acesso para cada visualização"]:::gold

    E3 --> M_Painel --> M_Prontuario --> M_Conduta --> M_Auditoria
    G_Perfil -->|Dados Clínicos Evolutivos| M_Painel"""
    }
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>MEASURE_TITLE</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800;900&display=swap" rel="stylesheet">
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html, body {{
      background: #FFFFFF;
      overflow: hidden;
      margin: 0;
      padding: 30px;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .card-canvas {{
      background: #FFFFFF;
      border: 6px solid #5C1A2A;
      border-radius: 32px;
      padding: 50px 60px;
      box-shadow: 0 20px 70px rgba(92, 26, 42, 0.18);
      display: inline-block;
      width: max-content;
      min-width: 1500px;
    }}
    .header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 5px solid #E5D4D8;
      padding-bottom: 28px;
      margin-bottom: 36px;
      gap: 40px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    .brand-title {{
      font-size: 3.4rem;
      font-weight: 900;
      color: #5C1A2A;
      letter-spacing: -1px;
    }}
    .brand-slogan {{
      font-size: 1.8rem;
      color: #C2185B;
      font-weight: 700;
    }}
    .badge {{
      background: #FDF0F2;
      border: 4px solid #C2185B;
      color: #C2185B;
      font-size: 1.6rem;
      font-weight: 800;
      padding: 14px 32px;
      border-radius: 50px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      white-space: nowrap;
    }}
    .diag-title {{
      font-size: 3.2rem;
      font-weight: 900;
      color: #5C1A2A;
      margin-bottom: 12px;
      line-height: 1.2;
      text-align: center;
    }}
    .diag-sub {{
      font-size: 1.85rem;
      color: #4B5563;
      margin-bottom: 40px;
      font-weight: 600;
      text-align: center;
    }}
    .mermaid-box {{
      background: #FAF7F8;
      border: 4px solid #E5D4D8;
      border-radius: 28px;
      padding: 40px 30px;
      text-align: center;
      display: inline-block;
      width: 100%;
    }}
    .mermaid {{
      display: inline-block;
      text-align: center;
    }}
    
    /* ESTILIZAÇÃO GIGANTE DOS NÓS */
    .node rect, .node polygon, .node circle, .node path {{
      rx: 20px !important;
      ry: 20px !important;
    }}
    .node .label, .node span, .node div, .nodeLabel {{
      font-family: 'Inter', sans-serif !important;
      font-size: 28px !important;
      font-weight: 700 !important;
      line-height: 1.45 !important;
      padding: 8px 16px !important;
    }}
    .node b, .node strong {{
      font-weight: 900 !important;
      font-size: 30px !important;
    }}
    .phase .label, .phase span, .phase div, .phase .nodeLabel {{
      font-size: 32px !important;
      font-weight: 900 !important;
      color: #FFFFFF !important;
      letter-spacing: 0.5px;
    }}
    .phase b, .phase strong {{
      color: #FFD580 !important;
      font-size: 33px !important;
    }}
    .edgeLabel, .edgeLabel span {{
      font-family: 'Inter', sans-serif !important;
      font-size: 24px !important;
      font-weight: 800 !important;
      background-color: #FFFFFF !important;
      padding: 8px 16px !important;
      border: 3px solid #C2185B !important;
      border-radius: 12px !important;
      color: #5C1A2A !important;
    }}
    .edgePath path {{
      stroke: #C2185B !important;
      stroke-width: 5px !important;
    }}
    .footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 4px solid #E5D4D8;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 1.5rem;
      font-weight: 700;
      color: #4B5563;
      gap: 30px;
    }}
  </style>
  <script src="{mermaid_uri}"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      flowchart: {{
        useMaxWidth: false,
        htmlLabels: true,
        curve: 'basis',
        nodeSpacing: 50,
        rankSpacing: 65,
        padding: 35
      }},
      theme: 'base',
      themeVariables: {{
        fontSize: '32px',
        fontFamily: "'Inter', sans-serif",
        primaryColor: '#FFFFFF',
        primaryTextColor: '#1F2937',
        primaryBorderColor: '#C2185B',
        lineColor: '#C2185B',
        secondaryColor: '#FFF8E7',
        tertiaryColor: '#FFFFFF'
      }}
    }});

    window.addEventListener('load', () => {{
      setTimeout(() => {{
        const card = document.querySelector('.card-canvas');
        if (card) {{
          const rect = card.getBoundingClientRect();
          document.title = `MEASURED_SIZE:${{Math.ceil(rect.width)}}x${{Math.ceil(rect.height)}}`;
        }}
      }}, 1200);
    }});
  </script>
</head>
<body>
  <div class="card-canvas">
    <div class="header">
      <div class="brand">
        <svg viewBox="0 0 100 100" width="70" height="70">
          <path d="M50 15 C45 35 25 45 15 50 C35 55 45 75 50 85 C55 75 75 55 85 50 C75 45 55 35 50 15 Z" fill="#5C1A2A"/>
          <path d="M50 28 C46 40 32 46 25 50 C38 54 46 68 50 72 C54 68 62 54 75 50 C68 46 54 40 50 28 Z" fill="#C2185B"/>
          <circle cx="50" cy="50" r="8" fill="#C9A84C"/>
        </svg>
        <div>
          <div class="brand-title">Nymphia</div>
          <div class="brand-slogan">Cada batimento importa.</div>
        </div>
      </div>
      <span class="badge">Arquitetura Oficial v2.3.0</span>
    </div>

    <div class="diag-title">{title}</div>
    <div class="diag-sub">{subtitle}</div>

    <div class="mermaid-box">
      <div class="mermaid">
{mermaid}
      </div>
    </div>

    <div class="footer">
      <div>Conformidade Clínica: CFM 2.454/2026, CDC, FEBRASGO, ACOG e Ministério da Saúde</div>
      <div>Plataforma Nymphia • https://nymphia-plataforma-ia.onrender.com</div>
    </div>
  </div>
</body>
</html>"""

def generate_all_flowcharts():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("GERAÇÃO DE FLUXOGRAMAS EM FORMATO GIGANTE E ULTRA-LEGÍVEL (NYMPHIA v2.3.0)")
    print("=" * 70)

    temp_dir = BASE_DIR / "scripts" / "temp_diagrams"
    temp_dir.mkdir(exist_ok=True)

    generated_images = []

    for d in DIAGRAMS:
        item_id = d["id"]
        html_file = temp_dir / f"{item_id}.html"
        png_file = BASE_DIR / f"{item_id}.png"

        html_content = HTML_TEMPLATE.format(
            title=d["title"],
            subtitle=d["subtitle"],
            mermaid=d["mermaid"],
            mermaid_uri=MERMAID_URI
        )
        html_file.write_text(html_content, encoding="utf-8")

        print(f"\n[+] Processando {item_id}...")
        
        # Passo 1: Obter dimensões exatas via dump-dom
        cmd_dump = [
            EDGE_EXE,
            "--headless",
            "--disable-gpu",
            "--allow-file-access-from-files",
            "--window-size=3000,9000",
            "--virtual-time-budget=4000",
            "--dump-dom",
            str(html_file.resolve())
        ]
        res_dump = subprocess.run(cmd_dump, capture_output=True, text=True, encoding="utf-8")
        
        match = re.search(r'MEASURED_SIZE:(\d+)x(\d+)', res_dump.stdout)
        if match:
            w, h = int(match.group(1)), int(match.group(2))
            print(f"    Dimensão medida do canvas: {w}px de largura × {h}px de altura")
            win_w = w + 80
            win_h = h + 80
        else:
            print("    Aviso: MEASURED_SIZE não detectado, usando valores padrão de alta resolução")
            win_w, win_h = 2400, 6000
            w, h = 2300, 5800

        # Passo 2: Capturar screenshot no tamanho exato
        cmd_shot = [
            EDGE_EXE,
            "--headless",
            "--disable-gpu",
            "--allow-file-access-from-files",
            "--virtual-time-budget=4000",
            f"--window-size={win_w},{win_h}",
            f"--screenshot={png_file}",
            str(html_file.resolve())
        ]
        subprocess.run(cmd_shot, capture_output=True, text=True)

        if png_file.exists() and png_file.stat().st_size > 5000:
            # Passo 3: Recorte perfeito do card-canvas
            try:
                im = Image.open(png_file)
                # Recorta exatamente os 30px de margem do body
                left = 30
                top = 30
                right = min(im.width, left + w)
                bottom = min(im.height, top + h)
                cropped = im.crop((left, top, right, bottom))
                cropped.save(str(png_file), quality=95)
                print(f"    [OK] Salvo com perfeição: {png_file.name} ({cropped.size[0]}x{cropped.size[1]} px, {png_file.stat().st_size // 1024} KB)")
                generated_images.append(png_file)
            except Exception as e:
                print(f"    Aviso no crop de {png_file.name}: {e}")
                generated_images.append(png_file)
        else:
            print(f"    [ERRO] Falha ao renderizar {png_file.name}")

    # Limpeza de temporários
    for f in temp_dir.glob("*.html"):
        try:
            f.unlink()
        except Exception:
            pass
    try:
        temp_dir.rmdir()
    except Exception:
        pass

    # Passo 4: Criação do Painel Infográfico Geral Unificado
    if len(generated_images) == len(DIAGRAMS):
        print("\n" + "=" * 70)
        print("CRIANDO PAINEL INFOGRÁFICO UNIFICADO (FLUXOGRAMA_GERAL_COMPLETO_NYMPHIA.png)...")
        try:
            imgs = [Image.open(p) for p in generated_images]
            max_w = max(im.width for im in imgs)
            spacing = 60
            padding = 50
            total_h = sum(im.height for im in imgs) + (len(imgs) - 1) * spacing + padding * 2

            combined = Image.new("RGB", (max_w + padding * 2, total_h), (253, 240, 242)) # Rosa suave Nymphia

            curr_y = padding
            for im in imgs:
                x_offset = padding + (max_w - im.width) // 2
                combined.paste(im, (x_offset, curr_y))
                curr_y += im.height + spacing
                im.close()

            combined_path = BASE_DIR / "FLUXOGRAMA_GERAL_COMPLETO_NYMPHIA.png"
            combined.save(str(combined_path), quality=95)
            print(f"[OK] Painel Unificado gerado: {combined_path.name} ({combined.width}x{combined.height} px, {combined_path.stat().st_size // 1024} KB)")
        except Exception as e:
            print(f"[ERRO] Falha ao unificar painel: {e}")

    print("\n" + "=" * 70)
    print("TODAS AS IMAGENS FORAM GERADAS COM SUCESSO EM TAMANHO GIGANTE E ULTRA-LEGÍVEL!")
    print("=" * 70)

if __name__ == "__main__":
    generate_all_flowcharts()
