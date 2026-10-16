"""
Estabilidade do servidor no plano grátis (512 MB) e configuração de produção.

Log do Render em 15/10/2026: quatro "Carregando modelos de ML" seguidos e
depois "Out of memory (used over 512Mi)". Cada /health disparava um novo
carregamento completo enquanto o primeiro ainda rodava.
"""
import threading
import time

import pytest

from app.services import ai_risk_service


@pytest.fixture
def modelos_zerados(monkeypatch):
    estado = {"carregado": False, "carregando": False, "desligados_por_memoria": [], "modelos": {},
              "atipicidade": None, "metricas": None}
    monkeypatch.setattr(ai_risk_service, "_modelos_estado", estado)
    return estado


def test_varios_pedidos_ao_mesmo_tempo_carregam_os_modelos_uma_vez(monkeypatch, modelos_zerados):
    chamadas = []

    def carregamento_lento():
        chamadas.append(1)
        time.sleep(0.3)

    monkeypatch.setattr(ai_risk_service, "_carregar_modelos_sem_trava", carregamento_lento)
    linhas = [threading.Thread(target=ai_risk_service.carregar_modelos_ml) for _ in range(8)]
    for t in linhas:
        t.start()
    for t in linhas:
        t.join()
    assert len(chamadas) == 1
    assert modelos_zerados["carregado"] is True


def test_health_nao_carrega_modelos(client, monkeypatch, modelos_zerados):
    def proibido():
        raise AssertionError("o /health não pode carregar modelos")

    monkeypatch.setattr(ai_risk_service, "_carregar_modelos_sem_trava", proibido)
    res = client.get("/health")
    assert res.status_code == 200
    assert "modelos_carregando" in res.json()


def test_health_ignora_pedido_publico_de_recarregar_ia(client, monkeypatch, modelos_zerados):
    def proibido():
        raise AssertionError("o /health não pode carregar modelos")

    monkeypatch.setattr(ai_risk_service, "_carregar_modelos_sem_trava", proibido)
    res = client.get("/health?recarregar_ia=true")
    assert res.status_code == 200
    assert not any("bertimbau" in chave for chave in res.json())


# --- Ambiente ---

def test_no_render_sem_environment_e_producao(monkeypatch):
    from app.config import ambiente_de_desenvolvimento
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("RENDER", "true")
    assert ambiente_de_desenvolvimento() is False


def test_environment_explicito_vence(monkeypatch):
    from app.config import ambiente_de_desenvolvimento
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")
    assert ambiente_de_desenvolvimento() is True
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert ambiente_de_desenvolvimento() is False


def test_local_sem_variaveis_e_desenvolvimento(monkeypatch):
    from app.config import ambiente_de_desenvolvimento
    for nome in ("ENVIRONMENT", "ENV", "RENDER"):
        monkeypatch.delenv(nome, raising=False)
    assert ambiente_de_desenvolvimento() is True


# --- Chave dos logins ---

def test_segredo_do_banco_e_forte_e_estavel():
    from app.database import obter_ou_criar_segredo
    primeiro = obter_ou_criar_segredo("teste_estabilidade")
    segundo = obter_ou_criar_segredo("teste_estabilidade")
    assert primeiro == segundo
    assert len(primeiro) >= 64


def test_producao_nunca_usa_a_chave_publica(monkeypatch):
    from app.config import settings, SEGREDO_PUBLICO_DO_REPOSITORIO
    from app.main import garantir_chave_jwt_segura
    monkeypatch.setattr(settings, "NYMPHIA_SECRET_KEY", SEGREDO_PUBLICO_DO_REPOSITORIO)
    garantir_chave_jwt_segura()
    assert settings.NYMPHIA_SECRET_KEY != SEGREDO_PUBLICO_DO_REPOSITORIO
    assert len(settings.NYMPHIA_SECRET_KEY) >= 64


def test_chave_forte_do_ambiente_e_mantida(monkeypatch):
    from app.config import settings
    from app.main import garantir_chave_jwt_segura
    forte = "k" * 80
    monkeypatch.setattr(settings, "NYMPHIA_SECRET_KEY", forte)
    garantir_chave_jwt_segura()
    assert settings.NYMPHIA_SECRET_KEY == forte


def test_link_de_redefinicao_usa_o_endereco_do_servico_no_render(monkeypatch):
    from app.api.auth import _url_publica
    monkeypatch.delenv("NYMPHIA_URL_PUBLICA", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://nymphia-global.onrender.com/")
    assert _url_publica() == "https://nymphia-global.onrender.com"


# --- Memória: o plano grátis do Render tem 512 MB e os modelos todos ocupam ~520 MB ---

@pytest.fixture
def sem_cgroup(monkeypatch, tmp_path):
    """Faz o teste não depender da máquina: o limite vem só de um arquivo falso."""
    arquivo = tmp_path / "memory.max"
    monkeypatch.setattr(ai_risk_service, "CAMINHOS_LIMITE_CGROUP", (str(arquivo),))
    for nome in ("NYMPHIA_LIMITE_MEMORIA_MB", "RENDER"):
        monkeypatch.delenv(nome, raising=False)
    return arquivo


def test_variavel_de_memoria_vence(monkeypatch, sem_cgroup):
    sem_cgroup.write_text("536870912")
    monkeypatch.setenv("NYMPHIA_LIMITE_MEMORIA_MB", "2048")
    assert ai_risk_service.limite_de_memoria_mb() == 2048


def test_limite_do_conteiner_e_lido(sem_cgroup):
    sem_cgroup.write_text("536870912")
    assert ai_risk_service.limite_de_memoria_mb() == 512


def test_render_sem_limite_visivel_assume_512(monkeypatch, sem_cgroup):
    sem_cgroup.write_text("max")
    monkeypatch.setenv("RENDER", "true")
    assert ai_risk_service.limite_de_memoria_mb() == 512


def test_fora_do_render_sem_limite_nao_inventa_limite(sem_cgroup):
    sem_cgroup.write_text("max")
    assert ai_risk_service.limite_de_memoria_mb() is None


def _carregar_com_limite(monkeypatch, limite_mb):
    import joblib
    carregados = []

    def load_falso(caminho):
        carregados.append(caminho.rsplit("/", 1)[-1])
        return {"features": ["idade"], "modelo": None}

    monkeypatch.setattr(joblib, "load", load_falso)
    monkeypatch.setattr(ai_risk_service, "limite_de_memoria_mb", lambda: limite_mb)
    ai_risk_service._carregar_modelos_sem_trava()
    return carregados


def test_modelos_v2_carregam_inteiros_mesmo_com_512_mb(monkeypatch, modelos_zerados):
    # Os modelos v2 têm menos de 1 MB cada; nenhum precisa ficar desligado
    carregados = _carregar_com_limite(monkeypatch, 512)
    for nome in ai_risk_service.NOMES_MODELOS:
        assert f"risco_{nome}.joblib" in carregados
    assert "atipicidade.joblib" in carregados
    assert modelos_zerados["desligados_por_memoria"] == []


def test_sem_modelos_nenhum_numero_e_inventado(modelos_zerados):
    modelos_zerados["carregado"] = True  # nenhum modelo ligado
    resultado = ai_risk_service.calculate_maternal_risks({"idade": 30}, [])
    assert resultado["condicoes"]
    for item in resultado["condicoes"].values():
        assert item["fonte"] == "indisponivel"
        assert item["probabilidade"] is None and item["nivel"] is None


def test_health_mostra_modelos_desligados_por_memoria(client, modelos_zerados):
    modelos_zerados["desligados_por_memoria"] = ["bem_estar_fetal", "malformacao"]
    res = client.get("/health")
    assert res.json()["modelos_desligados_por_memoria"] == ["bem_estar_fetal", "malformacao"]


# --- Coolify (Hostinger) e endereço do banco ---

def test_no_coolify_sem_environment_e_producao(monkeypatch):
    from app.config import ambiente_de_desenvolvimento
    for nome in ("ENVIRONMENT", "ENV", "RENDER"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("COOLIFY_URL", "https://app.nymphia.com.br")
    assert ambiente_de_desenvolvimento() is False


def test_link_de_redefinicao_usa_o_endereco_do_coolify(monkeypatch):
    from app.api.auth import _url_publica
    for nome in ("NYMPHIA_URL_PUBLICA", "RENDER_EXTERNAL_URL"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("COOLIFY_URL", "https://app.nymphia.com.br,https://www.nymphia.com.br")
    assert _url_publica() == "https://app.nymphia.com.br"
    monkeypatch.setenv("COOLIFY_URL", "app.nymphia.com.br")
    assert _url_publica() == "https://app.nymphia.com.br"


def test_url_publica_explicita_vence_o_coolify(monkeypatch):
    from app.api.auth import _url_publica
    monkeypatch.setenv("COOLIFY_URL", "https://abc.sslip.io")
    monkeypatch.setenv("NYMPHIA_URL_PUBLICA", "https://app.nymphia.com.br/")
    assert _url_publica() == "https://app.nymphia.com.br"


@pytest.mark.parametrize("colado", [
    "psql 'postgresql://u:p@ep-x.us-west-2.aws.neon.tech/neondb?sslmode=require'",
    "  \"postgresql://u:p@ep-x.us-west-2.aws.neon.tech/neondb?sslmode=require\"  ",
    "postgres://u:p@ep-x.us-west-2.aws.neon.tech/neondb?sslmode=require",
])
def test_endereco_do_banco_colado_de_varios_jeitos(colado):
    from app.config import limpar_endereco_do_banco
    assert limpar_endereco_do_banco(colado) == "postgresql://u:p@ep-x.us-west-2.aws.neon.tech/neondb?sslmode=require"


def test_link_de_site_no_lugar_do_banco_e_explicado_sem_mostrar_o_valor():
    from app.config import limpar_endereco_do_banco
    with pytest.raises(RuntimeError) as erro:
        limpar_endereco_do_banco("https://console.neon.tech/app/projects/segredo-123")
    assert "postgresql://" in str(erro.value)
    assert "segredo-123" not in str(erro.value)
