-- ============================================================
--  OncoTrack — MySQL Schema
--  Run this first: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS oncotrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE oncotrack;

-- ── Users (clinicians / admins) ─────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(64)  NOT NULL UNIQUE,
    email         VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role          ENUM('admin', 'oncologist', 'nurse', 'viewer') NOT NULL DEFAULT 'viewer',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Patients ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    mrn              VARCHAR(16)  NOT NULL UNIQUE,   -- Medical Record Number
    first_name       VARCHAR(64)  NOT NULL,
    last_name        VARCHAR(64)  NOT NULL,
    dob              DATE         NOT NULL,
    gender           ENUM('Male','Female','Other','Prefer not to say') NOT NULL,
    ethnicity        VARCHAR(64),
    phone            VARCHAR(20),
    email            VARCHAR(128),
    address          TEXT,
    -- Oncology-specific
    cancer_type      VARCHAR(128) NOT NULL,
    cancer_stage     ENUM('I','II','III','IV','Unknown') NOT NULL DEFAULT 'Unknown',
    diagnosis_date   DATE         NOT NULL,
    primary_site     VARCHAR(128),
    histology        VARCHAR(128),
    status           ENUM('Active','Remission','Deceased','Lost to Follow-up') NOT NULL DEFAULT 'Active',
    -- Admin
    created_by       INT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ── Lab Results ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lab_results (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT         NOT NULL,
    test_name       VARCHAR(128) NOT NULL,
    test_category   ENUM('CBC','Tumor Marker','Metabolic Panel','Coagulation','Urinalysis','Other') NOT NULL,
    value           DECIMAL(10,3) NOT NULL,
    unit            VARCHAR(32)  NOT NULL,
    reference_low   DECIMAL(10,3),
    reference_high  DECIMAL(10,3),
    is_abnormal     BOOLEAN GENERATED ALWAYS AS (
                        value < reference_low OR value > reference_high
                    ) STORED,
    collected_at    DATETIME     NOT NULL,
    resulted_at     DATETIME,
    notes           TEXT,
    ordered_by      INT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)  REFERENCES patients(id)  ON DELETE CASCADE,
    FOREIGN KEY (ordered_by)  REFERENCES users(id)     ON DELETE SET NULL,
    INDEX idx_patient_test (patient_id, test_name),
    INDEX idx_collected    (collected_at)
);

-- ── Treatments ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS treatments (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    patient_id        INT          NOT NULL,
    treatment_type    ENUM('Chemotherapy','Radiation','Surgery','Immunotherapy',
                          'Targeted Therapy','Hormone Therapy','Palliative','Other') NOT NULL,
    protocol_name     VARCHAR(128),
    drug_regimen      TEXT,
    start_date        DATE         NOT NULL,
    end_date          DATE,
    cycle_number      INT,
    total_cycles      INT,
    dose_mg           DECIMAL(8,2),
    dose_unit         VARCHAR(32)  DEFAULT 'mg',
    frequency         VARCHAR(64),
    response          ENUM('Complete Response','Partial Response','Stable Disease',
                           'Progressive Disease','Unknown') DEFAULT 'Unknown',
    toxicity_grade    TINYINT CHECK (toxicity_grade BETWEEN 0 AND 5),
    notes             TEXT,
    administered_by   INT,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)      REFERENCES patients(id)  ON DELETE CASCADE,
    FOREIGN KEY (administered_by) REFERENCES users(id)     ON DELETE SET NULL,
    INDEX idx_patient_treatment (patient_id, treatment_type)
);

-- ── Visits ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS visits (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT          NOT NULL,
    visit_date      DATETIME     NOT NULL,
    visit_type      ENUM('Initial Consult','Follow-up','Chemo Session',
                         'Radiation Session','Urgent','Telehealth') NOT NULL,
    attending_id    INT,
    weight_kg       DECIMAL(5,2),
    height_cm       DECIMAL(5,2),
    ecog_score      TINYINT CHECK (ecog_score BETWEEN 0 AND 5),  -- Performance status
    chief_complaint TEXT,
    assessment      TEXT,
    plan            TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)  REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (attending_id) REFERENCES users(id)   ON DELETE SET NULL
);

-- ── Audit Logs ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT,
    action       VARCHAR(64)   NOT NULL,   -- e.g. READ, CREATE, UPDATE, DELETE
    resource     VARCHAR(64)   NOT NULL,   -- e.g. patients, lab_results
    resource_id  INT,
    endpoint     VARCHAR(256),
    ip_address   VARCHAR(45),
    status_code  SMALLINT,
    detail       JSON,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_action  (user_id, action),
    INDEX idx_resource     (resource, resource_id),
    INDEX idx_created      (created_at)
);

-- ── Useful views ────────────────────────────────────────────

-- Latest lab result per test per patient
CREATE OR REPLACE VIEW v_latest_labs AS
SELECT l.*
FROM lab_results l
INNER JOIN (
    SELECT patient_id, test_name, MAX(collected_at) AS max_date
    FROM lab_results
    GROUP BY patient_id, test_name
) latest ON l.patient_id = latest.patient_id
         AND l.test_name  = latest.test_name
         AND l.collected_at = latest.max_date;

-- Patient summary (used by dashboard)
CREATE OR REPLACE VIEW v_patient_summary AS
SELECT
    p.id,
    p.mrn,
    CONCAT(p.first_name, ' ', p.last_name)  AS full_name,
    TIMESTAMPDIFF(YEAR, p.dob, CURDATE())   AS age,
    p.gender,
    p.cancer_type,
    p.cancer_stage,
    p.diagnosis_date,
    p.status,
    COUNT(DISTINCT t.id)  AS total_treatments,
    COUNT(DISTINCT l.id)  AS total_labs,
    COUNT(DISTINCT v.id)  AS total_visits,
    MAX(v.visit_date)     AS last_visit
FROM patients p
LEFT JOIN treatments t ON t.patient_id = p.id
LEFT JOIN lab_results l ON l.patient_id = p.id
LEFT JOIN visits      v ON v.patient_id = p.id
GROUP BY p.id;