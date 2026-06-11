"""

Lab result endpoints.

GET    /api/labs/patient/{patient_id}     list labs for a patient
GET    /api/labs/{lab_id}                 get one lab result
POST   /api/labs                          create a lab result
PATCH  /api/labs/{lab_id}                 update a lab result
GET    /api/labs/patient/{id}/abnormal    abnormal results only
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.Connection import get_db
from database.Schemas import LabResultCreate, LabResultUpdate, LabResultResponse
from database.Crud import (
    create_lab_result,
    get_lab_results,
    update_lab_result,
    get_patient,
)

logger = logging.getLogger("oncotrack.routers.labs")
router = APIRouter()


@router.get("/patient/{patient_id}", response_model=List[LabResultResponse])
def list_labs(
    patient_id : int,
    db         : Session = Depends(get_db)
):
    """
    Returns all lab results for a patient.
    Ordered by most recent first.
    """
    # Verify patient exists first
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {patient_id} not found"
        )
    labs = get_lab_results(db, patient_id)
    logger.info(f"Listed {len(labs)} labs for patient {patient_id}")
    return labs


@router.get("/patient/{patient_id}/abnormal", response_model=List[LabResultResponse])
def list_abnormal_labs(
    patient_id : int,
    db         : Session = Depends(get_db)
):
    """
    Returns only abnormal lab results for a patient.
    Useful for the dashboard alert panel.
    """
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    labs = get_lab_results(db, patient_id, abnormal_only=True)
    logger.info(f"Found {len(labs)} abnormal labs for patient {patient_id}")
    return labs


@router.post("/", response_model=LabResultResponse, status_code=201)
def create_new_lab(
    data : LabResultCreate,
    db   : Session = Depends(get_db)
):
    """Creates a new lab result for a patient."""
    patient = get_patient(db, data.patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {data.patient_id} not found"
        )
    lab = create_lab_result(db, data)
    logger.info(f"Created lab result for patient {data.patient_id}")
    return lab


@router.patch("/{lab_id}", response_model=LabResultResponse)
def update_existing_lab(
    lab_id : int,
    data   : LabResultUpdate,
    db     : Session = Depends(get_db)
):
    """Updates a lab result — only fields you send get changed."""
    lab = update_lab_result(db, lab_id, data)
    if not lab:
        raise HTTPException(
            status_code = 404,
            detail      = f"Lab result {lab_id} not found"
        )
    logger.info(f"Updated lab result {lab_id}")
    return lab