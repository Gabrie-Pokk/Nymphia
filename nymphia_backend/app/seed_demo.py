"""
Nymphia — Seed automático das contas de demonstração para testes
Garante que os 3 perfis de teste (Gestante, Médico, Parceiro) estejam
sempre disponíveis e vinculados na subida do backend em qualquer ambiente.
"""
import logging
from datetime import datetime, timedelta
from app.database import engine, SessionLocal, Base
from app.models.auth import Gestante, Profissional, Parceiro
from app.models.clinical import PerfilClinico, HistoricoFamiliar, RegistroAntropometrico
from app.models.relations import Vinculo, VinculoParceiro
from app.models.interaction import EventoAgenda
from app.auth import hash_senha

logger = logging.getLogger("nymphia.seed")

def seed_demo_accounts():
    db = SessionLocal()
    try:
        senha_padrao = hash_senha("senhaMaternidade123")

        # 1. Gestante Demo
        gestante = db.query(Gestante).filter_by(email="gestante@nymphia.com.br").first()
        if not gestante:
            gestante = Gestante(
                nome="Mariana Costa",
                email="gestante@nymphia.com.br",
                senha_hash=senha_padrao,
                recusa_ia=False
            )
            db.add(gestante)
            db.commit()
            db.refresh(gestante)
            logger.info("Conta demo Gestante criada: gestante@nymphia.com.br")
        else:
            gestante.senha_hash = senha_padrao
            gestante.nome = "Mariana Costa"
            db.commit()

        # Perfil Clínico da Gestante (com Antropometria Base)
        perfil = db.query(PerfilClinico).filter_by(gestante_id=gestante.id).first()
        dum_data = (datetime.utcnow() - timedelta(days=24 * 7)).date()
        dpp_data = (datetime.utcnow() + timedelta(days=16 * 7)).date()
        if not perfil:
            perfil = PerfilClinico(
                gestante_id=gestante.id,
                idade=28,
                estado_civil="Casada",
                escolaridade="Superior Completo",
                gestacoes_anteriores=0,
                partos_normais=0,
                partos_cesareos=0,
                perdas_gestacionais=0,
                dum=dum_data,
                dpp=dpp_data,
                altura_cm=165.0,
                peso_pre_gestacional=62.0,
                maternidade_nome="Hospital e Maternidade Santa Joana",
                maternidade_endereco="R. Dr. Eduardo Amaro, 225 - Paraíso, São Paulo - SP",
                maternidade_telefone="(11) 5080-6000"
            )
            db.add(perfil)
        else:
            perfil.dum = dum_data
            perfil.dpp = dpp_data
            perfil.maternidade_nome = "Hospital e Maternidade Santa Joana"
            if not perfil.altura_cm:
                perfil.altura_cm = 165.0
            if not perfil.peso_pre_gestacional:
                perfil.peso_pre_gestacional = 62.0
        db.commit()

        # Histórico Antropométrico da Gestante Demo (Curva de Atalah e Altura Uterina)
        num_regs = db.query(RegistroAntropometrico).filter_by(gestante_id=gestante.id).count()
        if num_regs == 0:
            reg1 = RegistroAntropometrico(
                gestante_id=gestante.id,
                data_registro=(datetime.utcnow() - timedelta(days=12 * 7)).date(),
                semana_gestacional=12,
                peso_atual_kg=63.1,
                altura_uterina_cm=12.0,
                circunferencia_abdominal_cm=78.0,
                pressao_arterial="110x70",
                edema="ausente",
                observacoes="1º trimestre tranquilo, sem queixas."
            )
            reg2 = RegistroAntropometrico(
                gestante_id=gestante.id,
                data_registro=(datetime.utcnow() - timedelta(days=6 * 7)).date(),
                semana_gestacional=18,
                peso_atual_kg=65.2,
                altura_uterina_cm=17.5,
                circunferencia_abdominal_cm=84.0,
                pressao_arterial="115x75",
                edema="ausente",
                observacoes="Início dos movimentos fetais perceptíveis."
            )
            reg3 = RegistroAntropometrico(
                gestante_id=gestante.id,
                data_registro=datetime.utcnow().date(),
                semana_gestacional=24,
                peso_atual_kg=67.4,
                altura_uterina_cm=23.0,
                circunferencia_abdominal_cm=90.0,
                pressao_arterial="120x80",
                edema="ausente",
                observacoes="Consulta com Dr. Carlos. Curva de Atalah adequada e altura uterina no percentil ideal."
            )
            db.add_all([reg1, reg2, reg3])
            db.commit()

        # 2. Médico Demo
        medico = db.query(Profissional).filter_by(email="medico@nymphia.com.br").first()
        if not medico:
            medico = Profissional(
                nome="Dr. Carlos Silva",
                email="medico@nymphia.com.br",
                senha_hash=senha_padrao,
                registro_tipo="CRM",
                registro_numero="123456",
                registro_uf="SP",
                status_verificacao="aprovado"
            )
            db.add(medico)
            db.commit()
            db.refresh(medico)
            logger.info("Conta demo Médico criada: medico@nymphia.com.br")
        else:
            medico.senha_hash = senha_padrao
            medico.nome = "Dr. Carlos Silva"
            medico.status_verificacao = "aprovado"
            db.commit()

        # Vínculo Médico <-> Gestante
        vinc_medico = db.query(Vinculo).filter_by(gestante_id=gestante.id, profissional_id=medico.id).first()
        if not vinc_medico:
            vinc_medico = Vinculo(
                gestante_id=gestante.id,
                profissional_id=medico.id,
                status="ativo",
                criado_em=datetime.utcnow()
            )
            db.add(vinc_medico)
            db.commit()

        # 3. Parceiro Demo
        parceiro = db.query(Parceiro).filter_by(email="parceiro@nymphia.com.br").first()
        if not parceiro:
            parceiro = Parceiro(
                nome="Lucas Mendes",
                email="parceiro@nymphia.com.br",
                senha_hash=senha_padrao
            )
            db.add(parceiro)
            db.commit()
            db.refresh(parceiro)
            logger.info("Conta demo Parceiro criada: parceiro@nymphia.com.br")
        else:
            parceiro.senha_hash = senha_padrao
            parceiro.nome = "Lucas Mendes"
            db.commit()

        # Vínculo Parceiro <-> Gestante
        vinc_parc = db.query(VinculoParceiro).filter_by(gestante_id=gestante.id).first()
        if not vinc_parc:
            vinc_parc = VinculoParceiro(
                gestante_id=gestante.id,
                parceiro_id=parceiro.id,
                status="ativo",
                criado_em=datetime.utcnow()
            )
            db.add(vinc_parc)
            db.commit()
        else:
            vinc_parc.parceiro_id = parceiro.id
            vinc_parc.status = "ativo"
            db.commit()

        # Agenda da Gestante
        evs = db.query(EventoAgenda).filter_by(gestante_id=gestante.id).count()
        if evs == 0:
            e1 = EventoAgenda(
                gestante_id=gestante.id,
                tipo="consulta",
                titulo="Consulta de Pré-Natal com Dr. Carlos",
                data_hora=datetime.utcnow() + timedelta(days=3, hours=4),
                notas="Levar resultados de hemograma e curva glicêmica.",
                concluido=False
            )
            e2 = EventoAgenda(
                gestante_id=gestante.id,
                tipo="exame",
                titulo="Ultrassom Morfológico de 2º Trimestre",
                data_hora=datetime.utcnow() + timedelta(days=7, hours=2),
                notas="Chegar com 20 minutos de antecedência.",
                concluido=False
            )
            db.add_all([e1, e2])
            db.commit()

        logger.info("Contas demo verificadas e prontas para uso em produção.")
    except Exception as e:
        logger.error(f"Erro ao inicializar contas demo: {e}")
        db.rollback()
    finally:
        db.close()
