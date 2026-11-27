import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    false,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String(20), nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(Text, nullable=True)
    auth_provider = Column(String(30), nullable=False, default="local", server_default=text("'local'"))
    arrangement = Column(
        String(30),
        nullable=False,
        default="patient-managed",
        server_default=text("'patient-managed'"),
    )
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    text_size = Column(String(20), nullable=False, default="medium", server_default=text("'medium'"))
    high_contrast = Column(Boolean, nullable=False, default=False, server_default=false())
    timezone = Column(String(64), nullable=False, default="UTC", server_default=text("'UTC'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('patient', 'caregiver')", name="chk_users_role"),
        CheckConstraint("arrangement IN ('patient-managed', 'caregiver-created')", name="chk_users_arrangement"),
        CheckConstraint(
            "text_size IN ('small', 'medium', 'large', 'extra_large')",
            name="chk_users_text_size",
        ),
        CheckConstraint(
            "arrangement <> 'caregiver-created' OR password_hash IS NULL",
            name="chk_caregiver_created_no_password",
        ),
    )


class PairingCode(Base):
    __tablename__ = "pairing_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CaregiverLink(Base):
    __tablename__ = "caregiver_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invited_email = Column(String(255), nullable=True)
    arrangement = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("arrangement IN ('patient-managed', 'caregiver-created')", name="chk_links_arrangement"),
        CheckConstraint(
            "status IN ('pending', 'active', 'declined', 'cancelled', 'expired', 'revoked', 'removed')",
            name="chk_links_status",
        ),
        Index("idx_caregiver_links_patient", "patient_id", "status"),
        Index("idx_caregiver_links_caregiver", "caregiver_id", "status"),
    )


class SectionPermission(Base):
    __tablename__ = "section_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link_id = Column(UUID(as_uuid=True), ForeignKey("caregiver_links.id", ondelete="CASCADE"), nullable=False)
    section = Column(String(30), nullable=False)
    can_view = Column(Boolean, nullable=False, default=False, server_default=false())
    can_edit = Column(Boolean, nullable=False, default=False, server_default=false())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("link_id", "section", name="uq_section_permissions_link_section"),
        CheckConstraint(
            "section IN ('medicines', 'allergies', 'appointments', 'health_history', 'emergency_profile')",
            name="chk_section_permissions_section",
        ),
        CheckConstraint("can_edit = FALSE OR can_view = TRUE", name="chk_edit_requires_view"),
    )


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link_id = Column(UUID(as_uuid=True), ForeignKey("caregiver_links.id", ondelete="CASCADE"), nullable=False)
    notify_missed_dose = Column(Boolean, nullable=False, default=True, server_default=true())
    notify_low_stock = Column(Boolean, nullable=False, default=True, server_default=true())
    notify_appointments = Column(Boolean, nullable=False, default=True, server_default=true())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("link_id", name="uq_notification_settings_link_id"),)


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=True)
    instructions = Column(Text, nullable=True)
    quantity_remaining = Column(Numeric(10, 2), nullable=True)
    low_stock_threshold = Column(Numeric(10, 2), nullable=True)
    source = Column(String(20), nullable=False, default="manual", server_default=text("'manual'"))
    requires_ocr_review = Column(Boolean, nullable=False, default=False, server_default=false())
    prescription_file_key = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("source IN ('manual', 'ocr')", name="chk_medicines_source"),
        Index("idx_medicines_patient", "patient_id"),
    )


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    allergen = Column(String(200), nullable=False)
    reaction = Column(Text, nullable=True)
    source = Column(String(20), nullable=False, default="manual", server_default=text("'manual'"))
    requires_ocr_review = Column(Boolean, nullable=False, default=False, server_default=false())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("source IN ('manual', 'ocr')", name="chk_allergies_source"),
        Index("idx_allergies_patient", "patient_id"),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(200), nullable=False)
    provider_name = Column(String(200), nullable=True)
    appointment_at = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)
    source = Column(String(20), nullable=False, default="manual", server_default=text("'manual'"))
    requires_ocr_review = Column(Boolean, nullable=False, default=False, server_default=false())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("source IN ('manual', 'ocr')", name="chk_appointments_source"),
        Index("idx_appointments_patient_time", "patient_id", "appointment_at"),
    )


class HealthHistoryEntry(Base):
    __tablename__ = "health_history_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    source = Column(String(20), nullable=False, default="manual", server_default=text("'manual'"))
    requires_ocr_review = Column(Boolean, nullable=False, default=False, server_default=false())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("source IN ('manual', 'ocr')", name="chk_health_history_source"),
        Index("idx_health_history_patient", "patient_id"),
    )


class EmergencyProfile(Base):
    __tablename__ = "emergency_profiles"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blood_type = Column(String(20), nullable=True)
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    medical_notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ReminderSchedule(Base):
    __tablename__ = "reminder_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    time_of_day = Column(Time, nullable=False)
    days_of_week = Column(String(50), nullable=False)
    paused = Column(Boolean, nullable=False, default=False, server_default=false())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("idx_reminder_schedules_patient", "patient_id", "paused"),)


class ScheduledDose(Base):
    __tablename__ = "scheduled_doses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("reminder_schedules.id", ondelete="CASCADE"), nullable=False)
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="not_confirmed", server_default=text("'not_confirmed'"))
    late = Column(Boolean, nullable=False, default=False, server_default=false())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    responded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('taken', 'skipped', 'not_confirmed')", name="chk_doses_status"),
        Index("idx_scheduled_doses_patient_time", "patient_id", "scheduled_for", "status"),
    )


class FamiliarPerson(Base):
    __tablename__ = "familiar_persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    relationship = Column(String(100), nullable=True)
    consented_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    enrolled_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    stored_on_device = Column(Boolean, nullable=False, default=True, server_default=true())
    device_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("idx_familiar_persons_patient", "patient_id"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (Index("idx_audit_logs_patient_time", "patient_id", "created_at"),)


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default=text("'pending'"))
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    scheduled_purge_at = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'cancelled', 'completed')", name="chk_deletion_status"),
        Index("idx_deletion_requests_user_status", "user_id", "status"),
    )
