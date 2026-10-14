"""
Testes de Ponta a Ponta: Bloco 3 - Check-in e Triagem Clínica de Urgência
========================================================================
3.4 Aceite: gestante registra check-in com sintoma de alerta, profissional vinculado
vê a contagem de alertas maior que zero e a paciente sobe na ordenação por urgência.
"""

import uuid
import pytest
from datetime import datetime, timedelta

def test_3_4_e2e_checkin_alerta_eleva_contagem_e_prioridade_no_painel_do_medico(client):
    """
    Fluxo completo de triagem obstétrica:
    1. Médico obstetra se cadastra e gera código de convite para duas gestantes (A e B).
    2. Gestante A se cadastra, vincula-se ao médico e registra check-in de rotina (sem alertas).
    3. Gestante B se cadastra, vincula-se ao médico (sem check-in inicialmente).
    4. Médico consulta painel: Gestante A precede Gestante B (tem check-in vs sem check-in, ambas 0 alertas).
    5. Gestante B registra check-in com sintoma físico de alerta grave ('Visão embaçada', 'Dor de cabeça').
    6. Médico consulta painel novamente:
       - Gestante B possui total_alertas_30d > 0.
       - Gestante B agora lidera a ordenação por urgência (posição 0), subindo na triagem.
    """
    # 1. Cadastro e login do profissional médico
    crm_num = "45678"
    prof_reg = client.post("/auth/profissional/cadastro", json={
        "nome": "Dr. Fernando Obstetra",
        "email": f"dr.fernando_{uuid.uuid4().hex[:6]}@clinica.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": crm_num,
        "registro_uf": "SP"
    })
    assert prof_reg.status_code == 201, prof_reg.text
    token_prof = prof_reg.json()["token"]
    headers_prof = {"Authorization": f"Bearer {token_prof}"}

    # 2. Médico gera dois códigos de convite
    convite_a = client.post("/vinculo/convite/gerar", headers=headers_prof).json()["codigo"]
    convite_b = client.post("/vinculo/convite/gerar", headers=headers_prof).json()["codigo"]

    # 3. Gestante A: Cadastro, Vínculo e Check-in Normal
    reg_a = client.post("/auth/gestante/cadastro", json={
        "nome": "Ana Paciente Normal",
        "email": f"ana_{uuid.uuid4().hex[:6]}@exemplo.com",
        "senha": "senhaSegura123"
    })
    token_a = reg_a.json()["token"]
    id_a = reg_a.json()["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    vinc_a = client.post("/vinculo/convite/usar", json={"codigo": convite_a}, headers=headers_a)
    assert vinc_a.status_code == 201

    # Check-in de rotina da Gestante A (sem sintomas graves de alerta)
    checkin_normal_resp = client.post("/checkin/registrar", json={
        "humor": 4,
        "descricao": "Dia calmo, sentindo apenas leve cansaço habitual.",
        "sintomas": ["Cansaço excessivo"],
        "movimentos_bebe": 8,
        "semana_gestacional": 28
    }, headers=headers_a)
    assert checkin_normal_resp.status_code == 201

    # 4. Gestante B: Cadastro e Vínculo (sem check-in inicialmente)
    reg_b = client.post("/auth/gestante/cadastro", json={
        "nome": "Beatriz Paciente Urgencia",
        "email": f"beatriz_{uuid.uuid4().hex[:6]}@exemplo.com",
        "senha": "senhaSegura123"
    })
    token_b = reg_b.json()["token"]
    id_b = reg_b.json()["id"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    vinc_b = client.post("/vinculo/convite/usar", json={"codigo": convite_b}, headers=headers_b)
    assert vinc_b.status_code == 201

    # 5. Painel inicial do médico:
    # Gestante A tem check-in e 0 alertas; Gestante B ainda não tem check-in.
    painel_inicial = client.get("/vinculo/minhas-gestantes", headers=headers_prof)
    assert painel_inicial.status_code == 200
    pacientes_iniciais = painel_inicial.json()
    assert len(pacientes_iniciais) == 2
    assert pacientes_iniciais[0]["gestante_id"] == id_a
    assert pacientes_iniciais[0]["total_alertas_30d"] == 0
    assert pacientes_iniciais[1]["gestante_id"] == id_b

    # 6. Gestante B registra check-in com sintomas clínicos de ALERTA GRAVE
    # Sintomas de alerta FEBRASGO: Visão embaçada (escotomas), Sangramento, Cefaleia intensa
    checkin_alerta_resp = client.post("/checkin/registrar", json={
        "humor": 1,
        "descricao": "Dor de cabeça súbita pulsátil muito forte, com visão embaçada e pontinhos brilhantes.",
        "sintomas": ["Dor de cabeça", "Visão embaçada"],
        "movimentos_bebe": 2,
        "semana_gestacional": 34
    }, headers=headers_b)
    assert checkin_alerta_resp.status_code == 201
    checkin_dados = checkin_alerta_resp.json()
    # Verifica que o motor clínico detectou alertas de urgência
    assert len(checkin_dados["alerta_sintoma_fisico"]) > 0

    # 7. Médico consulta o painel atualizado:
    painel_atualizado = client.get("/vinculo/minhas-gestantes", headers=headers_prof)
    assert painel_atualizado.status_code == 200
    pacientes_triagem = painel_atualizado.json()
    assert len(pacientes_triagem) == 2

    # CRITÉRIO DE ACEITE 3.4:
    # - Beatriz (Gestante B) agora é a PRIMEIRA da lista (posição 0)
    primeira_paciente = pacientes_triagem[0]
    assert primeira_paciente["gestante_id"] == id_b
    assert primeira_paciente["nome"] == "Beatriz Paciente Urgencia"
    # - Contagem de alertas maior que zero
    assert primeira_paciente["total_alertas_30d"] > 0
    assert primeira_paciente["total_alertas_30d"] >= 1

    # Ana (Gestante A) agora fica em segundo lugar (0 alertas)
    segunda_paciente = pacientes_triagem[1]
    assert segunda_paciente["gestante_id"] == id_a
    assert segunda_paciente["total_alertas_30d"] == 0
