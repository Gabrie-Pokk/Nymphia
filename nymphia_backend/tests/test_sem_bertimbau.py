"""
16/10/2026: o BERTimbau saiu (nunca rodou no servidor) e o check-in parou de
gravar a "anomalia" fixa (0,65 com urgência, 0,05 sem). O texto livre continua
classificado por palavras-chave, e o app diz isso.
"""
import uuid
from pathlib import Path

from app.models.clinical import CheckinRegistro
from app.services.ai_text_service import classify_text_emotions

APP = Path(__file__).resolve().parent.parent / "app"


def _gestante(client):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Texto", "email": f"texto_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    assert cad.status_code == 201, cad.text
    return {"Authorization": f"Bearer {cad.json()['token']}"}


def test_nenhum_codigo_do_app_carrega_torch_ou_transformers():
    for arquivo in APP.rglob("*.py"):
        texto = arquivo.read_text(encoding="utf-8")
        assert "import torch" not in texto and "from transformers" not in texto, arquivo
        assert "carregar_bertimbau" not in texto, arquivo


def test_health_diz_que_o_texto_e_classificado_por_palavras(client):
    corpo = client.get("/health").json()
    assert corpo["classificador_de_texto"] == "palavras_chave"
    assert not any("bertimbau" in chave for chave in corpo)


def test_marcas_sao_sim_ou_nao_e_nao_probabilidade():
    marcas, categorias = classify_text_emotions("Estou muito ansiosa e chorando o dia todo")
    assert set(marcas.values()) <= {0.0, 1.0}
    assert {"ansiedade", "tristeza_desanimo"} <= set(categorias)
    assert marcas["ansiedade"] == 1.0 and marcas["bem_estar"] == 0.0
    assert classify_text_emotions("xyz")[1] == ["neutro"]


def test_checkin_nao_grava_anomalia_fixa_nem_categorias_do_bertimbau(client, db_session):
    headers = _gestante(client)
    res = client.post("/checkin/registrar", headers=headers, json={
        "humor": 1, "descricao": "Estou com sangramento forte", "sintomas": [],
    })
    assert res.status_code == 201, res.text
    corpo = res.json()
    for campo in ("score_anomalia", "categorias_bertimbau", "bertimbau_disponivel"):
        assert campo not in corpo
    registro = db_session.query(CheckinRegistro).filter_by(id=corpo["id"]).first()
    assert registro.score_anomalia is None and registro.categorias_bertimbau is None
    assert registro.alerta_sintoma_fisico  # a urgência continua vindo das regras


def test_checkin_triste_recebe_a_orientacao_emocional(client):
    headers = _gestante(client)
    res = client.post("/checkin/registrar", headers=headers, json={
        "humor": 2, "descricao": "Me sinto triste e desanimada", "sintomas": [],
    })
    assert res.status_code == 201, res.text
    assert "rede de apoio" in res.json()["recomendacao"]
