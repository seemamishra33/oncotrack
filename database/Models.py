"""
models.py
=========
SQLAlchemy ORM models — one Python class per database table.

WHAT IS AN ORM?
    ORM = Object Relational Mapper.
    Instead of writing raw SQL like:
        SELECT * FROM patients WHERE id = 5
    You write Python like:
        session.query(Patient).filter(Patient.id == 5).first()

    SQLAlchemy translates your Python into SQL automatically.
    This means:
        - Less SQL to write
        - Python catches typos at startup, not at runtime
        - Easy to switch databases later (MySQL → PostgreSQL) with minimal changes

CONCEPTS DEMONSTRATED:
    - SQLAlchemy ORM    : Python classes that map to database tables
    - Relationships     : how tables link to each other (Patient has many LabResults)
    - Column types      : Integer, String, Date, Enum, etc.
    - Constraints       : NOT NULL, UNIQUE, FOREIGN KEY, CHECK
"""

from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Text,
    Boolean, Enum, ForeignKey, Numeric, SmallInteger,
    func, JSON, SMALLINT , Computed                # func.now() = SQL's NOW() function
)
from sqlalchemy.orm import relationship, Mapped, mapped_column  # defines how models link to each other
from database.Connection import Base      # the parent class all models inherit from



# ── User ──────────────────────────────────────────────────────────────────────
class User(Base):
    """
    Represents a clinician or admin who logs into the system.
    Every action (creating a patient, ordering a lab) is linked to a User
    through the audit_logs table — this is how we track who did what.
    """
    __tablename__ = "users"

    # Column(type, constraints)
    # primary_key=True  → this column uniquely identifies each row
    # autoincrement     → MySQL assigns the next available number automatically
    id            = Column(Integer, primary_key=True, autoincrement=True)

    # nullable=False    → this field is required (cannot be left empty)
    # unique=True       → no two users can have the same username
    username      = Column(String(64),  nullable=False, unique=True)
    email         = Column(String(128), nullable=False, unique=True)
    password_hash = Column(String(256), nullable=False)

    # Enum restricts the value to one of a fixed set of choices.
    # If you try to save role="superuser" it will raise an error.
    role          = Column(
                        Enum("admin", "oncologist", "nurse", "viewer"),
                        nullable=False,
                        default="viewer"
                    )
    is_active     = Column(Boolean, nullable=False, default=True)

    # server_default="CURRENT_TIMESTAMP" means MySQL sets this automatically
    # when a row is inserted — you don't need to pass it in Python.
    created_at    = Column(DateTime, server_default=func.now())

    # Relationships — these are Python-only, not real DB columns.
    # They let you write:  user.patients  instead of a JOIN query.
    # back_populates links the two sides of the relationship together.
    patients      = relationship("Patient",   back_populates="created_by_user")
    audit_logs    = relationship("AuditLog",  back_populates="user")

    def __repr__(self):
        # __repr__ controls what prints when you do print(user) — useful for debugging
        return f"<User id={self.id} username={self.username} role={self.role}>"


# ── Patient ───────────────────────────────────────────────────────────────────
class Patient(Base):
    """
    The central table — every other table links back to a patient.
    Stores demographics, cancer diagnosis details, and current status.
    """
    __tablename__ = "patients"

    id             = Column(Integer, primary_key=True, autoincrement=True)

    # MRN = Medical Record Number — unique identifier used in hospitals
    mrn            = Column(String(16),  nullable=False, unique=True)

    first_name     = Column(String(64),  nullable=False)
    last_name      = Column(String(64),  nullable=False)
    dob            = Column(Date,        nullable=False)   # Date stores only YYYY-MM-DD
    gender         = Column(
                        Enum("Male", "Female", "Other", "Prefer not to say"),
                        nullable=False
                    )
    ethnicity      = Column(String(64))     # no nullable=False → this field is optional
    phone          = Column(String(20))
    email          = Column(String(128))
    address        = Column(Text)           # Text = unlimited length string

    # ── Oncology-specific fields ──
    cancer_type    = Column(String(128), nullable=False)
    cancer_stage   = Column(
                        Enum("I", "II", "III", "IV", "Unknown"),
                        nullable=False,
                        default="Unknown"
                    )
    diagnosis_date = Column(Date,        nullable=False)
    primary_site   = Column(String(128))
    histology      = Column(String(128))
    status         = Column(
                        Enum("Active", "Remission", "Deceased", "Lost to Follow-up"),
                        nullable=False,
                        default="Active"
                    )

    # ForeignKey links this column to users.id
    # SET NULL means: if the user is deleted, set this to NULL rather than
    # deleting the patient (we don't want to lose patient data!)
    created_by     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    created_at     = Column(DateTime, server_default=func.now())
    updated_at     = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships — give us easy access to related records
    created_by_user = relationship("User",       back_populates="patients",    foreign_keys=[created_by])
    lab_results     = relationship("LabResult",  back_populates="patient",     cascade="all, delete-orphan")
    treatments      = relationship("Treatment",  back_populates="patient",     cascade="all, delete-orphan")
    visits          = relationship("Visit",      back_populates="patient",     cascade="all, delete-orphan")

    # cascade="all, delete-orphan" means: if a patient is deleted,
    # automatically delete all their lab results, treatments, and visits too.

    def __repr__(self):
        return f"<Patient id={self.id} mrn={self.mrn} name={self.first_name} {self.last_name}>"


# ── Lab Result ────────────────────────────────────────────────────────────────
class LabResult(Base):
    """
    One row = one lab test result for one patient on one date.
    A patient might have dozens of CBC tests over months — each is a separate row.

    The is_abnormal field is calculated automatically by MySQL using a
    generated column (defined in schema.sql), so we mark it as not stored
    in the ORM but still readable.
    """
    __tablename__ = "lab_results"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    patient_id     = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)

    test_name      = Column(String(128), nullable=False)  # e.g. "Hemoglobin", "CA-125"
    test_category  = Column(
                        Enum("CBC", "Tumor Marker", "Metabolic Panel",
                             "Coagulation", "Urinalysis", "Other"),
                        nullable=False
                    )

    # Numeric(10, 3) = up to 10 digits total, 3 after the decimal point
    # e.g. 9999999.999 — good for lab values like 134.500
    value          = Column(Numeric(10, 3), nullable=False)
    unit           = Column(String(32),     nullable=False)  # e.g. "g/dL", "U/mL"
    reference_low  = Column(Numeric(10, 3))   # normal range lower bound
    reference_high = Column(Numeric(10, 3))   # normal range upper bound
    is_abnormal = Column(Boolean, Computed("value < reference_low OR value > reference_high"), default=None)
    collected_at   = Column(DateTime, nullable=False)  # when blood was drawn
    resulted_at    = Column(DateTime)                  # when result came back (optional)
    notes          = Column(Text)
    ordered_by     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at     = Column(DateTime, server_default=func.now())

    # Relationships
    patient        = relationship("Patient", back_populates="lab_results")
    ordering_user  = relationship("User", foreign_keys=[ordered_by])

    def __repr__(self):
        return f"<LabResult id={self.id} test={self.test_name} value={self.value} {self.unit}>"


# ── Treatment ─────────────────────────────────────────────────────────────────
class Treatment(Base):
    """
    One row = one course of treatment (e.g. 6 cycles of FOLFOX chemotherapy).
    A patient may have multiple treatments — surgery first, then chemo, then radiation.
    """
    __tablename__ = "treatments"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    patient_id      = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)

    treatment_type  = Column(
                          Enum("Chemotherapy", "Radiation", "Surgery",
                               "Immunotherapy", "Targeted Therapy",
                               "Hormone Therapy", "Palliative", "Other"),
                          nullable=False
                      )
    protocol_name   = Column(String(128))   # e.g. "FOLFOX", "R-CHOP"
    drug_regimen    = Column(Text)          # full drug names and doses

    start_date      = Column(Date, nullable=False)
    end_date        = Column(Date)          # nullable — treatment may still be ongoing

    cycle_number    = Column(Integer)       # which cycle the patient is currently on
    total_cycles    = Column(Integer)       # total cycles planned

    # Numeric(8, 2) = up to 8 digits, 2 decimal places — e.g. 175.50 mg
    dose_mg         = Column(Numeric(8, 2))
    dose_unit       = Column(String(32), default="mg")
    frequency       = Column(String(64))    # e.g. "Q3W" = every 3 weeks

    response        = Column(
                          Enum("Complete Response", "Partial Response",
                               "Stable Disease", "Progressive Disease", "Unknown"),
                          default="Unknown"
                      )

    # SmallInteger is more efficient for small numbers (0-5 range here)
    toxicity_grade  = Column(SmallInteger)  # 0=none, 1=mild, 2=moderate, 3=severe, 4=life-threatening, 5=death
    notes           = Column(Text)
    administered_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    patient         = relationship("Patient", back_populates="treatments")
    administered_by_user = relationship("User", foreign_keys=[administered_by])

    def __repr__(self):
        return f"<Treatment id={self.id} type={self.treatment_type} protocol={self.protocol_name}>"


# ── Visit ─────────────────────────────────────────────────────────────────────
class Visit(Base):
    """
    One row = one clinical visit (in-person or telehealth).
    Records weight, performance status (ECOG), assessment and plan.
    ECOG score (0-4) measures how cancer affects daily activities.
    """
    __tablename__ = "visits"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    patient_id      = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)

    visit_date      = Column(DateTime, nullable=False)
    visit_type      = Column(
                          Enum("Initial Consult", "Follow-up", "Chemo Session",
                               "Radiation Session", "Urgent", "Telehealth"),
                          nullable=False
                      )
    attending_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # Numeric(5, 2) = up to 5 digits, 2 decimal — e.g. 75.50 kg
    weight_kg       = Column(Numeric(5, 2))
    height_cm       = Column(Numeric(5, 2))

    # ECOG performance status: 0=fully active, 4=completely disabled
    ecog_score      = Column(SmallInteger)

    chief_complaint = Column(Text)  # why the patient came in today
    assessment      = Column(Text)  # clinician's findings
    plan            = Column(Text)  # what happens next
    created_at      = Column(DateTime, server_default=func.now())

    # Relationships
    patient         = relationship("Patient", back_populates="visits")
    attending       = relationship("User", foreign_keys=[attending_id])

    def __repr__(self):
        return f"<Visit id={self.id} patient_id={self.patient_id} date={self.visit_date}>"


# ── Audit Log ─────────────────────────────────────────────────────────────────
class AuditLog(Base):
    """
    Every API call that reads or changes patient data gets logged here.
    This is a compliance requirement in healthcare (HIPAA audit trail).
    We populate this automatically using a FastAPI middleware decorator —
    no developer has to remember to add logging manually.

    Example row:
        user_id=3, action=READ, resource=patients, resource_id=42,
        endpoint=/patients/42, status_code=200
    """
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # What happened
    action      = Column(String(64), nullable=False)   # READ, CREATE, UPDATE, DELETE
    resource    = Column(String(64), nullable=False)   # patients, lab_results, etc.
    resource_id = Column(Integer)                      # which specific record

    # Context
    endpoint    = Column(String(256))   # e.g. /api/patients/42
    ip_address  = Column(String(45))    # supports IPv6 (max 45 chars)
    status_code = Column(SmallInteger)  # HTTP status: 200, 404, 500, etc.

    created_at  = Column(DateTime, server_default=func.now())

    # Relationship
    user        = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} resource={self.resource}/{self.resource_id}>"