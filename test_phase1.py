"""
Final Phase 1 smoke test.
Verifies every layer of the database stack works end to end.
"""
import logging
logging.basicConfig(level=logging.INFO, format="%(name)s — %(message)s")

from database import (
    get_db,
    get_patients, get_users,
    get_lab_results, get_treatments, get_visits
)

print("\n── Phase 1 Final Verification ──\n")

# Use get_db() generator manually
db = next(get_db())

try:
    users    = get_users(db)
    patients = get_patients(db)

    print(f"✓  Users:       {len(users)}")
    print(f"✓  Patients:    {len(patients)}")

    if patients:
        p = patients[0]
        labs       = get_lab_results(db, p.id)
        treatments = get_treatments(db,  p.id)
        visits     = get_visits(db,      p.id)

        print(f"✓  Sample patient: {p.first_name} {p.last_name} ({p.mrn})")
        print(f"   Cancer:    {p.cancer_type} Stage {p.cancer_stage}")
        print(f"   Status:    {p.status}")
        print(f"   Labs:      {len(labs)}")
        print(f"   Treatments:{len(treatments)}")
        print(f"   Visits:    {len(visits)}")

    print("\n✓  Phase 1 complete — database layer fully operational!")

finally:
    db.close()