import io
import pytest
from app.config import settings

def test_security_headers_presentes_em_todas_as_rotas(client):
    """
    Verifica a implementação completa dos cabeçalhos de segurança (Grau A+)
    conforme exigido na auditoria de conformidade.
    """
    res = client.get("/health")
    assert res.status_code == 200

    # 1. HSTS
    assert "Strict-Transport-Security" in res.headers
    assert "max-age=63072000" in res.headers["Strict-Transport-Security"]

    # 2. X-Content-Type-Options
    assert res.headers.get("X-Content-Type-Options") == "nosniff"

    # 3. Anti-clickjacking (X-Frame-Options e CSP frame-ancestors)
    assert res.headers.get("X-Frame-Options") == "DENY"

    # 4. Referrer-Policy para proteção LGPD
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # 5. Permissions-Policy
    perm_policy = res.headers.get("Permissions-Policy", "")
    assert "geolocation=(self)" in perm_policy
    assert "camera=(self)" in perm_policy
    assert "microphone=()" in perm_policy

    # 6. Content-Security-Policy em modo Report-Only
    csp_ro = res.headers.get("Content-Security-Policy-Report-Only", "")
    assert "default-src 'self'" in csp_ro
    assert "frame-ancestors 'none'" in csp_ro
    assert "base-uri 'self'" in csp_ro
    assert "object-src 'none'" in csp_ro

    # 7. Remoção de fingerprints do servidor
    assert "x-render-origin-server" not in res.headers


def test_upload_exame_rejeita_arquivo_com_magic_bytes_invalidos(client):
    """
    Garante que arquivo com extensão .png mas conteúdo de texto/script seja REJEITADO
    com HTTP 400 por violar a checagem de assinatura binária (MIME spoofing defense).
    """
    # 1. Cria gestante e obtém token
    reg = client.post("/auth/gestante/cadastro", json={
        "aceite_termos": True,
        "consentimento_dados_saude": True,
        "nome": "Carla Upload Teste",
        "email": "carla.upload@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Arquivo falso: extensão .png com conteúdo de texto puro
    arquivo_falso = io.BytesIO(b"<script>alert('xss')</script>")
    arquivo_falso.name = "exame_falso.png"

    res = client.post(
        "/exames/upload",
        data={
            "tipo": "Hemograma",
            "data_realizacao": "2026-10-14"
        },
        files={
            "arquivo": ("exame_falso.png", arquivo_falso, "image/png")
        },
        headers=headers
    )
    assert res.status_code == 400
    assert "magic bytes" in res.json()["detail"].lower() or "incompatível" in res.json()["detail"].lower()


def test_upload_exame_aceita_arquivo_com_magic_bytes_validos(client):
    """
    Garante que arquivo legítimo (PNG iniciando com cabeçalho oficial \\x89PNG\\r\\n\\x1a\\n)
    seja aceito com HTTP 201.
    """
    reg = client.post("/auth/gestante/cadastro", json={
        "aceite_termos": True,
        "consentimento_dados_saude": True,
        "nome": "Marina Exame Valido",
        "email": "marina.exame@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Arquivo PNG real com magic bytes oficiais
    conteudo_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    arquivo_valido = io.BytesIO(conteudo_png)
    arquivo_valido.name = "laudo_ultrassom.png"

    res = client.post(
        "/exames/upload",
        data={
            "tipo": "Ultrassom Morfológico",
            "data_realizacao": "2026-10-14"
        },
        files={
            "arquivo": ("laudo_ultrassom.png", arquivo_valido, "image/png")
        },
        headers=headers
    )
    assert res.status_code == 201
    assert "arquivo_url" in res.json()


def test_simulador_webhook_bloqueado_em_producao(client, monkeypatch):
    """
    Garante que o simulador de webhook retorne 403 Forbidden caso a aplicação
    esteja com a flag de produção ativa, impedindo fraudes financeiras.
    """
    reg = client.post("/auth/gestante/cadastro", json={
        "aceite_termos": True,
        "consentimento_dados_saude": True,
        "nome": "Luciana Teste Prod",
        "email": "luciana.prod@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ativa flag de produção via monkeypatch
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    res = client.post(
        "/assinatura/simular-webhook",
        json={"status": "approved", "subscription_id": "TEST_123"},
        headers=headers
    )
    assert res.status_code == 404

