"""
Seed_data.py
============
Populates the database with realistic fake data for development
and portfolio demonstration.

CONCEPTS DEMONSTRATED:
    - Faker library     : generates realistic fake data
    - Generators        : used via get_db() session management
    - Logging           : tracks seeding progress
    - Python random     : weighted choices for realistic distributions
"""

import logging
import random
from datetime import datetime, timedelta, date

from faker import Faker
from sqlalchemy.orm import Session

from database.Connection import SessionLocal
from database.Models import User, Patient, LabResult, Treatment, Visit, AuditLog

# ── Setup ─────────────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger("oncotrack.seed")
fake   = Faker()
Faker.seed(42)    # fixed seed = same data every run, great for demos
random.seed(42)


# ── Realistic oncology data pools ─────────────────────────────
CANCER_TYPES = [
    "Breast Cancer", "Lung Cancer", "Colorectal Cancer",
    "Prostate Cancer", "Lymphoma", "Leukemia",
    "Melanoma", "Pancreatic Cancer", "Ovarian Cancer", "Bladder Cancer"
]

CANCER_STAGES = ["I", "II", "III", "IV", "Unknown"]
STAGE_WEIGHTS = [20, 30, 25, 20, 5]   # Stage II most common

TREATMENT_TYPES = [
    "Chemotherapy", "Radiation", "Surgery",
    "Immunotherapy", "Targeted Therapy", "Hormone Therapy",
    "Palliative", "Other"
]

DRUG_REGIMENS = [
    "FOLFOX", "FOLFIRI", "AC-T", "R-CHOP",
    "Pembrolizumab", "Trastuzumab", "Carboplatin/Paclitaxel"
]

VISIT_TYPES = [
    "Initial Consult", "Follow-up", "Chemo Session",
    "Radiation Session", "Urgent", "Telehealth"
]

LAB_TESTS = [
    # (test_name, category, unit, low, high)
    ("WBC",          "CBC",           "10^3/uL",  4.5,   11.0),
    ("RBC",          "CBC",           "10^6/uL",  4.2,    5.9),
    ("Hemoglobin",   "CBC",           "g/dL",     12.0,  17.5),
    ("Platelets",    "CBC",           "10^3/uL", 150.0, 400.0),
    ("CA-125",       "Tumor Marker",  "U/mL",      0.0,   35.0),
    ("PSA",          "Tumor Marker",  "ng/mL",     0.0,    4.0),
    ("CEA",          "Tumor Marker",  "ng/mL",     0.0,    3.0),
    ("Creatinine",   "Metabolic Panel","mg/dL",    0.6,    1.2),
    ("ALT",          "Metabolic Panel","U/L",       7.0,   56.0),
    ("Glucose",      "Metabolic Panel","mg/dL",    70.0,  100.0),
]

ROLES = ["oncologist", "nurse", "viewer"]

PATIENT_STATUSES  = ["Active", "Remission", "Deceased", "Lost to Follow-up"]
STATUS_WEIGHTS    = [60, 25, 10, 5]   # mostly active patients


# ╔══════════════════════════════════════════════════════════════╗
# ║  SEEDER FUNCTIONS                                            ║
# ╚══════════════════════════════════════════════════════════════╝

def seed_users(db: Session, count: int = 10) -> list[User]:
    """Create demo users with plain text passwords."""
    logger.info(f"Seeding {count} users...")
    users = []

    # Demo users — plain text passwords for demo project
    demo_users = [
        {
            "username"      : "admin",
            "email"         : "admin@oncotrack.com",
            "password_hash" : "admin123",   # plain text for demo
            "role"          : "admin",
        },
        {
            "username"      : "dr_smith",
            "email"         : "dr.smith@oncotrack.com",
            "password_hash" : "demo123",
            "role"          : "oncologist",
        },
        {
            "username"      : "nurse_jane",
            "email"         : "jane@oncotrack.com",
            "password_hash" : "demo123",
            "role"          : "nurse",
        },
        {
            "username"      : "viewer1",
            "email"         : "viewer@oncotrack.com",
            "password_hash" : "demo123",
            "role"          : "viewer",
        },
    ]

    for demo in demo_users:
        user = User(
            username      = demo["username"],
            email         = demo["email"],
            password_hash = demo["password_hash"],
            role          = demo["role"],
            is_active     = True,
        )
        db.add(user)
        users.append(user)

    # Random clinical staff
    for i in range(count - len(demo_users)):
        user = User(
            username      = fake.unique.user_name(),
            email         = fake.unique.email(),
            password_hash = "demo123",
            role          = random.choice(ROLES),
            is_active     = random.choices([True, False], weights=[90, 10])[0],
        )
        db.add(user)
        users.append(user)

    db.commit()
    logger.info(f"  created {len(users)} users")
    return users

def seed_patients(db: Session, users: list[User], count: int = 50) -> list[Patient]:
    """Create fake patients with realistic oncology data."""
    logger.info(f"Seeding {count} patients...")
    patients = []

    for i in range(count):
        # Generate a diagnosis date in the last 5 years
        diagnosis_date = fake.date_between(
            start_date = "-5y",
            end_date   = "today"
        )

        patient = Patient(
            mrn            = f"MRN{str(i + 1).zfill(5)}",   # MRN00001, MRN00002...
            first_name     = fake.first_name(),
            last_name      = fake.last_name(),
            dob            = fake.date_of_birth(minimum_age=18, maximum_age=90),
            gender         = random.choice(["Male", "Female", "Other"]),
            ethnicity      = random.choice(["Caucasian", "Hispanic", "Asian",
                                            "African American", "Other", None]),
            phone          = fake.phone_number()[:20],
            email          = fake.email(),
            address        = fake.address(),
            cancer_type    = random.choice(CANCER_TYPES),
            cancer_stage   = random.choices(CANCER_STAGES, weights=STAGE_WEIGHTS)[0],
            diagnosis_date = diagnosis_date,
            primary_site   = fake.body_part() if hasattr(fake, 'body_part') else None,
            histology      = random.choice(["Adenocarcinoma", "Squamous Cell",
                                            "Large Cell", "Small Cell", None]),
            status         = random.choices(PATIENT_STATUSES, weights=STATUS_WEIGHTS)[0],
            created_by     = random.choice(users).id,
        )
        db.add(patient)
        patients.append(patient)

    db.commit()
    logger.info(f"  created {len(patients)} patients")
    return patients


def seed_lab_results(db: Session, patients: list[Patient], labs_per_patient: int = 5):
    """Create fake lab results for each patient."""
    logger.info(f"Seeding lab results ({labs_per_patient} per patient)...")
    total = 0

    for patient in patients:
        for _ in range(labs_per_patient):
            # Pick a random test from our pool
            test = random.choice(LAB_TESTS)
            test_name, category, unit, ref_low, ref_high = test

            # Occasionally generate abnormal values for realism
            if random.random() < 0.3:   # 30% chance of abnormal
                value = round(random.uniform(ref_high, ref_high * 1.5), 3)
            else:
                value = round(random.uniform(ref_low, ref_high), 3)

            lab = LabResult(
                patient_id     = patient.id,
                test_name      = test_name,
                test_category  = category,
                value          = value,
                unit           = unit,
                reference_low  = ref_low,
                reference_high = ref_high,
                collected_at   = fake.date_time_between(
                                     start_date = "-2y",
                                     end_date   = "now"
                                 ),
                notes          = None,
            )
            db.add(lab)
            total += 1

    db.commit()
    logger.info(f"  created {total} lab results")


def seed_treatments(db: Session, patients: list[Patient]):
    """Create 1-3 treatments per patient."""
    logger.info("Seeding treatments...")
    total = 0

    for patient in patients:
        num_treatments = random.randint(1, 3)
        for _ in range(num_treatments):
            start = fake.date_between(
                start_date = patient.diagnosis_date,
                end_date   = "today"
            )
            treatment = Treatment(
                patient_id      = patient.id,
                treatment_type  = random.choice(TREATMENT_TYPES),
                protocol_name   = random.choice(["Protocol A", "Protocol B", None]),
                drug_regimen    = random.choice(DRUG_REGIMENS + [None]),
                start_date      = start,
                end_date        = start + timedelta(days=random.randint(30, 180)),
                cycle_number    = random.randint(1, 6),
                total_cycles    = random.randint(6, 12),
                dose_mg         = round(random.uniform(50, 500), 2),
                frequency       = random.choice(["Daily", "Weekly",
                                                 "Every 3 weeks", "Monthly"]),
                response        = random.choice([
                                    "Complete Response", "Partial Response",
                                    "Stable Disease", "Progressive Disease", "Unknown"
                                  ]),
                toxicity_grade  = random.randint(0, 4),
                notes           = fake.sentence() if random.random() < 0.3 else None,
            )
            db.add(treatment)
            total += 1

    db.commit()
    logger.info(f"  created {total} treatments")


def seed_visits(db: Session, patients: list[Patient], users: list[User]):
    """Create 2-5 visits per patient."""
    logger.info("Seeding visits...")
    total = 0

    for patient in patients:
        num_visits = random.randint(2, 5)
        for _ in range(num_visits):
            visit = Visit(
                patient_id      = patient.id,
                visit_date      = fake.date_time_between(
                                      start_date = "-2y",
                                      end_date   = "now"
                                  ),
                visit_type      = random.choice(VISIT_TYPES),
                attending_id    = random.choice(users).id,
                weight_kg       = round(random.uniform(45, 120), 2),
                height_cm       = round(random.uniform(150, 195), 2),
                ecog_score      = random.randint(0, 4),
                chief_complaint = fake.sentence(),
                assessment      = fake.paragraph(),
                plan            = fake.sentence(),
            )
            db.add(visit)
            total += 1

    db.commit()
    logger.info(f"  created {total} visits")


# ╔══════════════════════════════════════════════════════════════╗
# ║  MAIN — run everything in order                              ║
# ╚══════════════════════════════════════════════════════════════╝

def run_seed(clear_existing: bool = False):
    """
    Main seeder function.
    Set clear_existing=True to wipe and reseed from scratch.
    """
    db = SessionLocal()

    try:
        if clear_existing:
            logger.info("Clearing existing data...")
            # Delete in reverse order to respect foreign keys
            db.query(AuditLog).delete()
            db.query(Visit).delete()
            db.query(Treatment).delete()
            db.query(LabResult).delete()
            db.query(Patient).delete()
            db.query(User).delete()
            db.commit()
            logger.info("  cleared all tables")

        # Check if already seeded
        existing = db.query(User).count()
        if existing > 0 and not clear_existing:
            logger.info(f"Database already has {existing} users — skipping seed.")
            logger.info("Run with clear_existing=True to reseed.")
            return

        # Seed in order — parents before children
        users    = seed_users(db,     count=10)
        patients = seed_patients(db,  users=users,    count=50)
        seed_lab_results(db,  patients=patients, labs_per_patient=5)
        seed_treatments(db,   patients=patients)
        seed_visits(db,       patients=patients, users=users)

        logger.info("Seed complete!")
        logger.info(f"  Users:       {db.query(User).count()}")
        logger.info(f"  Patients:    {db.query(Patient).count()}")
        logger.info(f"  Lab Results: {db.query(LabResult).count()}")
        logger.info(f"  Treatments:  {db.query(Treatment).count()}")
        logger.info(f"  Visits:      {db.query(Visit).count()}")

    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed(clear_existing=True)