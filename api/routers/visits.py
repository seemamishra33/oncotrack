"""

Visit endpoints.

GET    /api/visits/patient/{patient_id}   list visits
POST   /api/visits                         create visit
PATCH  /api/visits/{visit_id}              update visit
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.Connection import get_db
from database.Schemas import VisitCreate, VisitUpdate, VisitResponse
from database.Crud import (
    create_visit,
    get_visits,
    update_visit,
    get_patient,
)

logger = logging.getLogger("oncotrack.routers.visits")
router = APIRouter()


@router.get("/patient/{patient_id}", response_model=List[VisitResponse])
def list_visits(
    patient_id : int,
    visit_type : Optional[str] = Query(None, description="Filter by type e.g. Follow-up"),
    db         : Session       = Depends(get_db)
):
    """
    Returns all visits for a patient.
    Optionally filter by visit type.

    Examples:
        GET /api/visits/patient/1
        GET /api/visits/patient/1?visit_type=Follow-up
    """
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {patient_id} not found"
        )
    visits = get_visits(db, patient_id, visit_type=visit_type)
    logger.info(f"Listed {len(visits)} visits for patient {patient_id}")
    return visits


@router.post("/", response_model=VisitResponse, status_code=201)
def create_new_visit(
    data : VisitCreate,
    db   : Session = Depends(get_db)
):
    """Creates a new visit record for a patient."""
    patient = get_patient(db, data.patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {data.patient_id} not found"
        )
    visit = create_visit(db, data)
    logger.info(f"Created visit for patient {data.patient_id}")
    return visit


@router.patch("/{visit_id}", response_model=VisitResponse)
def update_existing_visit(
    visit_id : int,
    data     : VisitUpdate,
    db       : Session = Depends(get_db)
):
    """Updates a visit — only fields you send get changed."""
    visit = update_visit(db, visit_id, data)
    if not visit:
        raise HTTPException(
            status_code = 404,
            detail      = f"Visit {visit_id} not found"
        )
    logger.info(f"Updated visit {visit_id}")
    return visit