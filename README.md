# OncoTrack

An oncology patient data management dashboard — built as a portfolio project demonstrating a full-stack Python architecture.

> **Note:** All patient data is 100% synthetic, generated with [Faker](https://faker.readthedocs.io/) for demonstration purposes only. No real patient information is used anywhere in this project.

---

## Tech Stack

| Layer        | Technology |
|--------------|------------|
| Backend API  | FastAPI |
| Frontend     | Streamlit |
| Database     | MySQL |
| ORM          | SQLAlchemy |
| Validation   | Pydantic |
| Fake Data    | Faker |
| Auth         | Simple username/password (demo) |

**Python concepts demonstrated:** generators, decorators, logging, middleware, dependency injection, type hints.

---

## Project Structure

```
oncotrack/
├── database/
│   ├── schema.sql          # MySQL tables + views
│   ├── Connection.py        # SQLAlchemy engine + get_db() generator
│   ├── Models.py             # ORM models (6 tables)
│   ├── Schemas.py            # Pydantic validation schemas
│   ├── Crud.py               # CRUD operations + @log_db_operation decorator
│   ├── Seed_data.py          # Faker-based synthetic data seeder
│   └── __init__.py
├── api/
│   ├── main.py               # FastAPI app entry point
│   ├── auth/
│   │   ├── auth.py           # Authentication logic
│   │   └── router.py         # /auth endpoints
│   ├── routers/
│   │   ├── patients.py       # /api/patients endpoints
│   │   ├── labs.py            # /api/labs endpoints
│   │   ├── treatments.py      # /api/treatments endpoints
│   │   └── visits.py          # /api/visits endpoints
│   └── middleware/
│       └── audit.py           # Automatic audit logging middleware
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Database Schema

Six tables, all linked to a central `patients` table:

```
users  ───┐
          ├──> patients ──> lab_results
          │              ├─> treatments
          │              └─> visits
          └──> audit_logs
```

Two views are included for reporting:
- `v_latest_labs` — most recent result per test per patient
- `v_patient_summary` — dashboard-ready patient summary with age, totals, and last visit

---

## Demo Credentials

| Role        | Username    | Password  | Access                        |
|-------------|-------------|-----------|--------------------------------|
| Admin       | admin       | admin123  | Full access                   |
| Oncologist  | dr_smith    | demo123   | Patient data + treatments     |
| Nurse       | nurse_jane  | demo123   | Patient data + visits         |
| Viewer      | viewer1     | demo123   | Read-only access               |

> This is a portfolio demo — passwords are stored in plain text for simplicity. A production system would use bcrypt password hashing and JWT-based authentication (see [Security Notes](#security-notes) below).

---

## Running Locally

### 1. Clone the repo
```bash
git clone git@github.com:seemamishra33/oncotrack.git
cd oncotrack
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and set your MySQL credentials.

### 5. Create the database
```bash
mysql -u root -p < database/schema.sql
```

### 6. Seed with synthetic data
```bash
python database/Seed_data.py
```

This creates:
- 10 users (including 4 demo accounts above)
- 50 patients with realistic oncology profiles
- ~250 lab results
- ~100 treatments
- ~175 visits

### 7. Start the API server
```bash
uvicorn api.main:app --reload --port 8000
```

Visit:
- API root: `http://localhost:8000/`
- Interactive docs (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 8. Start the Streamlit dashboard
```bash
streamlit run streamlit/app.py
```
Visit `http://localhost:8501`

---

## API Overview

### Authentication
| Method | Endpoint              | Description                  |
|--------|-----------------------|-------------------------------|
| POST   | `/auth/login`         | Login with username/password |
| GET    | `/auth/me/{username}` | Get user profile              |

### Patients
| Method | Endpoint                        | Description                       |
|--------|----------------------------------|------------------------------------|
| GET    | `/api/patients`                  | List patients (filter by status/stage, pagination) |
| GET    | `/api/patients/{id}`             | Get one patient                   |
| GET    | `/api/patients/mrn/{mrn}`        | Get patient by MRN                |
| POST   | `/api/patients`                  | Create patient                    |
| PATCH  | `/api/patients/{id}`             | Update patient (partial)          |
| DELETE | `/api/patients/{id}`             | Delete patient (cascades)         |
| GET    | `/api/patients/{id}/summary`     | Full patient summary              |

### Lab Results
| Method | Endpoint                                   | Description                  |
|--------|----------------------------------------------|-------------------------------|
| GET    | `/api/labs/patient/{patient_id}`              | List labs for a patient        |
| GET    | `/api/labs/patient/{patient_id}/abnormal`     | Abnormal results only          |
| POST   | `/api/labs`                                    | Create lab result              |
| PATCH  | `/api/labs/{lab_id}`                           | Update lab result              |

### Treatments
| Method | Endpoint                                | Description                       |
|--------|--------------------------------------------|-------------------------------------|
| GET    | `/api/treatments/patient/{patient_id}`      | List treatments (filter by type)   |
| POST   | `/api/treatments`                            | Create treatment                  |
| PATCH  | `/api/treatments/{treatment_id}`             | Update treatment                  |

### Visits
| Method | Endpoint                          | Description                       |
|--------|---------------------------------------|--------------------------------------|
| GET    | `/api/visits/patient/{patient_id}`     | List visits (filter by type)        |
| POST   | `/api/visits`                           | Create visit                       |
| PATCH  | `/api/visits/{visit_id}`                | Update visit                       |

---

## Audit Logging

Every API request is automatically logged via `AuditMiddleware` — no developer effort needed in individual routes. Each entry records:

- HTTP method → mapped to `READ` / `CREATE` / `UPDATE` / `DELETE`
- Resource accessed (`patients`, `labs`, `treatments`, `visits`, `auth`)
- Endpoint path
- Response status code
- Timestamp

```sql
SELECT action, resource, endpoint, status_code, created_at
FROM audit_logs
ORDER BY created_at DESC
LIMIT 10;
```

---

## Security Notes

This is a **portfolio demo project**. The following simplifications were made intentionally:

| Demo Implementation              | Production Equivalent                          |
|-----------------------------------|--------------------------------------------------|
| Plain-text password comparison    | bcrypt password hashing                          |
| No session tokens                 | JWT tokens with expiry + refresh                 |
| Public demo credentials           | Per-user accounts, no shared credentials         |
| No rate limiting                  | Rate limiting on `/auth/login`                   |
| CORS allows localhost only        | Restricted to production domain                  |

What **is** production-ready in this project:

- SQL injection prevention via SQLAlchemy ORM (parameterized queries)
- Environment variables for all secrets (`.env`, never committed)
- Full audit trail of all data access (HIPAA-style)
- Role-based fields in the data model (`admin`, `oncologist`, `nurse`, `viewer`)
- Input validation on every endpoint via Pydantic
- Structured logging with timing on every database operation

---

## Python Concepts Demonstrated

| Concept     | Where                                                        |
|-------------|----------------------------------------------------------------|
| Generators  | `get_db()` in `Connection.py` — yields a session, cleans up after |
| Decorators  | `@log_db_operation` in `Crud.py` — wraps every CRUD function with logging |
| Logging     | Structured logs throughout `database/` and `api/`              |
| Middleware  | `AuditMiddleware` — logs every request automatically            |
| Dependency Injection | `Depends(get_db)` in every route                        |
| Pydantic validation | Custom `@field_validator` for MRN format, toxicity grade, ECOG score |

---

## License

This project is for portfolio/demonstration purposes.
