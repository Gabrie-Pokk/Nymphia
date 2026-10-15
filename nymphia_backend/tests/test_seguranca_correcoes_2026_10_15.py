"""
Testes das correções de segurança de 15/10/2026.

1. Recuperação de senha: o código nunca aparece na resposta, não serve como
   sessão, vence em 30 minutos, vale uma vez e derruba as sessões antigas.
2. Tokens de sessão: o antigo token de redefinição (JWT com "tipo_acao")
   não é aceito em nenhuma rota.
3. Arquivos enviados: não existe mais pasta pública; cada arquivo só sai para
   quem tem direito.
4. Área da equipe: desligada sem token forte; token errado é recusado; toda
   decisão fica auditada.
5. Configuração de produção: segredo público ou curto impede o servidor de ligar.
6. Limite de tentativas: trocar o começo do X-Forwarded-For não escapa do limite.
"""
import re
from datetime import datetime, timedelta

import pytest

from app.config import Settings, problemas_de_configuracao_em_producao, SEGREDO_PUBLICO_DO_REPOSITORIO
from app.models.auth import AuditoriaAdmin, TokenRedefinicaoSenha
from app.security.jwt_auth import create_access_token

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _gestante(client, email="ana.seg@teste.com", senha="SenhaOriginal123!"):
    res = client.post("/auth/gestante/cadastro", json={
        "aceite_termos": True,
        "consentimento_dados_saude": True,
        "nome": "Ana Segura",
        "email": email,
        "senha": senha,
    })
    assert res.status_code == 201, res.text
    return res.json()


def _codigo_do_email(caixa):
    return re.search(r"\?redefinir=([A-Za-z0-9_\-]+)", caixa[-1][2]).group(1)


# --- 1. Recuperação de senha ---

def test_resposta_igual_para_email_existente_e_inexistente(client, emails_enviados):
    _gestante(client)
    existe = client.post("/auth/esqueci-senha", json={"email": "ana.seg@teste.com"})
    nao_existe = client.post("/auth/esqueci-senha", json={"email": "ninguem@teste.com"})
    assert existe.status_code == nao_existe.status_code == 200
    assert existe.json() == nao_existe.json()
    assert "reset_token" not in existe.json()
    assert len(emails_enviados) == 1


def test_codigo_de_redefinicao_nao_serve_como_login(client, emails_enviados):
    _gestante(client)
    client.post("/auth/esqueci-senha", json={"email": "ana.seg@teste.com"})
    codigo = _codigo_do_email(emails_enviados)
    res = client.get("/meus-dados/minhas-revisoes", headers={"Authorization": f"Bearer {codigo}"})
    assert res.status_code == 401


def test_jwt_antigo_de_redefinicao_e_recusado_como_sessao(client):
    conta = _gestante(client)
    token_antigo = create_access_token(
        {"sub": conta["id"], "perfil": "gestante", "tipo_acao": "redefinicao_senha"},
        expires_delta=timedelta(minutes=30),
    )
    res = client.get("/meus-dados/minhas-revisoes", headers={"Authorization": f"Bearer {token_antigo}"})
    assert res.status_code == 401


def test_banco_guarda_so_o_hash_do_codigo(client, db_session, emails_enviados):
    _gestante(client)
    client.post("/auth/esqueci-senha", json={"email": "ana.seg@teste.com"})
    codigo = _codigo_do_email(emails_enviados)
    registros = db_session.query(TokenRedefinicaoSenha).all()
    assert len(registros) == 1
    assert registros[0].token_hash != codigo
    assert len(registros[0].token_hash) == 64


def test_codigo_vencido_e_recusado(client, db_session, emails_enviados):
    _gestante(client)
    client.post("/auth/esqueci-senha", json={"email": "ana.seg@teste.com"})
    codigo = _codigo_do_email(emails_enviados)
    registro = db_session.query(TokenRedefinicaoSenha).first()
    registro.expira_em = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()
    res = client.post("/auth/redefinir-senha", json={"token": codigo, "nova_senha": "NovaSenha456!"})
    assert res.status_code == 400


def test_pedido_novo_invalida_o_anterior(client, emails_enviados):
    _gestante(client)
    client.post("/auth/esqueci-senha", json={"email": "ana.seg@teste.com"})
    primeiro = _codigo_do_email(emails_enviados)
    client.post("/auth/esqueci-senha", json={"email": "ana.seg@teste.com"})
    segundo = _codigo_do_email(emails_enviados)
    assert primeiro != segundo
    assert client.post("/auth/redefinir-senha", json={"token": primeiro, "nova_senha": "NovaSenha456!"}).status_code == 400
    assert client.post("/auth/redefinir-senha", json={"token": segundo, "nova_senha": "NovaSenha456!"}).status_code == 200


def test_trocar_a_senha_derruba_sessoes_antigas(client, emails_enviados):
    conta = _gestante(client)
    sessao_antiga = {"Authorization": f"Bearer {conta['token']}"}
    assert client.get("/meus-dados/minhas-revisoes", headers=sessao_antiga).status_code == 200

    client.post("/auth/esqueci-senha", json={"email": "ana.seg@teste.com"})
    codigo = _codigo_do_email(emails_enviados)
    assert client.post("/auth/redefinir-senha", json={"token": codigo, "nova_senha": "NovaSenha456!"}).status_code == 200

    assert client.get("/meus-dados/minhas-revisoes", headers=sessao_antiga).status_code == 401
    novo_login = client.post("/auth/gestante/login", json={"email": "ana.seg@teste.com", "senha": "NovaSenha456!"})
    sessao_nova = {"Authorization": f"Bearer {novo_login.json()['token']}"}
    assert client.get("/meus-dados/minhas-revisoes", headers=sessao_nova).status_code == 200


# --- 3. Arquivos enviados ---

def _enviar_exame(client, headers):
    res = client.post(
        "/exames/upload",
        data={"tipo": "Hemograma", "data_realizacao": "2026-10-01"},
        files={"arquivo": ("laudo.png", PNG_1X1, "image/png")},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    return res.json()["arquivo_url"]


def test_arquivo_de_exame_so_sai_para_quem_tem_direito(client):
    dona = _gestante(client, email="dona@teste.com")
    outra = _gestante(client, email="outra@teste.com")
    url = _enviar_exame(client, {"Authorization": f"Bearer {dona['token']}"})

    sem_login = client.get(url)
    assert sem_login.status_code == 401

    da_dona = client.get(url, headers={"Authorization": f"Bearer {dona['token']}"})
    assert da_dona.status_code == 200
    assert da_dona.content.startswith(b"\x89PNG")
    assert "no-store" in da_dona.headers.get("Cache-Control", "")

    de_outra = client.get(url, headers={"Authorization": f"Bearer {outra['token']}"})
    assert de_outra.status_code == 404


def test_nome_de_arquivo_malicioso_nao_sai_da_pasta(client):
    conta = _gestante(client)
    headers = {"Authorization": f"Bearer {conta['token']}"}
    for nome in ("nymphia.db", "x.py", "conftest.py"):
        assert client.get(f"/storage/{nome}", headers=headers).status_code == 404
    # Com "../" a rota de arquivos nem é alcançada; no máximo volta a página do app
    for caminho in ("/storage/..%2F..%2Fapp%2Fconfig.py", "/..%2F..%2Fnymphia_backend%2Fapp%2Fconfig.py"):
        res = client.get(caminho, headers=headers)
        assert b"NYMPHIA_SECRET_KEY" not in res.content
        assert b"SQLite format" not in res.content


# --- 4. Área da equipe ---

def test_area_da_equipe_desligada_sem_token_configurado(client, monkeypatch):
    monkeypatch.delenv("NYMPHIA_ADMIN_TOKEN", raising=False)
    res = client.get("/admin/profissionais", headers={"X-Admin-Token": "qualquer"})
    assert res.status_code == 503


def test_area_da_equipe_recusa_token_curto_no_servidor(client, monkeypatch):
    monkeypatch.setenv("NYMPHIA_ADMIN_TOKEN", "curto")
    assert client.get("/admin/profissionais", headers={"X-Admin-Token": "curto"}).status_code == 503


def test_area_da_equipe_recusa_token_errado(client, admin_headers):
    assert client.get("/admin/profissionais", headers={"X-Admin-Token": "errado"}).status_code == 401
    assert client.get("/admin/profissionais").status_code == 401


def test_aprovacao_fica_auditada(client, db_session, admin_headers):
    res = client.post("/auth/profissional/cadastro", json={
        "aceite_termos": True, "nome": "Dra. Auditada", "email": "auditada@clinica.com",
        "senha": "senhaSegura123", "registro_tipo": "CRM", "registro_numero": "33333", "registro_uf": "PR",
    })
    prof_id = res.json()["id"]

    pendentes = client.get("/admin/profissionais", headers=admin_headers).json()
    assert any(p["id"] == prof_id for p in pendentes)

    client.post(f"/admin/profissionais/{prof_id}/aprovar", headers=admin_headers)
    linha = db_session.query(AuditoriaAdmin).filter(AuditoriaAdmin.alvo_id == prof_id).first()
    assert linha is not None
    assert linha.acao == "aprovar_profissional"
    assert linha.feito_por == "Equipe de teste"


# --- 5. Configuração de produção ---

def test_segredo_publico_impede_producao():
    config = Settings(NYMPHIA_SECRET_KEY=SEGREDO_PUBLICO_DO_REPOSITORIO)
    assert problemas_de_configuracao_em_producao(config)


def test_segredo_curto_impede_producao():
    config = Settings(NYMPHIA_SECRET_KEY="curto-demais")
    assert problemas_de_configuracao_em_producao(config)


def test_segredo_forte_libera_producao():
    config = Settings(NYMPHIA_SECRET_KEY="x" * 64)
    assert problemas_de_configuracao_em_producao(config) == []


# --- 6. Limite de tentativas ---

def test_trocar_o_inicio_do_x_forwarded_for_nao_escapa_do_limite(client):
    codigos = []
    for i in range(12):
        res = client.post(
            "/auth/gestante/login",
            json={"email": f"tentativa_{i}@teste.com", "senha": "senhaErrada123"},
            # O cliente inventa um IP diferente a cada tentativa; o proxy acrescenta o real no fim
            headers={"X-Forwarded-For": f"10.0.0.{i}, 200.200.200.200"},
        )
        codigos.append(res.status_code)
    assert codigos[:10] == [401] * 10
    assert codigos[10:] == [429, 429]


# --- 7. Exames: nenhum valor inventado ---

def test_upload_de_exame_nao_inventa_resultado(client):
    conta = _gestante(client, email="exame.real@teste.com")
    res = client.post(
        "/exames/upload",
        data={"tipo": "Glicemia de jejum", "data_realizacao": "2026-10-01"},
        files={"arquivo": ("laudo.png", PNG_1X1, "image/png")},
        headers={"Authorization": f"Bearer {conta['token']}"},
    )
    assert res.status_code == 201
    # Antes vinha {"glicemia_jejum_mg_dl": 84.0, "status": "normal_primeiro_tri"} para qualquer laudo
    assert res.json()["valores_extraidos"] is None


# --- 8. Aprovações automáticas antigas voltam para conferência ---

def test_aprovados_automaticamente_voltam_para_pendente(db_session):
    from app.database import profissionais_para_conferencia_manual
    from app.models.auth import Profissional
    from app.security.jwt_auth import hash_password

    antigo = Profissional(
        nome="Dra. Antiga", email="antiga@clinica.com", senha_hash=hash_password("senhaSegura123"),
        registro_tipo="CRM", registro_numero="123.456", registro_uf="SP", status_verificacao="aprovado",
    )
    rejeitado = Profissional(
        nome="Dr. Rejeitado", email="rejeitado@clinica.com", senha_hash=hash_password("senhaSegura123"),
        registro_tipo="CRM", registro_numero="777777", registro_uf="RJ", status_verificacao="rejeitado",
    )
    db_session.add_all([antigo, rejeitado])
    db_session.commit()

    movidos = profissionais_para_conferencia_manual(db_session=db_session)

    assert movidos == 1
    db_session.refresh(antigo)
    db_session.refresh(rejeitado)
    assert antigo.status_verificacao == "pendente"
    assert antigo.registro_numero == "123456"
    assert rejeitado.status_verificacao == "rejeitado"


def test_area_da_equipe_tem_limite_de_pedidos(client, admin_headers):
    from app.security.rate_limiter import admin_rate_limiter
    admin_rate_limiter.reset()
    errados = {"X-Admin-Token": "chute-errado"}
    codigos = [client.get("/admin/profissionais", headers=errados).status_code for _ in range(61)]
    assert codigos[:60] == [401] * 60
    assert codigos[60] == 429
    admin_rate_limiter.reset()


def test_respostas_da_api_nao_ficam_no_cache_do_navegador(client):
    conta = _gestante(client, email="cache@teste.com")
    res = client.get("/meus-dados/minhas-revisoes", headers={"Authorization": f"Bearer {conta['token']}"})
    assert res.headers.get("Cache-Control") == "no-store"


def test_service_worker_nao_guarda_respostas_da_api():
    """
    A v1 do service worker guardava no aparelho toda resposta GET fora de /api
    (e a API da Nymphia não usa /api): histórico de check-in, perfil clínico,
    lista de pacientes. Confirmado no navegador em 15/10/2026.
    """
    from pathlib import Path
    sw = Path(__file__).resolve().parents[2] / "frontend" / "public" / "sw.js"
    if not sw.exists():
        pytest.skip("frontend não está neste checkout")
    fonte = sw.read_text(encoding="utf-8")
    assert 'const CACHE_NAME = "nymphia-pwa-v1"' not in fonte
    assert "function ehArquivoEstatico" in fonte
    assert 'request.mode !== "navigate" && !ehArquivoEstatico(url)' in fonte
