-- ============================================================================
-- 1. USERS, AUTHENTICATION, PAIRING & DISPLAY SETTINGS
-- ============================================================================

CREATE TABLE users (
    id                      UUID PRIMARY KEY,
    role                    VARCHAR(20) NOT NULL CHECK (role IN ('patient', 'caregiver')),
    full_name               VARCHAR(150) NOT NULL,
    email                   VARCHAR(255) UNIQUE,
    password_hash           TEXT, -- NULL for caregiver-created patient accounts
    auth_provider           VARCHAR(30) NOT NULL DEFAULT 'local',
    arrangement             VARCHAR(30) NOT NULL DEFAULT 'patient-managed'
                            CHECK (arrangement IN ('patient-managed', 'caregiver-created')),
    created_by_user_id      UUID REFERENCES users(id) ON DELETE SET NULL,
    text_size               VARCHAR(20) NOT NULL DEFAULT 'medium'
                            CHECK (text_size IN ('small', 'medium', 'large', 'extra_large')),
    high_contrast           BOOLEAN NOT NULL DEFAULT FALSE,
    timezone                VARCHAR(64) NOT NULL DEFAULT 'UTC',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_caregiver_created_no_password CHECK (
        arrangement <> 'caregiver-created' OR password_hash IS NULL
    )
);

CREATE TABLE pairing_codes (
    id                      UUID PRIMARY KEY,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by_user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash               TEXT NOT NULL,
    expires_at              TIMESTAMPTZ NOT NULL,
    used_at                 TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE password_reset_codes (
    id                      UUID PRIMARY KEY,
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash               TEXT NOT NULL,
    expires_at              TIMESTAMPTZ NOT NULL,
    used_at                 TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. CAREGIVER LINKS, PER-SECTION PERMISSIONS & NOTIFICATION PREFERENCES
-- ============================================================================

CREATE TABLE caregiver_links (
    id                      UUID PRIMARY KEY,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    caregiver_id            UUID REFERENCES users(id) ON DELETE SET NULL,
    invited_email           VARCHAR(255),
    arrangement             VARCHAR(30) NOT NULL
                            CHECK (arrangement IN ('patient-managed', 'caregiver-created')),
    status                  VARCHAR(20) NOT NULL
                            CHECK (status IN (
                                'pending', 'active', 'declined',
                                'cancelled', 'expired', 'revoked', 'removed'
                            )),
    expires_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE section_permissions (
    id                      UUID PRIMARY KEY,
    link_id                 UUID NOT NULL REFERENCES caregiver_links(id) ON DELETE CASCADE,
    section                 VARCHAR(30) NOT NULL
                            CHECK (section IN (
                                'medicines', 'allergies', 'appointments',
                                'health_history', 'emergency_profile'
                            )),
    can_view                BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit                BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (link_id, section),
    CONSTRAINT chk_edit_requires_view CHECK (can_edit = FALSE OR can_view = TRUE)
);

CREATE TABLE notification_settings (
    id                      UUID PRIMARY KEY,
    link_id                 UUID NOT NULL REFERENCES caregiver_links(id) ON DELETE CASCADE,
    notify_missed_dose      BOOLEAN NOT NULL DEFAULT TRUE,
    notify_low_stock        BOOLEAN NOT NULL DEFAULT TRUE,
    notify_appointments     BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (link_id)
);

-- ============================================================================
-- 3. PERSONAL HEALTH WALLET (MEDICINES, ALLERGIES, APPOINTMENTS, HISTORY, EMERGENCY)
-- ============================================================================

CREATE TABLE medicines (
    id                      UUID PRIMARY KEY,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by_user_id      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name                    VARCHAR(200) NOT NULL,
    dosage                  VARCHAR(100),
    instructions            TEXT,
    quantity_remaining      NUMERIC(10, 2),
    low_stock_threshold     NUMERIC(10, 2),
    source                  VARCHAR(20) NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual', 'ocr')),
    requires_ocr_review     BOOLEAN NOT NULL DEFAULT FALSE,
    prescription_file_key   TEXT, -- Key in private/protected file storage (no public URL)
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE allergies (
    id                      UUID PRIMARY KEY,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by_user_id      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    allergen                VARCHAR(200) NOT NULL,
    reaction                TEXT,
    source                  VARCHAR(20) NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual', 'ocr')),
    requires_ocr_review     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE appointments (
    id                      UUID PRIMARY KEY,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by_user_id      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title                   VARCHAR(200) NOT NULL,
    provider_name           VARCHAR(200),
    appointment_at          TIMESTAMPTZ NOT NULL,
    notes                   TEXT,
    source                  VARCHAR(20) NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual', 'ocr')),
    requires_ocr_review     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE health_history_entries (
    id                      UUID PRIMARY KEY,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by_user_id      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title                   VARCHAR(200) NOT NULL,
    details                 TEXT,
    source                  VARCHAR(20) NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual', 'ocr')),
    requires_ocr_review     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE emergency_profiles (
    patient_id              UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    blood_type              VARCHAR(20),
    emergency_contact_name  VARCHAR(150),
    emergency_contact_phone VARCHAR(50),
    medical_notes           TEXT,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. MEDICATION REMINDERS & SCHEDULED DOSES
-- ============================================================================

CREATE TABLE reminder_schedules (
    id                      UUID PRIMARY KEY,
    medicine_id             UUID NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    time_of_day             TIME NOT NULL,
    days_of_week            VARCHAR(50) NOT NULL, -- e.g. MON,TUE,WED,THU,FRI,SAT,SUN or DAILY
    paused                  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE scheduled_doses (
    id                      UUID PRIMARY KEY,
    schedule_id             UUID NOT NULL REFERENCES reminder_schedules(id) ON DELETE CASCADE,
    medicine_id             UUID NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_for           TIMESTAMPTZ NOT NULL,
    status                  VARCHAR(20) NOT NULL DEFAULT 'not_confirmed'
                            CHECK (status IN ('taken', 'skipped', 'not_confirmed')),
    late                    BOOLEAN NOT NULL DEFAULT FALSE,
    responded_at            TIMESTAMPTZ,
    responded_by_user_id    UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 5. FAMILIAR PERSONS (OFFLINE ON-DEVICE EMBEDDINGS + CONSENT METADATA)
-- ============================================================================

CREATE TABLE familiar_persons (
    id                      UUID PRIMARY KEY,
    patient_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                    VARCHAR(150) NOT NULL,
    relationship            VARCHAR(100),
    consented_by_user_id    UUID REFERENCES users(id) ON DELETE SET NULL,
    enrolled_by_user_id     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    enrolled_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stored_on_device        BOOLEAN NOT NULL DEFAULT TRUE,
    device_synced_at        TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 6. AUDIT LOGS & ACCOUNT DELETION REQUESTS (7-DAY WINDOW)
-- ============================================================================

CREATE TABLE audit_logs (
    id                      UUID PRIMARY KEY,
    actor_user_id           UUID REFERENCES users(id) ON DELETE SET NULL,
    patient_id              UUID REFERENCES users(id) ON DELETE SET NULL,
    action                  VARCHAR(100) NOT NULL,
    target_type             VARCHAR(100),
    target_id               UUID,
    details                 JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE deletion_requests (
    id                      UUID PRIMARY KEY,
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status                  VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'cancelled', 'completed')),
    requested_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scheduled_purge_at      TIMESTAMPTZ NOT NULL, -- requested_at + 7 days
    cancelled_at            TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ
);

-- ============================================================================
-- 7. INDEXES FOR COMMON QUERIES
-- ============================================================================

CREATE INDEX idx_caregiver_links_patient ON caregiver_links(patient_id, status);
CREATE INDEX idx_caregiver_links_caregiver ON caregiver_links(caregiver_id, status);
CREATE INDEX idx_medicines_patient ON medicines(patient_id);
CREATE INDEX idx_allergies_patient ON allergies(patient_id);
CREATE INDEX idx_appointments_patient_time ON appointments(patient_id, appointment_at);
CREATE INDEX idx_health_history_patient ON health_history_entries(patient_id);
CREATE INDEX idx_reminder_schedules_patient ON reminder_schedules(patient_id, paused);
CREATE INDEX idx_scheduled_doses_patient_time ON scheduled_doses(patient_id, scheduled_for, status);
CREATE INDEX idx_familiar_persons_patient ON familiar_persons(patient_id);
CREATE INDEX idx_audit_logs_patient_time ON audit_logs(patient_id, created_at);
CREATE INDEX idx_deletion_requests_user_status ON deletion_requests(user_id, status);