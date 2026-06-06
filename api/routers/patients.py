"""
patients.py
===========
Patient CRUD endpoints.

GET    /api/patients           list all patients (with filters)
GET    /api/patients/{id}      get one patient
GET    /api/patients/mrn/{mrn} get patient by MRN
POST   /api/patients           create a patient
PATCH  /api/patients/{id}      update a patient
DELETE /api/patients/{id}      delete a patient
GET    /api/patients/{id}/summary  full patient summary
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.Connection import get_db
from database.Schemas import PatientCreate, PatientUpdate, PatientResponse
from database.Crud import (
    create_patient,
    get_patient,
    get_patients,
    get_patient_by_mrn,
    update_patient,
    delete_patient,
    get_lab_results,
    get_treatments,
    get_visits,
)

logger = logging.getLogger("oncotrack.routers.patients")
router = APIRouter()


# ── LIST patients ─────────────────────────────────────────────
@router.get("/", response_model=List[PatientResponse])
def list_patients(
    skip   : int            = Query(0,    description="Number of records to skip"),
    limit  : int            = Query(100,  description="Max records to return"),
    status : Optional[str]  = Query(None, description="Filter by status: Active, Remission, Deceased"),
    stage  : Optional[str]  = Query(None, description="Filter by stage: I, II, III, IV"),
    db     : Session        = Depends(get_db)
):
    """
    Returns a list of patients.
    Supports pagination (skip/limit) and filtering by status and stage.

    Examples:
        GET /api/patients                      all patients
        GET /api/patients?status=Active        active only
        GET /api/patients?stage=III            stage III only
        GET /api/patients?skip=0&limit=10      first 10 patients
    """
    patients = get_patients(db, skip=skip, limit=limit, status=status, stage=stage)
    logger.info(f"Listed {len(patients)} patients")
    return patients


# ── GET one patient ───────────────────────────────────────────
@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(
    patient_id : int,
    db         : Session = Depends(get_db)
):
    """
    Returns a single patient by id.
    Raises 404 if not found.
    """
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {patient_id} not found"
        )
    return patient


# ── GET patient by MRN ────────────────────────────────────────
@router.get("/mrn/{mrn}", response_model=PatientResponse)
def read_patient_by_mrn(
    mrn : str,
    db  : Session = Depends(get_db)
):
    """
    Returns a patient by Medical Record Number.
    Useful for looking up a specific patient quickly.
    """
    patient = get_patient_by_mrn(db, mrn)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient with MRN {mrn} not found"
        )
    return patient


# ── CREATE patient ────────────────────────────────────────────
@router.post("/", response_model=PatientResponse, status_code=201)
def create_new_patient(
    data : PatientCreate,
    db   : Session = Depends(get_db)
):
    """
    Creates a new patient record.
    Returns 201 Created on success.
    Returns 400 if MRN already exists.
    """
    # Check MRN is unique
    existing = get_patient_by_mrn(db, data.mrn)
    if existing:
        raise HTTPException(
            status_code = 400,
            detail      = f"Patient with MRN {data.mrn} already exists"
        )
    patient = create_patient(db, data)
    logger.info(f"Created patient: {patient.mrn}")
    return patient


# ── UPDATE patient ────────────────────────────────────────────
@router.patch("/{patient_id}", response_model=PatientResponse)
def update_existing_patient(
    patient_id : int,
    data       : PatientUpdate,
    db         : Session = Depends(get_db)
):
    """
    Updates a patient record.
    Only the fields you send get updated — others stay the same.

    Example — update just the status:
        PATCH /api/patients/1
        {"status": "Remission"}
    """
    patient = update_patient(db, patient_id, data)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {patient_id} not found"
        )
    logger.info(f"Updated patient: {patient_id}")
    return patient


# ── DELETE patient ────────────────────────────────────────────
@router.delete("/{patient_id}", status_code=204)
def delete_existing_patient(
    patient_id : int,
    db         : Session = Depends(get_db)
):
    """
    Deletes a patient and all related records.
    Returns 204 No Content on success.
    Returns 404 if patient not found.

    WARNING: This also deletes all lab results,
    treatments and visits for this patient (cascade).
    """
    deleted = delete_patient(db, patient_id)
    if not deleted:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {patient_id} not found"
        )
    logger.info(f"Deleted patient: {patient_id}")
    return None


# ── GET patient summary ───────────────────────────────────────
@router.get("/{patient_id}/summary")
def patient_summary(
    patient_id : int,
    db         : Session = Depends(get_db)
):
    """
    Returns a full summary of a patient including
    their labs, treatments and visits counts.
    Useful for the Streamlit dashboard patient detail page.
    """
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code = 404,
            detail      = f"Patient {patient_id} not found"
        )

    labs       = get_lab_results(db, patient_id)
    treatments = get_treatments(db,  patient_id)
    visits     = get_visits(db,      patient_id)

    return {
        "patient"          : {
            "id"             : patient.id,
            "mrn"            : patient.mrn,
            "full_name"      : f"{patient.first_name} {patient.last_name}",
            "dob"            : str(patient.dob),
            "gender"         : patient.gender,
            "cancer_type"    : patient.cancer_type,
            "cancer_stage"   : patient.cancer_stage,
            "diagnosis_date" : str(patient.diagnosis_date),
            "status"         : patient.status,
        },
        "summary"          : {
            "total_labs"       : len(labs),
            "total_treatments" : len(treatments),
            "total_visits"     : len(visits),
            "abnormal_labs"    : sum(1 for l in labs if l.is_abnormal),
        }
    }