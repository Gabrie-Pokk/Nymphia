# PENDÊNCIAS E DECISÕES ESTRATÉGICAS — NYMPHIA

**Fundador**: Gabriel  
**Data**: 14 de Outubro de 2026  
**Finalidade**: Registro transparente de todos os itens bloqueados por falta de decisão de produto, necessidade de infraestrutura ou preservação de dados em produção (Regras Invioláveis 2, 4 e 6).

---

## 1. SEGURANÇA E AUTENTICAÇÃO (BLOCO 1)

### 1.1. Armazenamento do Token JWT em `localStorage` no Frontend
- **O que é**: O token de autenticação JWT é gravado no `localStorage` do navegador sob a chave `nymphia_token` (`frontend/src/context/AuthContext.jsx:L21` e `frontend/src/utils/api.js:L5`).
- **Por que não foi alterado agora**: Conforme a orientação do Bloco 1.6, mudar isso abruptamente derrubaria a sessão de todas as usuárias e profissionais logados.
- **Risco Técnico**: Qualquer script malicioso executado no navegador (ataque XSS via dependência comprometida ou injeção) pode ler o `localStorage` e exfiltrar o token da gestante ou do médico.
- **Alternativa Proposta**:
  1. Migrar para cookies `HttpOnly`, `Secure`, `SameSite=Lax`. O JavaScript do navegador perde acesso de leitura direta ao token, anulando o risco de exfiltração por XSS.
  2. Implementar fluxo de `access_token` de curta duração (15 minutos) + `refresh_token` no cookie, com rota `/auth/refresh`.
  3. Proteção contra CSRF via padrão Double Submit Cookie ou cabeçalho customizado obrigatório (`X-Requested-With`).
- **O que preciso de você para destravar**: Aprovação arquitetural para alterar o transporte de autenticação do frontend e backend no próximo sprint.

---

### 1.2. Validade de 30 dias do JWT e Mecanismo de Revogação de Sessão
- **O que é**: Atualmente, o token JWT gerado tem validade estática de até 30 dias (`ACCESS_TOKEN_EXPIRE_MINUTES`) e é *stateless* — ou seja, uma vez emitido, ele é aceito pela API até expirar, mesmo que a senha seja alterada ou que a usuária clique em "Sair".
- **Por que não foi alterado agora**: Regra Inviolável 4 ("NUNCA altere o comportamento de autenticação de forma que derrube sessão de quem já está usando").
- **Proposta Segura de Revogação (Sem Derrubar Sessões Ativas)**:
  1. Adicionar uma coluna inteira `token_version` (padrão `1`) nas tabelas `gestantes`, `profissionais` e `parceiros`.
  2. Emitir os novos tokens com o claim `"tv": user.token_version`.
  3. Ao deslogar ou alterar senha, o backend incrementa `token_version += 1`.
  4. Para retrocompatibilidade: tokens antigos sem o claim `"tv"` continuam sendo aceitos até expirarem naturalmente, evitando que qualquer usuária ativa seja deslogada.
- **O que preciso de você para destravar**: Aprovação para rodar a migração que adiciona a coluna `token_version` e ativar a checagem no middleware.

---

### 1.3. Lista de Violações da CSP (Content-Security-Policy) e Conflito de Câmera
- **O que é**: A política de cabeçalhos de segurança foi configurada em modo **Report-Only** (`Content-Security-Policy-Report-Only`), conforme solicitado no Bloco 1.2.
- **Violações Mapeadas / Recursos Externos Legítimos que o Frontend Consome**:
  - `connect-src`:
    - `https://nymphia-global.onrender.com` (API Backend)
    - `https://api.qrserver.com` (Geração de QR Code SVG para o Pix do Mercado Pago)
    - `https://cdn.jsdelivr.net` (Carregamento de modelos WASM/binários do Google MediaPipe Pose)
  - `script-src`:
    - `'self'` e CDN do MediaPipe para execução do motor de visão computacional no navegador.
  - `img-src`:
    - `'self'`, `data:`, `blob:` (essencial para pré-visualização de fotos do diário visual e fotos de exames no navegador).
  - `font-src`:
    - `https://fonts.googleapis.com` e `https://fonts.gstatic.com` (tipografia Google Fonts).
- **CONFLITO CRÍTICO DE PERMISSIONS-POLICY (Câmera)**:
  - O prompt solicitou o cabeçalho: `Permissions-Policy: geolocation=(self), camera=(), microphone=()`.
  - **Atenção**: Ao definir `camera=()`, o navegador **bloqueia sumariamente o acesso à câmera** no frontend. No entanto, o módulo de Visão Corporal e Análise Biomecânica da Nymphia (`frontend/src/pages/gestante/BodyVision.jsx`) **necessita da câmera** da gestante para guiar a postura e o ângulo lombar via MediaPipe Pose.
- **O que preciso de você para destravar**:
  1. Autorizar o ajuste do cabeçalho para `Permissions-Policy: geolocation=(self), camera=(self), microphone=()`.
  2. Aprovar a lista de domínios externos legítimos acima para consolidar a CSP definitiva em modo bloqueante.

---

## 2. BANCO DE DADOS E INFRAESTRUTURA (BLOCO 2)

### 2.1. Execução do Script de Migração SQLite para PostgreSQL
- **O que é**: Foi desenvolvido o script robusto `scripts/migrar_sqlite_para_postgres.py`, que lê o banco local SQLite, resolve as chaves estrangeiras em ordem topológica e insere os dados no PostgreSQL de destino com validação de contagem de linhas e modo `--dry-run`.
- **Por que travou**: Regra Inviolável 2 ("NUNCA execute operação destrutiva... Escreva o script, deixe ele pronto, e me avise para eu rodar").
- **O que preciso de você para destravar**:
  1. Criar a instância de PostgreSQL (no Render, Supabase, Neon ou AWS).
  2. Definir a variável de ambiente `NYMPHIA_DATABASE_URL` no painel do Render.
  3. Executar o script a partir do ambiente de produção:
     ```bash
     python scripts/migrar_sqlite_para_postgres.py --sqlite nymphia.db --postgres $NYMPHIA_DATABASE_URL
     ```

---

### 2.2. Ausência de Disco Persistente no Plano Gratuito do Render
- **O que é**: O arquivo `render.yaml` (linha 13) especifica `plan: free`. A camada gratuita do Render roda sobre contêineres efêmeros. Sempre que a aplicação reinicia (inatividade de 15 minutos ou deploy de código), todo o sistema de arquivos local é apagado.
- **Risco**: Se a Nymphia permanecer em SQLite sem disco persistente, **todas as usuárias, exames e check-ins serão apagados no próximo deploy**.
- **O que preciso de você para destravar**:
  - **Opção A (Recomendada)**: Contratar o PostgreSQL gerenciado do Render ($7/mês) e migrar os dados.
  - **Opção B**: Adicionar um `disk` pago no `render.yaml` ($1/mês/GB) montado em `/var/data` e apontar o SQLite para lá.
  - Sua decisão define qual linha de infraestrutura seguir.

---

## 3. CHECK-IN HISTÓRICO E RETROCOMPATIBILIDADE (BLOCO 3)

### 3.1. Execução do Script de Retrocompatibilidade de Check-ins Antigos
- **O que é**: Foi desenvolvido o script `scripts/retrocompat_checkin_device_id.py` para mapear check-ins anônimos legados (`gestante_id` com UUID gerado no aparelho) para as contas cadastradas das gestantes.
- **Casos Ambíguos**: O script foi programado para **deixar de fora** registros onde mais de uma gestante usou o mesmo aparelho ou onde a correlação temporal for incerta, salvando a lista em `casos_ambiguos_checkin.json` para auditoria manual.
- **Por que travou**: Regra Inviolável 2 ("NUNCA execute operação destrutiva em dado de usuária... deixe pronto, e me avise para eu rodar").
- **O que preciso de você para destravar**:
  - Rodar o script em modo de homologação:
    ```bash
    python scripts/retrocompat_checkin_device_id.py --dry-run
    ```
  - Após inspecionar a saída e validar que nenhum dado será corrompido, rodar com `--executar`.

---

## 4. MODELOS CLÍNICOS E A FEATURE "SEXO" NO SIH (BLOCO 5)

### 4.1. Substituição dos Modelos de Produção sem a Feature 'SEXO'
- **O que é**: A feature `SEXO` no SIH possui variância zero (100% dos 169.213 casos da coorte obstétrica são do sexo feminino, código `3`). Os 4 modelos SIH foram retreinados sem essa feature e entregues com comparativo completo em `COMPARATIVO_SIH_SEM_SEXO.md`.
- **Por que travou**: Bloco 5.2 ("Não substitua os modelos de produção sem eu aprovar").
- **Trade-off Clínico Observado**:
  - A remoção de `SEXO` elevou a acurácia global e a precisão em todos os modelos (ex: acurácia da Eclâmpsia subiu de 83,3% para 89,9%, e o ROC-AUC do ITU subiu de 0,7815 para 0,8162).
  - Contudo, houve uma discreta redução no Recall positivo (ex: Recall da Pré-Eclâmpsia passou de 63,6% para 60,1%).
- **O que preciso de você para destravar**:
  - Decidir se aprova promover os modelos sem `SEXO` para a pasta oficial `nymphia_backend/modelos/` e atualizar `app/modelos.py`. Caso aprove, basta copiar os arquivos de `nymphia_backend/modelos_experimentais_sem_sexo/`.
