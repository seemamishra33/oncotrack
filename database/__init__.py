"""
__init__.py
===========
Makes the database/ folder a Python package.
Exposes the most commonly used objects so other
parts of the app can import them cleanly.
"""

# Connection essentials — needed by every route
from database.Connection import engine, SessionLocal, get_db, Base

# ORM Models — needed by FastAPI and Streamlit
from database.Models import (
    User,
    Patient,
    LabResult,
    Treatment,
    Visit,
    AuditLog,
)

# CRUD operations — needed by FastAPI routes
from database.Crud import (
    # User
    create_user, get_user, get_users,
    get_user_by_username, update_user, delete_user,
    # Patient
    create_patient, get_patient, get_patients,
    get_patient_by_mrn, update_patient, delete_patient,
    # Lab Results
    create_lab_result, get_lab_results, update_lab_result,
    # Treatments
    create_treatment, get_treatments, update_treatment,
    # Visits
    create_visit, get_visits, update_visit,
    # Audit
    create_audit_log, get_audit_logs,
)

# Package version
__version__ = "1.0.0"
__all__ = [
    # Connection
    "engine", "SessionLocal", "get_db", "Base",
    # Models
    "User", "Patient", "LabResult", "Treatment", "Visit", "AuditLog",
    # Crud
    "create_user", "get_user", "get_users", "get_user_by_username",
    "update_user", "delete_user",
    "create_patient", "get_patient", "get_patients", "get_patient_by_mrn",
    "update_patient", "delete_patient",
    "create_lab_result", "get_lab_results", "update_lab_result",
    "create_treatment", "get_treatments", "update_treatment",
    "create_visit", "get_visits", "update_visit",
    "create_audit_log", "get_audit_logs",
]