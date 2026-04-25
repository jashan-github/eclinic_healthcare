"""
Role feature permission service
Manages admin-controlled tab/feature visibility for doctor and staff roles.
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.role_feature_permission import (
    RoleFeaturePermission,
    ROLE_FEATURES,
    DOCTOR_FEATURES,
    STAFF_FEATURES,
)
from app.core.security import UserRole


class RolePermissionService:
    """Service for role feature permissions (doctor/staff tab visibility)."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> Dict[str, Dict[str, bool]]:
        """
        Get all role permissions for admin UI.
        Returns { "doctor": { "appointments": true, ... }, "staff": { "patients": true, "payments": true } }.
        """
        rows = (
            self.db.query(RoleFeaturePermission)
            .filter(RoleFeaturePermission.deleted_at.is_(None))
            .all()
        )
        result: Dict[str, Dict[str, bool]] = {"doctor": {}, "staff": {}}
        for r in rows:
            if r.role_name not in result:
                result[r.role_name] = {}
            result[r.role_name][r.feature_key] = r.enabled
        # Ensure all defined features exist (default True if missing)
        for role_name, features in ROLE_FEATURES.items():
            if role_name not in result:
                result[role_name] = {}
            for fk in features:
                result[role_name].setdefault(fk, True)
        # Return each role's permissions in ascending order by permission (feature) name
        return {
            role_name: dict(sorted(perms.items(), key=lambda x: x[0].lower()))
            for role_name, perms in result.items()
        }

    def get_for_role(self, role_name: str) -> Dict[str, bool]:
        """
        Get permission map for a role. Only returns keys that are valid for that role.
        """
        valid = ROLE_FEATURES.get(role_name, [])
        rows = (
            self.db.query(RoleFeaturePermission)
            .filter(
                RoleFeaturePermission.role_name == role_name,
                RoleFeaturePermission.deleted_at.is_(None),
            )
            .all()
        )
        result = {fk: True for fk in valid}
        for r in rows:
            if r.feature_key in valid:
                result[r.feature_key] = r.enabled
        return result

    def get_for_current_user(self, role: UserRole) -> Optional[Dict[str, bool]]:
        """
        Get effective permissions for current user's role.
        Returns None for non-doctor/non-staff (e.g. admin sees all in UI; no tab filtering).
        """
        role_name = self._role_to_permission_role(role)
        if role_name is None:
            return None
        return self.get_for_role(role_name)

    def _role_to_permission_role(self, role: UserRole) -> Optional[str]:
        """Map UserRole to role_name used in role_feature_permissions."""
        if role == UserRole.DOCTOR:
            return "doctor"
        if role == UserRole.STAFF or role == UserRole.RECEPTIONIST or role == UserRole.NURSE:
            return "staff"
        return None

    def update_bulk(
        self,
        payload: Dict[str, Dict[str, bool]],
    ) -> Dict[str, Dict[str, bool]]:
        """
        Update permissions from admin payload: { "doctor": { "appointments": true, ... }, "staff": { ... } }.
        Only updates roles and features that are defined in ROLE_FEATURES.
        """
        for role_name, features_dict in payload.items():
            if role_name not in ROLE_FEATURES:
                continue
            valid_features = ROLE_FEATURES[role_name]
            for feature_key, enabled in features_dict.items():
                if feature_key not in valid_features:
                    continue
                row = (
                    self.db.query(RoleFeaturePermission)
                    .filter(
                        RoleFeaturePermission.role_name == role_name,
                        RoleFeaturePermission.feature_key == feature_key,
                        RoleFeaturePermission.deleted_at.is_(None),
                    )
                    .first()
                )
                if row:
                    row.enabled = bool(enabled)
                else:
                    self.db.add(
                        RoleFeaturePermission(
                            role_name=role_name,
                            feature_key=feature_key,
                            enabled=bool(enabled),
                        )
                    )
        self.db.commit()
        return self.get_all()

    @staticmethod
    def doctor_features() -> List[str]:
        return list(DOCTOR_FEATURES)

    @staticmethod
    def staff_features() -> List[str]:
        return list(STAFF_FEATURES)
