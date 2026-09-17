import random
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.devices import CintaNymphiaLeitura
from app.schemas.all_schemas import CintaLeituraCreate, CintaLeituraOut
from app.security.jwt_auth import get_current_gestante

router = APIRouter(prefix="/cinta", tags=["Cinta Nymphia — Doppler Wearable (Roadmap 2027 V3)"])

NORMAL_BPM_MIN = 110
NORMAL_BPM_MAX = 160

def classify_fhr(bpm: int) -> str:
    if bpm < NORMAL_BPM_MIN:
        return "bradicardia"
    elif bpm > NORMAL_BPM_MAX:
        return "taquicardia"
    return "normal"

@router.post("/telemetria", response_model=CintaLeituraOut, status_code=status.HTTP_201_CREATED)
def registrar_leitura_doppler(
    payload: CintaLeituraCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Ingestão de batimentos cardíacos fetais (FHR) contínuos transmitidos
    pelos transdutores Doppler da Cinta Nymphia.
    """
    fhr_status = classify_fhr(payload.bpm)
    leitura = CintaNymphiaLeitura(
        gestante_id=gestante.id,
        bpm=payload.bpm,
        status=fhr_status,
        data_hora=datetime.utcnow()
    )
    db.add(leitura)
    db.commit()
    db.refresh(leitura)
    return leitura

@router.get("/leituras-recentes", response_model=List[CintaLeituraOut])
def listar_leituras_recentes(
    limite: int = 60,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Retorna as últimas leituras de FHR para renderização contínua do traçado cardiotocográfico.
    """
    leituras = (
        db.query(CintaNymphiaLeitura)
        .filter(CintaNymphiaLeitura.gestante_id == gestante.id)
        .order_by(CintaNymphiaLeitura.data_hora.desc())
        .limit(limite)
        .all()
    )
    # Retorna em ordem cronológica para o gráfico
    return list(reversed(leituras))

@router.get("/simulador")
def obter_leitura_simulador():
    """
    Endpoint gerador de telemetria Doppler contínua para demonstração do hardware 2027.
    Gera batimentos fisiológicos (120-155 bpm) com variabilidade batimento a batimento.
    """
    base_bpm = 138
    variabilidade = random.randint(-8, 8)
    simulated_bpm = base_bpm + variabilidade
    return {
        "bpm": simulated_bpm,
        "status": classify_fhr(simulated_bpm),
        "linha_de_base_normal": "110-160 bpm",
        "timestamp": datetime.utcnow().isoformat(),
        "sinal_transdutor": "otimo",
        "audio_doppler_simulado": True
    }
