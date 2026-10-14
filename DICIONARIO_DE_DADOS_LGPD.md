# DICIONARIO_DE_DADOS_LGPD.md — Dicionário de Dados e Classificação de Privacidade (LGPD)

> **Plataforma Nymphia — Saúde Materno-Infantil**  
> **Conformidade Legal**: Lei Geral de Proteção de Dados Pessoais (Lei Federal nº 13.709/2018 — LGPD), Resolução CFM nº 2.454/2026 (Inteligência Artificial na Medicina) e Resoluções CFM nº 1.821/2007 e 2.299/2021 (Prontuário e Telemedicina).

---

## 1. Enquadramento e Critérios de Classificação da LGPD

Conforme o **Artigo 5º da Lei nº 13.709/2018 (LGPD)**, as colunas do banco de dados da Nymphia são classificadas em três categorias jurídicas rigorosas:

1. **Dado Pessoal Sensível (Art. 5º, II da LGPD)**:
   - Dados referentes à **saúde**, histórico obstétrico, sinais vitais, glicemia, pressão arterial, medicamentos, exames laboratoriais, ecografias, sintomas, biometria postural e vida reprodutiva/sexual.
   - **Regime Jurídico**: Tratamento fundamentado no **Art. 11, I** (consentimento específico e destacado da gestante) e **Art. 11, II, alínea "f"** (tutela da saúde, exclusivamente por profissionais de saúde e serviços de saúde) e **alínea "e"** (proteção da vida ou da incolumidade física da gestante e do feto).
2. **Dado Pessoal Comum (Art. 5º, I da LGPD)**:
   - Informações que identificam ou tornam identificável a pessoa natural (nome, e-mail, telefone, CRM/COREN, credenciais de acesso e perfil).
   - **Regime Jurídico**: Fundamentado no **Art. 7º, I** (consentimento), **Art. 7º, V** (execução de contrato/termos de uso) e **Art. 7º, II** (cumprimento de obrigação legal/regulatória).
3. **Dado Operacional / Metadado Técnico / Auditoria**:
   - Identificadores de sistema (UUIDs), chaves estrangeiras, timestamps de auditoria, logs de acesso exigidos pelo Art. 16 do Marco Civil da Internet e status de moderação. Não identificam diretamente o indivíduo sem correlação.

---

## 2. Catálogo Estruturado das Tabelas e Colunas

### 2.1. `gestantes` (Titulares Principais)
Registros cadastrais e controle de consentimento das gestantes.

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) [PK] | Identificador universal único (UUID) da gestante | Metadado Técnico | Art. 7º, V (Contrato) |
| `nome` | VARCHAR(255) | Nome completo civil da gestante | **Dado Pessoal Comum** | Art. 7º, V (Contrato) |
| `email` | VARCHAR(255) | Endereço eletrônico para login e comunicações | **Dado Pessoal Comum** | Art. 7º, V (Contrato) |
| `senha_hash` | VARCHAR(255) | Hash criptográfico bcrypt da senha da usuária | Dado Operacional Seguro | Art. 7º, V / Art. 46 (Segurança) |
| `recusa_ia` | BOOLEAN | Opção de opt-out da análise automatizada por IA | Metadado de Consentimento | Art. 11, I / Art. 20 (Revisão Humana) |
| `termos_aceitos_em` | DATETIME | Data e hora do aceite dos Termos de Uso | Metadado de Governança | Art. 7º, I / Art. 8º (Prova de Consentimento) |
| `termos_versao` | VARCHAR(20) | Versão dos termos aceitos (ex: "1.0-2026") | Metadado de Governança | Art. 8º, § 6º (Transparência) |
| `consentimento_dados_saude` | BOOLEAN | Aceite específico e destacado para dados de saúde | Metadado de Consentimento | Art. 11, I (Consentimento Específico) |
| `consentimento_dados_saude_em`| DATETIME | Data e hora do consentimento específico | Metadado de Governança | Art. 11, I (Prova de Consentimento) |
| `criado_em` | DATETIME | Timestamp de criação da conta | Metadado Técnico | Art. 7º, V (Contrato) |

---

### 2.2. `perfis_clinicos` (Prontuário Obstétrico Base)
Dados antropométricos, histórico reprodutivo e maternidade de referência.

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER [PK] | Identificador sequencial do perfil | Metadado Técnico | Art. 11, II, "f" (Saúde) |
| `gestante_id` | VARCHAR(36) [FK] | Referência à gestante titular | Metadado Técnico | Art. 11, II, "f" (Saúde) |
| `idade` | INTEGER | Idade cronológica materna em anos | **Dado Pessoal Comum** | Art. 11, I e II, "f" |
| `estado_civil` | VARCHAR(50) | Estado civil declarado | **Dado Pessoal Comum** | Art. 7º, I (Consentimento) |
| `escolaridade` | VARCHAR(50) | Grau de instrução formal | **Dado Pessoal Comum** | Art. 7º, I (Consentimento) |
| `gestacoes_anteriores` | INTEGER | Número total de gestações prévias (G) | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `partos_normais` | INTEGER | Histórico de partos vaginais prévios (P) | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `partos_cesareos` | INTEGER | Histórico de cesarianas anteriores (C) | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `perdas_gestacionais` | INTEGER | Histórico de abortos ou óbitos fetais (A) | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `dum` | DATE | Data da Última Menstruação | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `dpp` | DATE | Data Provável do Parto calculada por Naegele | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `dpp_editada_manualmente` | BOOLEAN | Sinalizador de ajuste médico da idade gestacional | Metadado Clínico | Art. 11, II, "f" (Tutela da Saúde) |
| `altura_cm` | FLOAT | Estatura materna em centímetros | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `peso_pre_gestacional` | FLOAT | Peso prévio à gravidez em quilogramas (IMC) | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "f" (Tutela da Saúde) |
| `maternidade_nome` | VARCHAR(255) | Hospital/maternidade de referência para o parto | Dado Assistencial | Art. 11, II, "e" (Proteção da Vida) |
| `maternidade_endereco` | VARCHAR(255) | Endereço físico da maternidade de referência | Dado Assistencial | Art. 11, II, "e" (Proteção da Vida) |
| `maternidade_telefone` | VARCHAR(50) | Telefone de contato de emergência do hospital | Dado Assistencial | Art. 11, II, "e" (Proteção da Vida) |
| `maternidade_latitude` | FLOAT | Coordenada geográfica da maternidade | Dado Geoespacial | Art. 11, II, "e" (Proteção da Vida) |
| `maternidade_longitude` | FLOAT | Coordenada geográfica da maternidade | Dado Geoespacial | Art. 11, II, "e" (Proteção da Vida) |
| `atualizado_em` | DATETIME | Data e hora da última revisão clínica | Metadado de Auditoria | Art. 11, II, "f" |

---

### 2.3. `checkins` (Triagem Diária e Sinais de Alerta)
Registros diários de sintomas, bem-estar e vitalidade materna.

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER [PK] | Identificador sequencial do check-in | Metadado Técnico | Art. 11, II, "e" (Proteção da Vida) |
| `gestante_id` | VARCHAR(36) [FK] | Referência à conta autenticada da gestante | Metadado Técnico | Art. 11, II, "e" (Proteção da Vida) |
| `data_hora` | DATETIME | Data e hora do registro | Metadado Clínico | Art. 11, II, "e" (Proteção da Vida) |
| `humor` | VARCHAR(50) | Estado emocional auto-relatado | **Dado Pessoal Sensível (Saúde Mental)** | Art. 11, I e II, "f" |
| `sintomas` | TEXT | Sintomas informados pela paciente (JSON) | **Dado Pessoal Sensível (Saúde)** | Art. 11, I e II, "e" (Proteção da Vida) |
| `movimentacao_fetal` | VARCHAR(50) | Percepção materna de movimentos do bebê | **Dado Pessoal Sensível (Saúde Fetal)** | Art. 11, I e II, "e" (Proteção da Vida) |
| `horas_sono` | FLOAT | Duração do sono relatada | **Dado Pessoal Sensível (Saúde)** | Art. 11, I (Consentimento) |
| `copos_agua` | INTEGER | Hidratação diária estimada | Dado de Estilo de Vida | Art. 11, I (Consentimento) |
| `texto_livre` | TEXT | Relato subjetivo da gestante | **Dado Pessoal Sensível (Saúde)** | Art. 11, I (Consentimento) |
| `nivel_urgencia` | VARCHAR(20) | Triagem algorítmica ('verde', 'amarelo', 'vermelho')| **Dado Pessoal Sensível (Risco Clínico)** | Art. 11, II, "e" e "f" |
| `alertas_gerados` | TEXT | Lista estruturada de alertas disparados | **Dado Pessoal Sensível (Alerta Médico)** | Art. 11, II, "e" (Proteção da Vida) |
| `dados_sinais_vitais` | TEXT | Leituras de PA/Glicemia vinculadas (JSON) | **Dado Pessoal Sensível (Sinais Vitais)**| Art. 11, I e II, "e" |

---

### 2.4. `medicoes_dispositivo` (Telemetria IoT Homologada)
Leituras captadas por aparelhos Bluetooth SIG ou inseridas manualmente.

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER [PK] | Identificador da medição | Metadado Técnico | Art. 11, II, "f" |
| `gestante_id` | VARCHAR(36) [FK] | Referência à gestante titular | Metadado Técnico | Art. 11, II, "f" |
| `tipo` | VARCHAR(50) | Categoria ('pressao_arterial', 'glicemia') | Metadado Clínico | Art. 11, II, "f" |
| `sistolica` | INTEGER | Pressão arterial sistólica em mmHg | **Dado Pessoal Sensível (Saúde / Biomarcador)** | Art. 11, II, "e" (Proteção da Vida) |
| `diastolica` | INTEGER | Pressão arterial diastólica em mmHg | **Dado Pessoal Sensível (Saúde / Biomarcador)** | Art. 11, II, "e" (Proteção da Vida) |
| `glicemia` | FLOAT | Nível de glicemia capilar em mg/dL | **Dado Pessoal Sensível (Saúde / Biomarcador)** | Art. 11, II, "e" (Proteção da Vida) |
| `data_hora` | DATETIME | Data e hora exata da aferição | Metadado Clínico | Art. 11, II, "f" |
| `origem` | VARCHAR(50) | Método de coleta ('bluetooth_sig', 'manual')| Metadado de Rastreabilidade | Art. 11, II, "f" |

---

### 2.5. `eventos_emergencia` (Acionamento SAMU 192 e Alertas Paralelos)
Trilha crítica de acionamento de socorro obstétrico.

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER [PK] | Identificador do evento de emergência | Metadado Técnico | Art. 11, II, "e" (Proteção da Vida) |
| `gestante_id` | VARCHAR(36) [FK] | Identificador da gestante ou 'anonima_publica' | Metadado Assistencial | Art. 11, II, "e" (Proteção da Vida) |
| `data_hora` | DATETIME | Timestamp do servidor no momento do disparo | Metadado Crítico | Art. 11, II, "e" (Proteção da Vida) |
| `latitude` | FLOAT | Coordenada GPS de latitude para socorro | **Dado Geoespacial Sensível** | Art. 11, II, "e" (Proteção da Vida) |
| `longitude` | FLOAT | Coordenada GPS de longitude para socorro | **Dado Geoespacial Sensível** | Art. 11, II, "e" (Proteção da Vida) |
| `contexto` | JSON | Dados clínicos resumidos anexados ao alerta | **Dado Pessoal Sensível (Saúde)** | Art. 11, II, "e" (Proteção da Vida) |
| `profissional_notificado` | BOOLEAN | Confirmação de envio do alerta ao obstetra | Metadado Operacional | Art. 11, II, "e" (Proteção da Vida) |

---

### 2.6. `exames` e `integracoes_laboratoriais` (Exames e Interoperabilidade FHIR)
Laudos, ultrassonografias e mensagens estruturadas HL7/FHIR.

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `exames.id` | INTEGER [PK] | Identificador do exame | Metadado Técnico | Art. 11, II, "f" (Tutela da Saúde) |
| `exames.tipo` | VARCHAR(100) | Tipo de exame ('ultrassom_morfologico', etc.)| Metadado Clínico | Art. 11, II, "f" (Tutela da Saúde) |
| `exames.data_exame` | DATE | Data de realização do procedimento | Metadado Clínico | Art. 11, II, "f" (Tutela da Saúde) |
| `exames.resultado_resumo` | TEXT | Conclusão ecográfica ou laudo estruturado | **Dado Pessoal Sensível (Saúde)** | Art. 11, II, "f" (Tutela da Saúde) |
| `exames.arquivo_path` | VARCHAR(500) | Caminho seguro do PDF/imagem no storage | Metadado de Armazenamento | Art. 11, II, "f" / Art. 46 (Segurança) |
| `integracoes_laboratoriais.conteudo_fhir` | JSON | Mensagem estruturada FHIR com exames | **Dado Pessoal Sensível (Saúde)** | Art. 11, II, "f" (Interoperabilidade SUS) |

---

### 2.7. `mensagens` (Conversas com a Assistente IA Clínica)
Interações conversacionais e triagem de sintomas por Processamento de Linguagem Natural.

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER [PK] | Identificador da mensagem | Metadado Técnico | Art. 11, I (Consentimento) |
| `gestante_id` | VARCHAR(36) [FK] | Referência à titular da conversa | Metadado Técnico | Art. 11, I (Consentimento) |
| `papel` | VARCHAR(20) | Remetente ('usuario' ou 'assistente') | Metadado Técnico | Art. 11, I (Consentimento) |
| `conteudo` | TEXT | Texto da mensagem da gestante ou resposta da IA | **Dado Pessoal Sensível (Saúde e Queixas)**| Art. 11, I e II, "f" |
| `alerta_emergencia` | BOOLEAN | Sinalizador de menção a sintomas críticos | Metadado de Risco | Art. 11, II, "e" (Proteção da Vida) |
| `autorizado_compartilhar` | BOOLEAN | Consentimento específico para envio ao médico | Metadado de Compartilhamento | Art. 11, I / Art. 7º, § 5º (Compartilhamento) |

---

### 2.8. `profissionais` (Corpo Clínico Assistente)
Cadastro médico e validação de registro em conselho de classe (CRM/COREN).

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) [PK] | Identificador único do profissional | Metadado Técnico | Art. 7º, V (Contrato) |
| `nome` | VARCHAR(255) | Nome profissional do médico/enfermeiro | **Dado Pessoal Comum** | Art. 7º, V / Art. 7º, II (Obrigação Legal) |
| `email` | VARCHAR(255) | E-mail corporativo ou profissional | **Dado Pessoal Comum** | Art. 7º, V (Contrato) |
| `registro_tipo` | VARCHAR(10) | Conselho profissional ('CRM', 'COREN') | **Dado Pessoal Comum** | Art. 7º, II (Res. CFM 2.454/2026) |
| `registro_numero` | VARCHAR(50) | Número de inscrição no conselho de classe | **Dado Pessoal Comum** | Art. 7º, II (Fiscalização Profissional) |
| `registro_uf` | VARCHAR(2) | Unidade Federativa do conselho emissor | **Dado Pessoal Comum** | Art. 7º, II (Fiscalização Profissional) |
| `documento_comprovante_path` | VARCHAR(500) | Upload de cédula de identidade profissional | Dado Cadastral Restrito | Art. 7º, II (Validação de Identidade) |
| `status_verificacao` | VARCHAR(20) | Status ('pendente', 'aprovado', 'rejeitado')| Metadado de Compliance | Art. 7º, II (Conformidade CFM) |

---

### 2.9. `logs_acesso` e `solicitacoes_revisao_ia` (Auditoria e Direitos do Titular)
Trilha imutável de acessos ao prontuário e pedidos de revisão humana de IA (Art. 20 LGPD).

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `logs_acesso.acessado_por_id` | VARCHAR(36) | ID de quem consultou a ficha da gestante | Metadado de Auditoria | Art. 18, IV / Art. 16 Marco Civil |
| `logs_acesso.recurso` | VARCHAR(100) | Tela ou dado acessado ('ficha_paciente', etc.) | Metadado de Auditoria | Art. 18, IV / Art. 16 Marco Civil |
| `logs_acesso.data_hora` | DATETIME | Momento exato da consulta | Metadado de Auditoria | Art. 18, IV / Art. 16 Marco Civil |
| `solicitacoes_revisao_ia.motivo` | TEXT | Justificativa da gestante solicitando revisão humana | **Direito do Titular (Art. 20 LGPD)** | Art. 20 da LGPD (Revisão de Decisões Automatizadas) |
| `solicitacoes_revisao_ia.resposta_revisao`| TEXT | Parecer emitido pelo profissional humano | Metadado de Compliance | Art. 20, § 1º da LGPD |

---

### 2.10. `assinaturas` e `transacoes_pagamento` (Cobrança e Mercado Pago)
Gestão financeira sem armazenamento de dados de cartão de crédito (PCI-DSS).

| Coluna | Tipo SQL | Significado Funcional | Classificação LGPD | Base Legal Principal |
| :--- | :--- | :--- | :--- | :--- |
| `assinaturas.plano` | VARCHAR(50) | Plano contratado ('free', 'premium', etc.) | Dado Contratual | Art. 7º, V (Execução de Contrato) |
| `assinaturas.status` | VARCHAR(20) | Status ('ativa', 'pendente', 'inadimplente') | Dado Contratual | Art. 7º, V (Execução de Contrato) |
| `transacoes_pagamento.mercado_pago_payment_id` | VARCHAR(100) | ID externo de pagamento no Mercado Pago | Metadado Financeiro | Art. 7º, V e II (Fiscal/Tributário) |
| `transacoes_pagamento.valor` | FLOAT | Quantia faturada em reais (BRL) | Metadado Financeiro | Art. 7º, V e II (Fiscal/Tributário) |

---

## 3. Matriz de Direitos dos Titulares (Artigo 18 da LGPD)

| Direito do Titular | Endpoint / Recurso no Sistema | Status de Implementação |
| :--- | :--- | :--- |
| **Confirmação e Acesso** | `GET /meus-dados/resumo` | Implementado |
| **Portabilidade em Formato Estruturado** | `GET /meus-dados/exportar?formato=json` | Implementado (JSON interoperável) |
| **Relatório Legível de Prontuário** | `GET /meus-dados/exportar?formato=pdf` | Implementado (PDF auditado) |
| **Trilha de Acessos de Terceiros** | `GET /meus-dados/logs-acesso` | Implementado (Audit log consultável pela gestante) |
| **Revisão de Decisões Automatizadas (IA)** | `POST /meus-dados/solicitar-revisao-ia` | Implementado (Garante revisão humana sob Art. 20) |
| **Revogação do Consentimento / Anonimização** | `POST /meus-dados/anonimizar` | Implementado (com guarda obrigatória de prontuário por 20 anos sob Lei 13.787/2018) |

---

## 4. Medidas Técnicas e Organizacionais de Segurança da Informação (Art. 46 LGPD)

1. **Criptografia em Repouso e em Trânsito**: Todas as transmissões utilizam TLS 1.3 obrigatório com HSTS (`Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`). Senhas armazenadas com salt dinâmico e hash bcrypt.
2. **Separação Lógica de Papéis (RBAC)**: O perfil `parceiro` nunca tem acesso a laudos de exames sem permissão explícita da gestante; o perfil `profissional` só acessa pacientes mediante autorização de vínculo ativo (`Vinculo.status == 'ativo'`).
3. **Imunidade da Rota de Emergência**: Conforme a **Regra 3 e Art. 11, II, "e" da LGPD**, nenhum mecanismo de cobrança, bloqueio de conta ou checagem de plano pode intervir ou recusar o envio de alerta de emergência médica ao SAMU 192.
