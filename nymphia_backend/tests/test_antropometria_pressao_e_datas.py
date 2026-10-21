"""
Antropometria, correções de 15/10/2026:
- a pressão anotada junto com o peso passou a ser avaliada (antes era ignorada);
- cada medida é avaliada na semana em que foi feita, não na de hoje;
- nada de valores inventados (peso pré-gestacional como atual, semana 24, idade 28).
"""
import uuid
from datetime import date, timedelta

import pytest

from app.services.anthropometry_service import (
    avaliar_pressao_arterial,
    avaliar_ritmo_de_ganho,
    ler_pressao_arterial,
)
from app.services.clinical_movement_service import avaliar_seguranca_movimento


def _gestante(client, semanas_dum=30, peso_pre=60.0, altura=165.0):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Antropometria", "email": f"antropo_{uuid.uuid4().hex[:8]}@teste.com",
        "senha": "senhaSegura123", "aceite_termos": True, "consentimento_dados_saude": True,
    })
    headers = {"Authorization": f"Bearer {cad.json()['token']}"}
    if semanas_dum is not None:
        dum = date.today() - timedelta(days=semanas_dum * 7)
        res = client.post("/perfil-clinico", json={
            "idade": 29, "gestacoes_anteriores": 0, "partos_normais": 0, "partos_cesareos": 0,
            "perdas_gestacionais": 0, "dum": dum.isoformat(), "dpp": (dum + timedelta(days=280)).isoformat(),
        }, headers=headers)
        assert res.status_code == 201, res.text
        if peso_pre:
            client.post("/antropometria/perfil-base", json={"altura_cm": altura, "peso_pre_gestacional": peso_pre},
                        headers=headers)
    return headers


def _pesagem(client, headers, peso, dias_atras=0, **extra):
    corpo = {"semana_gestacional": 24, "peso_atual_kg": peso,
             "data_registro": (date.today() - timedelta(days=dias_atras)).isoformat(), **extra}
    return client.post("/antropometria/registro", json=corpo, headers=headers)


# --- Pressão ---

@pytest.mark.parametrize("texto,esperado", [
    ("120/80", (120, 80)), ("140x90", (140, 90)), ("12 por 8", (120, 80)), ("15/10", (150, 100)),
    ("160/110 mmHg", (160, 110)), ("80/120", None), ("pressão boa", None), ("", None),
])
def test_leitura_da_pressao(texto, esperado):
    assert ler_pressao_arterial(texto) == esperado


def test_cortes_da_pressao():
    assert avaliar_pressao_arterial("118/76")["nivel"] == "nenhum"
    assert avaliar_pressao_arterial("140/85")["nivel"] == "urgente"
    assert avaliar_pressao_arterial("130/90")["nivel"] == "urgente"
    muito_alta = avaliar_pressao_arterial("16 por 11")
    assert muito_alta["nivel"] == "urgente" and "agora" in muito_alta["orientacao"]


def test_pesagem_com_pressao_160_110_avisa_na_hora(client):
    headers = _gestante(client, semanas_dum=30)
    res = _pesagem(client, headers, 70.0, pressao_arterial="160/110")
    assert res.status_code == 201, res.text
    alertas = res.json()["alertas"]
    assert alertas and alertas[0]["tipo"] == "pressao" and alertas[0]["nivel"] == "urgente"


def test_painel_mostra_a_pressao_alta(client):
    headers = _gestante(client, semanas_dum=30)
    _pesagem(client, headers, 70.0, pressao_arterial="150/95")
    painel = client.get("/antropometria/painel", headers=headers).json()
    assert painel["alertas"][0]["tipo"] == "pressao"
    assert painel["alertas"][0]["nivel"] == "urgente"


def test_pressao_alta_antiga_vira_aviso_para_medir_de_novo(client):
    headers = _gestante(client, semanas_dum=30)
    _pesagem(client, headers, 70.0, dias_atras=10, pressao_arterial="150/95")
    alerta = client.get("/antropometria/painel", headers=headers).json()["alertas"][0]
    assert alerta["nivel"] == "atencao"
    assert "Meça de novo" in alerta["orientacao"]


def test_pressao_ilegivel_e_recusada(client):
    headers = _gestante(client, semanas_dum=30)
    res = _pesagem(client, headers, 70.0, pressao_arterial="mais ou menos boa")
    assert res.status_code == 422
    assert "120/80" in res.json()["detail"]


def test_pressao_em_cmhg_e_guardada_em_mmhg(client):
    headers = _gestante(client, semanas_dum=30)
    res = _pesagem(client, headers, 70.0, pressao_arterial="12 por 8")
    assert res.json()["pressao_arterial"] == "120/80"
    assert res.json()["alertas"] == []


# --- Datas e semanas ---

def test_semana_da_pesagem_vem_da_dum(client):
    # A tela sugeria 24 semanas; com DUM de 30 semanas atrás, vale 30
    headers = _gestante(client, semanas_dum=30)
    res = _pesagem(client, headers, 70.0)
    assert res.json()["semana_gestacional"] == 30


def test_pesagem_antiga_e_avaliada_na_propria_semana(client):
    headers = _gestante(client, semanas_dum=30)
    _pesagem(client, headers, 63.0, dias_atras=8 * 7)  # feita com 22 semanas
    avaliacao = client.get("/antropometria/painel", headers=headers).json()["avaliacao_ganho_ufrj"]
    assert avaliacao["semana"] == 22
    # 3 kg com 22 semanas, eutrófica: dentro da faixa (antes ia para "abaixo" ao comparar com a 30ª)
    assert avaliacao["status"] == "ADEQUADO"


def test_sem_pesagem_nao_ha_avaliacao_inventada(client):
    headers = _gestante(client, semanas_dum=20)
    painel = client.get("/antropometria/painel", headers=headers).json()
    assert painel["peso_atual_kg"] is None
    assert painel["avaliacao_ganho_ufrj"] is None
    assert painel["ganho_peso_acumulado_kg"] is None


def test_sem_dum_e_sem_pesagem_a_semana_fica_em_branco(client):
    headers = _gestante(client, semanas_dum=None)
    painel = client.get("/antropometria/painel", headers=headers).json()
    assert painel["semana_gestacional_atual"] is None


def test_data_no_futuro_e_recusada(client):
    headers = _gestante(client, semanas_dum=30)
    res = _pesagem(client, headers, 70.0, dias_atras=-3)
    assert res.status_code == 422


def test_data_antes_da_dum_e_recusada(client):
    headers = _gestante(client, semanas_dum=10)
    res = _pesagem(client, headers, 70.0, dias_atras=12 * 7)
    assert res.status_code == 422


# --- Ganho rápido ---

def test_ganho_rapido_pelo_ritmo_semanal():
    hoje = date.today()
    alerta = avaliar_ritmo_de_ganho(72.5, hoje, 70.0, hoje - timedelta(days=14), semana=30)
    assert alerta and alerta["tipo"] == "ganho_rapido"
    # A regra antiga (1 kg em até 10 dias) continua valendo
    assert avaliar_ritmo_de_ganho(71.0, hoje, 70.0, hoje - timedelta(days=9), semana=30)
    # Ganho normal ou antes de 20 semanas: sem aviso
    assert avaliar_ritmo_de_ganho(70.6, hoje, 70.0, hoje - timedelta(days=14), semana=30) is None
    assert avaliar_ritmo_de_ganho(72.5, hoje, 70.0, hoje - timedelta(days=14), semana=16) is None


def test_painel_traz_curva_e_pontos_para_o_grafico(client):
    headers = _gestante(client, semanas_dum=30)
    _pesagem(client, headers, 64.0, dias_atras=6 * 7)
    _pesagem(client, headers, 66.0)
    painel = client.get("/antropometria/painel", headers=headers).json()
    assert len(painel["curva_ganho_recomendada"]) == 41
    assert [p["semana"] for p in painel["pontos_ganho"]] == [24, 30]
    assert painel["pontos_ganho"][-1]["ganho_kg"] == 6.0


# --- Movimento sem semana conhecida ---

def test_movimento_sem_semana_aplica_todas_as_cautelas():
    resultado = avaliar_seguranca_movimento("disposta", [], [], semana_gestacional=None)
    assert any("barriga para cima" in p for p in resultado["exercicios_proibidos"])
    assert "None" not in resultado["mensagem_ia"]


def test_movimento_traz_os_sinais_para_parar_da_diretriz():
    resultado = avaliar_seguranca_movimento("disposta", [], [], semana_gestacional=12)
    texto = " ".join(resultado["orientacoes_especificas"])
    assert "sangramento vaginal" in texto and "contrações regulares" in texto
    # Antes da metade da gestação a orientação de não ficar de costas não se aplica
    assert not any("barriga para cima" in p for p in resultado["exercicios_proibidos"])
    tudo = str(resultado)
    assert "placenta" not in tudo and "IA" not in resultado["mensagem_ia"]
