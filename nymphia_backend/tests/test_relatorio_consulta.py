"""
Relatório para a consulta (18/10/2026): PDF gerado no prontuário pela
profissional vinculada. Regras em app/services/relatorio_consulta_service.py.
"""
import random
import uuid
from datetime import date, datetime, timedelta

from app.models.auth import Gestante, Profissional
from app.models.clinical import CheckinRegistro, PerfilClinico, RegistroAntropometrico, TriagemEPDS
from app.models.governance import ObservacaoProfissional
from app.models.interaction import EventoAgenda, EventoEmergencia, Mensagem
from app.models.relations import LogAcesso
from app.services.relatorio_consulta_service import gerar_pdf, montar_relatorio


def _profissional(client, aprovar_profissional, nome="Dra. Relatório"):
    prof = client.post("/auth/profissional/cadastro", json={
        "aceite_termos": True, "nome": nome, "email": f"rel_{uuid.uuid4().hex[:8]}@clinica.com",
        "senha": "senhaSegura123", "registro_tipo": "CRM", "registro_numero": str(random.randint(100000, 999999)),
        "registro_uf": "SP",
    })
    assert prof.status_code == 201, prof.text
    aprovar_profissional(prof.json()["id"])
    return prof.json()["id"], {"Authorization": f"Bearer {prof.json()['token']}"}


def _gestante_vinculada(client, aprovar_profissional):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Relatório", "email": f"rel_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    assert cad.status_code == 201, cad.text
    headers = {"Authorization": f"Bearer {cad.json()['token']}"}
    prof_id, headers_prof = _profissional(client, aprovar_profissional)
    codigo = client.post("/vinculo/convite/gerar", headers=headers_prof).json()["codigo"]
    assert client.post("/vinculo/convite/usar", json={"codigo": codigo}, headers=headers).status_code == 201
    dum = date.today() - timedelta(days=30 * 7)
    perfil = client.post("/perfil-clinico", headers=headers, json={
        "idade": 31, "gestacoes_anteriores": 1, "partos_normais": 1, "partos_cesareos": 0, "perdas_gestacionais": 0,
        "dum": dum.isoformat(), "dpp": (dum + timedelta(days=280)).isoformat(),
    })
    assert perfil.status_code == 201, perfil.text
    return cad.json()["id"], headers, prof_id, headers_prof


def test_profissional_vinculada_baixa_o_pdf_e_o_acesso_fica_registrado(client, aprovar_profissional, db_session):
    gestante_id, headers, prof_id, headers_prof = _gestante_vinculada(client, aprovar_profissional)
    assert client.post("/checkin/registrar", headers=headers,
                       json={"humor": 2, "descricao": "Dor de cabeça forte desde ontem", "sintomas": []}).status_code == 201

    res = client.get(f"/vinculo/paciente/{gestante_id}/relatorio-consulta", headers=headers_prof)

    assert res.status_code == 200, res.text
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")
    disposicao = res.headers["content-disposition"]
    assert disposicao.startswith('attachment; filename="relatorio-consulta-')
    assert "Gestante" not in disposicao  # o nome dela não vai no nome do arquivo
    assert res.headers["cache-control"] == "no-store"
    log = db_session.query(LogAcesso).filter(LogAcesso.gestante_id == gestante_id,
                                             LogAcesso.recurso == "relatorio_consulta_pdf").all()
    assert len(log) == 1 and log[0].acessado_por_id == prof_id


def test_sem_vinculo_ativo_nao_baixa(client, aprovar_profissional):
    gestante_id, headers, _, _ = _gestante_vinculada(client, aprovar_profissional)
    _, headers_outra = _profissional(client, aprovar_profissional, nome="Dra. Sem Vínculo")

    assert client.get(f"/vinculo/paciente/{gestante_id}/relatorio-consulta", headers=headers_outra).status_code == 403
    assert client.get(f"/vinculo/paciente/{gestante_id}/relatorio-consulta", headers=headers).status_code in (401, 403)
    assert client.get(f"/vinculo/paciente/{gestante_id}/relatorio-consulta").status_code in (401, 403)


def test_pontos_de_atencao_trazem_os_fatos_do_periodo(client, aprovar_profissional, db_session):
    gestante_id, _, prof_id, _ = _gestante_vinculada(client, aprovar_profissional)
    prof = db_session.query(Profissional).filter(Profissional.id == prof_id).first()
    agora = datetime(2026, 10, 18, 21, 0)  # 18h em Brasília

    # Consulta 12 dias antes: o período começa nela
    db_session.add(EventoAgenda(gestante_id=gestante_id, tipo="consulta", titulo="Pré-natal",
                                data_hora=agora - timedelta(days=12)))
    db_session.add(EventoAgenda(gestante_id=gestante_id, tipo="exame", titulo="Glicemia de jejum",
                                data_hora=agora - timedelta(days=3), concluido=False))
    db_session.add(EventoAgenda(gestante_id=gestante_id, tipo="consulta", titulo="Retorno",
                                data_hora=agora + timedelta(days=2)))
    # Check-in antes da consulta: fica de fora
    db_session.add(CheckinRegistro(gestante_id=gestante_id, data_hora=agora - timedelta(days=20), humor=5,
                                   sintomas=[], alerta_sintoma_fisico=["Febre"], sinais_atencao=[]))
    for dias in (5, 4):
        db_session.add(CheckinRegistro(gestante_id=gestante_id, data_hora=agora - timedelta(days=dias), humor=2,
                                       sintomas=["Dor de cabeça"], descricao="Muita dor de cabeça",
                                       alerta_sintoma_fisico=["Dor de cabeça forte ou que não passa"],
                                       sinais_atencao=[], categorias_regras=[]))
    db_session.add(TriagemEPDS(gestante_id=gestante_id, data_hora=agora - timedelta(days=2), respostas=[1] * 10,
                               pontos_por_item=[1] * 10, pontuacao=12, pontos_autolesao=0, nivel="atencao"))
    db_session.add(EventoEmergencia(gestante_id=gestante_id, data_hora=agora - timedelta(days=1),
                                    contexto={}, profissional_notificado=False))
    db_session.add(RegistroAntropometrico(gestante_id=gestante_id, data_registro=(agora - timedelta(days=6)).date(),
                                          semana_gestacional=29, peso_atual_kg=64.0, pressao_arterial="120/80"))
    db_session.add(RegistroAntropometrico(gestante_id=gestante_id, data_registro=(agora - timedelta(days=1)).date(),
                                          semana_gestacional=30, peso_atual_kg=65.5, pressao_arterial="145/95"))
    db_session.commit()

    dados = montar_relatorio(db_session, gestante_id, prof, agora)
    pontos = " | ".join(dados["pontos"])

    assert dados["inicio"] == agora - timedelta(days=12)
    assert "em 06/10/2026" in dados["origem_periodo"]
    assert len(dados["checkins"]) == 2  # o de 20 dias atrás ficou de fora
    assert "Febre" not in pontos
    assert "Dor de cabeça forte ou que não passa (2 vezes: 13/10 e 14/10)" in pontos
    assert "Botão de emergência acionado em 17/10/2026 18:00; equipe avisada por e-mail: não" in pontos
    assert "Escala de Edimburgo em 16/10: 12 pontos (corte de triagem: 10)" in pontos
    assert "Maior pressão arterial registrada no período: 145/95 mmHg" in pontos
    assert "Humor 1 ou 2 (escala de 1 a 5) em 2 dos 2 check-ins" in pontos
    assert "Exame da agenda com data passada e não marcado como feito: Glicemia de jejum" in pontos
    assert "diferença de +1,5 kg" in pontos
    assert dados["proxima_consulta"].titulo == "Retorno"
    # Urgência vem antes do resto
    assert dados["pontos"][0].startswith("Sinal de urgência")
    assert gerar_pdf(dados).startswith(b"%PDF")


def test_recusa_de_ia_tira_o_rastreio_e_so_entram_conversas_autorizadas(client, aprovar_profissional, db_session):
    gestante_id, _, prof_id, _ = _gestante_vinculada(client, aprovar_profissional)
    outra_id, _ = _profissional(client, aprovar_profissional, nome="Dr. Outro")
    prof = db_session.query(Profissional).filter(Profissional.id == prof_id).first()
    agora = datetime.utcnow()

    db_session.add(Mensagem(gestante_id=gestante_id, papel="gestante", conteudo="Posso tomar dipirona?",
                            data_hora=agora - timedelta(days=2), autorizado_compartilhar=True))
    db_session.add(Mensagem(gestante_id=gestante_id, papel="gestante", conteudo="Assunto particular",
                            data_hora=agora - timedelta(days=1), autorizado_compartilhar=False))
    db_session.add(ObservacaoProfissional(profissional_id=prof_id, gestante_id=gestante_id,
                                          observacao="Pedir urocultura", criado_em=agora - timedelta(days=3)))
    db_session.add(ObservacaoProfissional(profissional_id=outra_id, gestante_id=gestante_id,
                                          observacao="Anotação de outra profissional", criado_em=agora))
    db_session.commit()

    dados = montar_relatorio(db_session, gestante_id, prof, agora)
    assert dados["rastreio"] is not None  # aceitou a IA: estimativas entram
    assert [m.conteudo for m in dados["conversas"]] == ["Posso tomar dipirona?"]
    assert [a.observacao for a in dados["anotacoes"]] == ["Pedir urocultura"]

    gestante = db_session.query(Gestante).filter(Gestante.id == gestante_id).first()
    gestante.recusa_ia = True
    db_session.commit()
    dados = montar_relatorio(db_session, gestante_id, prof, agora)
    assert dados["recusa_ia"] is True and dados["rastreio"] is None
    assert gerar_pdf(dados).startswith(b"%PDF")


def test_sem_registros_nem_cadastro_clinico_o_pdf_sai_mesmo_assim(client, aprovar_profissional, db_session):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Nova", "email": f"rel_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    assert cad.status_code == 201, cad.text
    gestante_id = cad.json()["id"]
    prof_id, _ = _profissional(client, aprovar_profissional)
    prof = db_session.query(Profissional).filter(Profissional.id == prof_id).first()
    assert db_session.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante_id).first() is None

    dados = montar_relatorio(db_session, gestante_id, prof)
    assert dados["rastreio"] is None
    assert "Nenhum check-in no período." in dados["pontos"]
    assert gerar_pdf(dados).startswith(b"%PDF")


def test_texto_livre_com_marcacao_e_emoji_nao_quebra_o_pdf(client, aprovar_profissional, db_session):
    gestante_id, _, prof_id, _ = _gestante_vinculada(client, aprovar_profissional)
    prof = db_session.query(Profissional).filter(Profissional.id == prof_id).first()
    db_session.add(CheckinRegistro(gestante_id=gestante_id, data_hora=datetime.utcnow() - timedelta(hours=2), humor=4,
                                   sintomas=["Enjoo <forte>"], descricao="Tudo bem <b>sim</b> & feliz \U0001F60A",
                                   alerta_sintoma_fisico=[], sinais_atencao=["Pressão <alta> & dor"]))
    db_session.commit()

    dados = montar_relatorio(db_session, gestante_id, prof)
    assert "Pressão &lt;alta&gt; &amp; dor" in " ".join(dados["pontos"])
    assert gerar_pdf(dados).startswith(b"%PDF")
