"""
Crud.py
=======
All database operations for OncoTrack.

CONCEPTS DEMONSTRATED:
    - Decorator     : @log_db_operation logs every operation automatically
    - Logging       : structured messages for debugging and audit trail
    - SQLAlchemy    : ORM queries instead of raw SQL
"""

import logging
import functools
import time
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.Models import User, Patient, LabResult, Treatment, Visit, AuditLog
from database.Schemas import (
    UserCreate, UserUpdate,
    PatientCreate, PatientUpdate,
    LabResultCreate, LabResultUpdate,
    TreatmentCreate, TreatmentUpdate,
    VisitCreate, VisitUpdate
)

# ── Logger setup ─────────────────────────────────────────────
logger = logging.getLogger("oncotrack.crud")


# ╔══════════════════════════════════════════════════════════════╗
# ║  DECORATOR — @log_db_operation                               ║
# ╚══════════════════════════════════════════════════════════════╝

def log_db_operation(func):
    """
    Decorator that wraps every CRUD function to:
      1. Log when the operation starts
      2. Measure how long it takes
      3. Log success with timing
      4. Log and re-raise any database errors
    """
    @functools.wraps(func)   # preserves the original function's name and docstring
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.info(f"START  {func.__name__}")
        try:
            result = func(*args, **kwargs)   # run the actual CRUD function
            elapsed = (time.time() - start) * 1000
            logger.info(f"OK     {func.__name__} ({elapsed:.1f}ms)")
            return result
        except SQLAlchemyError as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"FAILED {func.__name__} ({elapsed:.1f}ms) — {e}")
            raise   # re-raise so FastAPI returns a proper error response
    return wrapper


# ╔══════════════════════════════════════════════════════════════╗
# ║  USER operations                                             ║
# ╚══════════════════════════════════════════════════════════════╝

@log_db_operation
def create_user(db: Session, data: UserCreate) -> User:
    """Insert a new user. Password should be hashed before calling this."""
    user = User(
        username      = data.username,
        email         = data.email,
        password_hash = data.password,   # hash this in Phase 2 with bcrypt
        role          = data.role,
        is_active     = data.is_active,
    )
    db.add(user)       # stage the new row
    db.commit()        # write to database
    db.refresh(user)   # reload so user.id is populated
    return user


@log_db_operation
def get_user(db: Session, user_id: int) -> Optional[User]:
    """Fetch a single user by id."""
    return db.query(User).filter(User.id == user_id).first()


@log_db_operation
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Fetch a user by username — used for login."""
    return db.query(User).filter(User.username == username).first()


@log_db_operation
def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Fetch all users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()


@log_db_operation
def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[User]:
    """Update only the fields that were provided."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    # exclude_unset=True means only update fields the caller actually sent
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@log_db_operation
def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user. Returns True if deleted, False if not found."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


# ╔══════════════════════════════════════════════════════════════╗
# ║  PATIENT operations                                          ║
# ╚══════════════════════════════════════════════════════════════╝

@log_db_operation
def create_patient(db: Session, data: PatientCreate) -> Patient:
    """Insert a new patient record."""
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@log_db_operation
def get_patient(db: Session, patient_id: int) -> Optional[Patient]:
    """Fetch a single patient by id."""
    return db.query(Patient).filter(Patient.id == patient_id).first()


@log_db_operation
def get_patient_by_mrn(db: Session, mrn: str) -> Optional[Patient]:
    """Fetch a patient by Medical Record Number."""
    return db.query(Patient).filter(Patient.mrn == mrn).first()


@log_db_operation
def get_patients(
    db       : Session,
    skip     : int = 0,
    limit    : int = 100,
    status   : Optional[str] = None,   # filter by Active/Remission/etc
    stage    : Optional[str] = None,   # filter by cancer stage
) -> List[Patient]:
    """Fetch patients with optional filters and pagination."""
    query = db.query(Patient)
    if status:
        query = query.filter(Patient.status == status)
    if stage:
        query = query.filter(Patient.cancer_stage == stage)
    return query.offset(skip).limit(limit).all()


@log_db_operation
def update_patient(db: Session, patient_id: int, data: PatientUpdate) -> Optional[Patient]:
    """Update only the fields that were provided."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


@log_db_operation
def delete_patient(db: Session, patient_id: int) -> bool:
    """Delete a patient and all related records (cascade)."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return False
    db.delete(patient)
    db.commit()
    return True


# ╔══════════════════════════════════════════════════════════════╗
# ║  LAB RESULT operations                                       ║
# ╚══════════════════════════════════════════════════════════════╝

@log_db_operation
def create_lab_result(db: Session, data: LabResultCreate) -> LabResult:
    lab = LabResult(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return lab


@log_db_operation
def get_lab_results(
    db         : Session,
    patient_id : int,
    abnormal_only: bool = False,   # filter to only flagged results
) -> List[LabResult]:
    query = db.query(LabResult).filter(LabResult.patient_id == patient_id)
    if abnormal_only:
        query = query.filter(LabResult.is_abnormal == True)
    return query.order_by(LabResult.collected_at.desc()).all()


@log_db_operation
def update_lab_result(db: Session, lab_id: int, data: LabResultUpdate) -> Optional[LabResult]:
    lab = db.query(LabResult).filter(LabResult.id == lab_id).first()
    if not lab:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lab, field, value)
    db.commit()
    db.refresh(lab)
    return lab


# ╔══════════════════════════════════════════════════════════════╗
# ║  TREATMENT operations                                        ║
# ╚══════════════════════════════════════════════════════════════╝

@log_db_operation
def create_treatment(db: Session, data: TreatmentCreate) -> Treatment:
    treatment = Treatment(**data.model_dump())
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    return treatment


@log_db_operation
def get_treatments(
    db         : Session,
    patient_id : int,
    treatment_type: Optional[str] = None,
) -> List[Treatment]:
    query = db.query(Treatment).filter(Treatment.patient_id == patient_id)
    if treatment_type:
        query = query.filter(Treatment.treatment_type == treatment_type)
    return query.order_by(Treatment.start_date.desc()).all()


@log_db_operation
def update_treatment(db: Session, treatment_id: int, data: TreatmentUpdate) -> Optional[Treatment]:
    treatment = db.query(Treatment).filter(Treatment.id == treatment_id).first()
    if not treatment:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(treatment, field, value)
    db.commit()
    db.refresh(treatment)
    return treatment


# ╔══════════════════════════════════════════════════════════════╗
# ║  VISIT operations                                            ║
# ╚══════════════════════════════════════════════════════════════╝

@log_db_operation
def create_visit(db: Session, data: VisitCreate) -> Visit:
    visit = Visit(**data.model_dump())
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


@log_db_operation
def get_visits(
    db         : Session,
    patient_id : int,
    visit_type : Optional[str] = None,
) -> List[Visit]:
    query = db.query(Visit).filter(Visit.patient_id == patient_id)
    if visit_type:
        query = query.filter(Visit.visit_type == visit_type)
    return query.order_by(Visit.visit_date.desc()).all()


@log_db_operation
def update_visit(db: Session, visit_id: int, data: VisitUpdate) -> Optional[Visit]:
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(visit, field, value)
    db.commit()
    db.refresh(visit)
    return visit


# ╔══════════════════════════════════════════════════════════════╗
# ║  AUDIT LOG operations                                        ║
# ╚══════════════════════════════════════════════════════════════╝

@log_db_operation
def create_audit_log(
    db          : Session,
    action      : str,
    resource    : str,
    resource_id : Optional[int] = None,
    user_id     : Optional[int] = None,
    endpoint    : Optional[str] = None,
    status_code : Optional[int] = None,
    detail      : Optional[dict] = None,
) -> AuditLog:
    """Write an audit entry — called automatically by FastAPI middleware in Phase 2."""
    log = AuditLog(
        user_id     = user_id,
        action      = action,
        resource    = resource,
        resource_id = resource_id,
        endpoint    = endpoint,
        status_code = status_code,
        detail      = detail,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@log_db_operation
def get_audit_logs(
    db       : Session,
    resource : Optional[str] = None,
    user_id  : Optional[int] = None,
    limit    : int = 50,
) -> List[AuditLog]:
    """Fetch audit logs with optional filters."""
    query = db.query(AuditLog)
    if resource:
        query = query.filter(AuditLog.resource == resource)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()