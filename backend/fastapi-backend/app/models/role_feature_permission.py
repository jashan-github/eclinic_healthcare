"""
Role feature permission model
Stores which tabs/features are enabled per role (doctor, staff) for admin-controlled visibility.
"""

from sqlalchemy import Column, String, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


# Feature keys per role (for validation and seeding)
DOCTOR_FEATURES = [
    "appointments",
    "patients",
    "payments",
    "requests",
    "webinars",
    "messages",
    "analytics",
    "rx_templates",
]
STAFF_FEATURES = [
    "patients",
    "payments",
]
ROLE_FEATURES = {
    "doctor": DOCTOR_FEATURES,
    "staff": STAFF_FEATURES,
}


class RoleFeaturePermission(BaseModel):
    """
    One row per (role_name, feature_key). Admin toggles enabled to show/hide tabs for that role.
    """

    __tablename__ = "role_feature_permissions"

    role_name = Column(
        String(32),
        nullable=False,
        index=True,
        comment="Role: doctor, staff",
    )
    feature_key = Column(
        String(64),
        nullable=False,
        index=True,
        comment="Feature key: appointments, patients, payments, etc.",
    )
    enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="If true, tab/feature is visible for this role",
    )

    __table_args__ = (
        UniqueConstraint(
            "role_name",
            "feature_key",
            name="role_feature_permissions_role_feature_unique",
        ),
        Index("role_feature_permissions_role_name_index", "role_name"),
    )

    def __repr__(self):
        return f"<RoleFeaturePermission(role={self.role_name}, feature={self.feature_key}, enabled={self.enabled})>"
