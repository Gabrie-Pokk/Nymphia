# 🌸 Nymphia — Cada batimento importa
### Plataforma de Acompanhamento Gestacional Contínuo com Inteligência Artificial

A **Nymphia** é uma plataforma e startup de Inteligência Artificial para acompanhamento gestacional contínuo conectando a gestante, o obstetra e a rede assistencial de saúde.

---

## 🚀 Tecnologias & Arquitetura

- **Frontend PWA**: React 18 + Vite, Progressive Web App instalável em celulares (Android & iOS) com Service Worker para emergência 100% offline.
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy 2.0, Pydantic V2, Bcrypt e JWT.
- **Coração de Inteligência Artificial**:
  - **Random Forest (SINASC / CNES)**: Bem-Estar Fetal e Malformação congênita.
  - **Random Forest (SIH / DataSUS)**: Pré-Eclâmpsia, Eclâmpsia, Diabetes Gestacional e Infecções Urinárias (ITU).
  - **Isolation Forest**: Detecção não-supervisionada de atipicidade clínica multivariada.
  - **BERTimbau Fine-Tuned (PT-BR)**: Extração neural de estados emocionais e sintomas físicos.
  - **Motor Determinístico FEBRASGO/MS**: Triagem imediata de sinais de alarme obstétricos.
- **Wearable Doppler**: Cinta Nymphia com simulação contínua de FHR (BCF) e sintetizador Doppler via Web Audio API.
- **Conformidade CFM & LGPD**: Resolução CFM 2.454/2026 (direito de recusa e disclaimers estatísticos), auditoria de logs e exportação de dados (Art. 18).

---

## 📱 Instalação no Celular (PWA)

1. Abra a aplicação no navegador do celular (Chrome no Android ou Safari no iOS).
2. **Android**: Toque no botão "Instalar no Celular" na barra de notificação.
3. **iOS**: Toque no ícone de compartilhamento e selecione **"Adicionar à Tela de Início"**.
4. O app roda em modo autônomo (*standalone*), com atalhos para emergência 192 e check-in diário.

---

## 💻 Execução Local

### 1. Iniciar Tudo em 1 Clique (Windows)
```powershell
.\iniciar_nymphia.ps1
```
*Detecta automaticamente o IP da sua rede Wi-Fi e disponibiliza a aplicação para o seu celular.*

### 2. Manualmente
```bash
# Backend
cd nymphia_backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

---

## ☁️ Deploy em Nuvem 24/7 (Sem PC Ligado)

A plataforma conta com configurações prontas para deploy gratuito em nuvem:
- **Render.com**: Arquivo `render.yaml` pronto para deploy do Dockerfile multi-stage.
- **Railway.app**: Arquivo `railway.toml` configurado.
- Consulte [`deploy_nuvem.md`](deploy_nuvem.md) para o passo a passo completo.

---

## 🧪 Testes & Validação E2E

```powershell
# Testes Unitários
cd nymphia_backend
.\.venv\Scripts\pytest.exe -v

# Validação E2E (32 checks ao vivo)
python verify_e2e.py
```
