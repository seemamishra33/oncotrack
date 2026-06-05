"""
Schemas.py
==========
Pydantic schemas for data validation.

RULE OF THUMB:
    - Models.py  = shape of data IN the database
    - Schemas.py = shape of data IN/OUT of the API

Each table has up to three schemas:
    Base     → shared fields
    Create   → what the API accepts (POST)
    Update   → partial edits (PATCH) — all fields Optional
    Response → what the API returns (GET) — includes id, timestamps
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
import re


# ╔══════════════════════════════════════════════════════════════╗
# ║  USER schemas                                                ║
# ╚══════════════════════════════════════════════════════════════╝

class UserBase(BaseModel):
    username  : str
    email     : EmailStr        # Pydantic validates email format automatically
    role      : str = "viewer"
    is_active : bool = True


class UserCreate(UserBase):
    password  : str             # raw password — will be hashed before saving

    # field_validator runs automatically when UserCreate is instantiated
    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class UserUpdate(BaseModel):
    # ALL fields Optional — user can update just one field at a time
    username  : Optional[str]      = None
    email     : Optional[EmailStr] = None
    role      : Optional[str]      = None
    is_active : Optional[bool]     = None
    password  : Optional[str]      = None


class UserResponse(UserBase):
    id         : int
    created_at : datetime

    # This tells Pydantic: read data from ORM objects, not just dicts
    model_config = {"from_attributes": True}


# ╔══════════════════════════════════════════════════════════════╗
# ║  PATIENT schemas                                             ║
# ╚══════════════════════════════════════════════════════════════╝

class PatientBase(BaseModel):
    mrn            : str
    first_name     : str
    last_name      : str
    dob            : date
    gender         : str
    ethnicity      : Optional[str] = None
    phone          : Optional[str] = None
    email          : Optional[EmailStr] = None
    address        : Optional[str] = None
    cancer_type    : str
    cancer_stage   : str = "Unknown"
    diagnosis_date : date
    primary_site   : Optional[str] = None
    histology      : Optional[str] = None
    status         : str = "Active"


class PatientCreate(PatientBase):

    @field_validator("mrn")
    @classmethod
    def mrn_format(cls, value):
        # MRN must be alphanumeric, 4-16 characters
        if not re.match(r'^[A-Z0-9]{4,16}$', value):
            raise ValueError("MRN must be 4-16 uppercase letters/numbers")
        return value

    @field_validator("cancer_stage")
    @classmethod
    def valid_stage(cls, value):
        allowed = ["I", "II", "III", "IV", "Unknown"]
        if value not in allowed:
            raise ValueError(f"Stage must be one of {allowed}")
        return value


class PatientUpdate(BaseModel):
    # Every field Optional for partial updates
    first_name     : Optional[str]       = None
    last_name      : Optional[str]       = None
    phone          : Optional[str]       = None
    email          : Optional[EmailStr]  = None
    address        : Optional[str]       = None
    cancer_stage   : Optional[str]       = None
    primary_site   : Optional[str]       = None
    histology      : Optional[str]       = None
    status         : Optional[str]       = None


class PatientResponse(PatientBase):
    id         : int
    created_by : Optional[int] = None
    created_at : datetime
    updated_at : datetime

    model_config = {"from_attributes": True}


# ╔══════════════════════════════════════════════════════════════╗
# ║  LAB RESULT schemas                                          ║
# ╚══════════════════════════════════════════════════════════════╝

class LabResultBase(BaseModel):
    test_name      : str
    test_category  : str
    value          : Decimal
    unit           : str
    reference_low  : Optional[Decimal] = None
    reference_high : Optional[Decimal] = None
    collected_at   : datetime
    resulted_at    : Optional[datetime] = None
    notes          : Optional[str] = None


class LabResultCreate(LabResultBase):
    patient_id  : int
    ordered_by  : Optional[int] = None


class LabResultUpdate(BaseModel):
    value          : Optional[Decimal]  = None
    reference_low  : Optional[Decimal]  = None
    reference_high : Optional[Decimal]  = None
    resulted_at    : Optional[datetime] = None
    notes          : Optional[str]      = None


class LabResultResponse(LabResultBase):
    id          : int
    patient_id  : int
    is_abnormal : Optional[bool] = None   # computed by MySQL, read-only
    ordered_by  : Optional[int]  = None
    created_at  : datetime

    model_config = {"from_attributes": True}


# ╔══════════════════════════════════════════════════════════════╗
# ║  TREATMENT schemas                                           ║
# ╚══════════════════════════════════════════════════════════════╝

class TreatmentBase(BaseModel):
    treatment_type  : str
    protocol_name   : Optional[str]     = None
    drug_regimen    : Optional[str]     = None
    start_date      : date
    end_date        : Optional[date]    = None
    cycle_number    : Optional[int]     = None
    total_cycles    : Optional[int]     = None
    dose_mg         : Optional[Decimal] = None
    dose_unit       : Optional[str]     = "mg"
    frequency       : Optional[str]     = None
    response        : Optional[str]     = "Unknown"
    toxicity_grade  : Optional[int]     = None
    notes           : Optional[str]     = None


class TreatmentCreate(TreatmentBase):
    patient_id      : int
    administered_by : Optional[int] = None

    @field_validator("toxicity_grade")
    @classmethod
    def valid_toxicity(cls, value):
        if value is not None and not (0 <= value <= 5):
            raise ValueError("Toxicity grade must be between 0 and 5")
        return value


class TreatmentUpdate(BaseModel):
    end_date        : Optional[date]    = None
    cycle_number    : Optional[int]     = None
    response        : Optional[str]     = None
    toxicity_grade  : Optional[int]     = None
    notes           : Optional[str]     = None


class TreatmentResponse(TreatmentBase):
    id              : int
    patient_id      : int
    administered_by : Optional[int] = None
    created_at      : datetime

    model_config = {"from_attributes": True}


# ╔══════════════════════════════════════════════════════════════╗
# ║  VISIT schemas                                               ║
# ╚══════════════════════════════════════════════════════════════╝

class VisitBase(BaseModel):
    visit_date      : datetime
    visit_type      : str
    weight_kg       : Optional[Decimal] = None
    height_cm       : Optional[Decimal] = None
    ecog_score      : Optional[int]     = None
    chief_complaint : Optional[str]     = None
    assessment      : Optional[str]     = None
    plan            : Optional[str]     = None


class VisitCreate(VisitBase):
    patient_id  : int
    attending_id: Optional[int] = None

    @field_validator("ecog_score")
    @classmethod
    def valid_ecog(cls, value):
        if value is not None and not (0 <= value <= 5):
            raise ValueError("ECOG score must be between 0 and 5")
        return value


class VisitUpdate(BaseModel):
    weight_kg       : Optional[Decimal] = None
    height_cm       : Optional[Decimal] = None
    ecog_score      : Optional[int]     = None
    assessment      : Optional[str]     = None
    plan            : Optional[str]     = None


class VisitResponse(VisitBase):
    id           : int
    patient_id   : int
    attending_id : Optional[int] = None
    created_at   : datetime

    model_config = {"from_attributes": True}


# ╔══════════════════════════════════════════════════════════════╗
# ║  AUDIT LOG schemas                                           ║
# ╚══════════════════════════════════════════════════════════════╝

class AuditLogResponse(BaseModel):
    # Audit logs are read-only — no Create or Update schemas needed
    id          : int
    user_id     : Optional[int]  = None
    action      : str
    resource    : str
    resource_id : Optional[int]  = None
    endpoint    : Optional[str]  = None
    ip_address  : Optional[str]  = None
    status_code : Optional[int]  = None
    detail      : Optional[dict] = None
    created_at  : datetime

    model_config = {"from_attributes": True}


if __name__ == "__main__":
    # Test 1 — valid patient
    p = PatientCreate(
        mrn="MRN00123",
        first_name="Jane",
        last_name="Doe",
        dob="1980-05-15",
        gender="Female",
        cancer_type="Breast Cancer",
        cancer_stage="II",
        diagnosis_date="2024-01-10"
    )
    print(f"✓ Valid patient: {p.first_name} {p.last_name}, MRN: {p.mrn}")

    # Test 2 — bad MRN (lowercase)
    try:
        bad = PatientCreate(
            mrn="mrn123",           # ← lowercase, should fail
            first_name="John",
            last_name="Smith",
            dob="1975-03-20",
            gender="Male",
            cancer_type="Lung Cancer",
            cancer_stage="III",
            diagnosis_date="2024-02-01"
        )
    except Exception as e:
        print(f"✓ Validation caught bad MRN: {e.errors()[0]['msg']}")

    # Test 3 — bad toxicity grade
    try:
        bad = TreatmentCreate(
            patient_id=1,
            treatment_type="Chemotherapy",
            start_date="2024-01-15",
            toxicity_grade=9            # ← must be 0-5, should fail
        )
    except Exception as e:
        print(f"✓ Validation caught bad toxicity: {e.errors()[0]['msg']}")
