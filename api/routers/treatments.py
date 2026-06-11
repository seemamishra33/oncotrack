"""

Treatment endpoints.

GET    /api/treatments/patient/{patient_id}   list treatments
POST   /api/treatments                         create treatment
PATCH  /api/treatments/{treatment_id}          update treatment
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.Connection import get_db
from database.Schemas import TreatmentCreate, TreatmentUpdate, TreatmentResponse
from database.Crud import (
    create_treatment,
    get_treatments,
    update_treatment,
    get_patient,
)

logger = logging.getLogger("oncotrack.routers.treatments")
router = APIRouter()


@router.get("/patient/{patient_id}", response_model=List[TreatmentResponse])
def list_treatments(
    patient_id     : int,
    treatment_type : Optional[str] = Query(None, description="Filter by type e.g. Chemotherapy"),
    db             : Session       = Depends(get_db)
):
    """
    Returns all treatments for a patient.
    Optionally filter by treatment type.

    Examples:
        GET /api/treatments/patient/1
        GET /api/treatments/patient/1?treatment_type=Chemotherapy
    """
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {patient_id} not found"
        )
    treatments = get_treatments(db, patient_id, treatment_type=treatment_type)
    logger.info(f"Listed {len(treatments)} treatments for patient {patient_id}")
    return treatments


@router.post("/", response_model=TreatmentResponse, status_code=201)
def create_new_treatment(
    data : TreatmentCreate,
    db   : Session = Depends(get_db)
):
    """Creates a new treatment record for a patient."""
    patient = get_patient(db, data.patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {data.patient_id} not found"
        )
    treatment = create_treatment(db, data)
    logger.info(f"Created treatment for patient {data.patient_id}")
    return treatment


@router.patch("/{treatment_id}", response_model=TreatmentResponse)
def update_existing_treatment(
    treatment_id : int,
    data         : TreatmentUpdate,
    db           : Session = Depends(get_db)
):
    """Updates a treatment — only fields you send get changed."""
    treatment = update_treatment(db, treatment_id, data)
    if not treatment:
        raise HTTPException(
            status_code = 404,
            detail      = f"Treatment {treatment_id} not found"
        )
    logger.info(f"Updated treatment {treatment_id}")
    return treatment