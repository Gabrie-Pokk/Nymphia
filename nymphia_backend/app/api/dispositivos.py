from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.devices import MedicaoDispositivo
from app.schemas.all_schemas import MedicaoCreate, MedicaoOut
from app.security.jwt_auth import get_current_gestante
from app.services.rules_engine import analyze_urgency

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos e Bluetooth"])

@router.post("/medicao", response_model=MedicaoOut, status_code=status.HTTP_201_CREATED)
def registrar_medicao(
    payload: MedicaoCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Registra medição de monitor de pressão arterial de braço (BLE 0x1810) ou glicosímetro (BLE 0x1808).
    Alerta explicitamente contra uso de smartwatches ou aparelhos de pulso.
    """
    if payload.tipo not in ["pressao_arterial", "glicemia"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo inválido. Permitidos: 'pressao_arterial' ou 'glicemia'"
        )

    # Validação de dados clínicos
    if payload.tipo == "pressao_arterial":
        if not payload.sistolica or not payload.diastolica:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistólica e diastólica são obrigatórias para pressão arterial"
            )
    elif payload.tipo == "glicemia":
        if not payload.glicemia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valor de glicemia é obrigatório"
            )

    medicao = MedicaoDispositivo(
        gestante_id=gestante.id,
        tipo=payload.tipo,
        sistolica=payload.sistolica,
        diastolica=payload.diastolica,
        glicemia=payload.glicemia,
        origem=payload.origem,
        data_hora=datetime.utcnow()
    )
    db.add(medicao)
    db.commit()
    db.refresh(medicao)
    return medicao

@router.get("/medicoes", response_model=List[MedicaoOut])
def listar_medicoes(
    tipo: Optional[str] = None,
    desde: Optional[datetime] = None,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    query = db.query(MedicaoDispositivo).filter(MedicaoDispositivo.gestante_id == gestante.id)
    if tipo:
        query = query.filter(MedicaoDispositivo.tipo == tipo)
    if desde:
        query = query.filter(MedicaoDispositivo.data_hora >= desde)

    return query.order_by(MedicaoDispositivo.data_hora.desc()).all()

@router.get("/ble-info")
def obter_informacoes_ble():
    """
    Especificação dos perfis padrão Bluetooth SIG suportados pela Nymphia.
    """
    return {
        "dispositivos_suportados": [
            {
                "tipo": "pressao_arterial",
                "posicao": "braço (contraindicado punho ou smartwatch)",
                "service_uuid": "0x1810",
                "characteristic_uuid": "0x2A35",
                "modelo_referencia": "G-Tech LA850BT ou compatível"
            },
            {
                "tipo": "glicemia",
                "posicao": "capilar",
                "service_uuid": "0x1808",
                "characteristic_uuid": "0x2A18",
                "modelo_referencia": "Accu-Chek Guide Me ou compatível"
            }
        ],
        "contraindicacao_regulatoria": (
            "Smartwatches não possuem autorização médica para medição de pressão nem glicemia em gestantes. "
            "A Nymphia opera exclusivamente com aparelhos de braço e tiras glicêmicas validadas."
        )
    }
