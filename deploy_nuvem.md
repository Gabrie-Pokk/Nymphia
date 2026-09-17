# Como Deixar a Nymphia no Ar 24/7 (Acesso de Qualquer Lugar sem PC Ligado)

A Nymphia foi estruturada para poder ser hospedada gratuitamente na nuvem, permitindo que você ou qualquer usuária/médico acesse a plataforma diretamente do celular pelo 4G/5G, de qualquer lugar do mundo, sem precisar manter o computador ligado.

---

## Opção 1: Deploy Gratuito no Render.com (Recomendado — 1 Clique)

O **Render** oferece hospedagem gratuita para aplicações Docker. Como a Nymphia já possui um `Dockerfile` e `render.yaml` prontos, a subida é automática:

1. **Crie uma conta gratuita**:
   - Acesse [render.com](https://render.com) e conecte com seu GitHub.

2. **Crie um repositório no seu GitHub**:
   - Suba esta pasta do projeto para o seu GitHub (ex: `https://github.com/seu-usuario/nymphia`).

3. **Inicie o serviço no Render**:
   - No painel do Render, clique em **New +** -> **Web Service**.
   - Conecte o repositório `nymphia`.
   - O Render vai detectar automaticamente o `Dockerfile` e o `render.yaml`.
   - Clique em **Create Web Service**.

4. **Pronto!**:
   - Em 3 a 5 minutos, você receberá um link público HTTPS como:
     `https://nymphia-plataforma-ia.onrender.com`
   - O frontend PWA e todos os modelos de IA estarão rodando 24 horas por dia, 7 dias por semana na nuvem!

---

## Opção 2: Deploy no Railway.app

1. Acesse [railway.app](https://railway.app).
2. Clique em **New Project** -> **Deploy from GitHub repo**.
3. Selecione o repositório da Nymphia.
4. O Railway usará o `railway.toml` e o `Dockerfile` automaticamente.
5. Em minutos você terá um domínio público `.up.railway.app` com HTTPS ativo.

---

## Como Instalar no Celular pelo Link Público

Assim que você abrir o link gerado (ex: `https://nymphia-plataforma-ia.onrender.com`):

- **No Android (Google Chrome)**:
  - Um banner aparecerá no topo: **"Instale a Nymphia no Celular"**.
  - Toque no botão dourado **Instalar**.
  - O ícone da flor de lótus aparecerá na tela inicial como um aplicativo nativo independente!

- **No iPhone / iPad (Safari)**:
  - Abra o link no Safari.
  - Toque no botão de **Compartilhar** (ícone do quadrado com a seta apontando para cima).
  - Role para baixo e selecione **"Adicionar à Tela de Início"**.
  - Toque em **Adicionar** no canto superior direito.

### Modo Offline na Emergência:
Mesmo se a gestante perder o sinal do 4G ou Wi-Fi na rua, a tela `/emergencia` funcionará instantaneamente via Service Worker com acesso ao SAMU 192 e instruções de urgência.
