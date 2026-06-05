import logging
logging.basicConfig(level=logging.INFO, format="%(name)s — %(message)s")

from database.Connection import SessionLocal
from database.Crud import (
    create_user, get_user, get_users,
    create_patient, get_patient, get_patients
)
from database.Schemas import UserCreate, PatientCreate
from datetime import date

db = SessionLocal()

# Test 1 — create a user
print("\n── CREATE USER ──")
user = create_user(db, UserCreate(
    username = "dr_smith",
    email    = "smith@oncotrack.com",
    password = "secure123",
    role     = "oncologist"
))
print(f"Created: {user}")

# Test 2 — fetch that user back
print("\n── GET USER ──")
fetched = get_user(db, user.id)
print(f"Fetched: {fetched}")

# Test 3 — create a patient
print("\n── CREATE PATIENT ──")
patient = create_patient(db, PatientCreate(
    mrn            = "MRN00001",
    first_name     = "Jane",
    last_name      = "Doe",
    dob            = date(1980, 5, 15),
    gender         = "Female",
    cancer_type    = "Breast Cancer",
    cancer_stage   = "II",
    diagnosis_date = date(2024, 1, 10),
))
print(f"Created: {patient}")

# Test 4 — fetch all patients
print("\n── GET PATIENTS ──")
patients = get_patients(db)
print(f"Total patients: {len(patients)}")

db.close()