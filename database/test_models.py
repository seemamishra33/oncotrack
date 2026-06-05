#from database.Connection import engine
from database.Models import Base, User, Patient, LabResult, Treatment, Visit, AuditLog

# This just imports all models and confirms no errors
print("Models loaded:")
for model in [User, Patient, LabResult, Treatment, Visit, AuditLog]:
    print(f"  ✓  {model.__name__} → table: {model.__tablename__}")