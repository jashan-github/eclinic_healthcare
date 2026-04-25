"""
Vital Frequency Service
Business logic for vital frequency management
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, case

from app.models.vital_frequency import VitalFrequency
from app.models.vital_name import VitalName
from app.models.user import User
from app.models.user import Clinic
from app.core.exceptions import NotFoundException, ConflictException, ValidationException
from loguru import logger


class VitalFrequencyService:
    """Service for managing vital frequency rules"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_frequency_rule(
        self,
        patient_id: Optional[UUID] = None,
        clinic_id: Optional[UUID] = None,
        vital_name_id: Optional[UUID] = None
    ) -> Optional[VitalFrequency]:
        """
        Get frequency rule with priority:
        1. Patient-specific + Vital-specific (highest priority)
        2. Patient-specific + All vitals
        3. Clinic-specific + Vital-specific
        4. Clinic-specific + All vitals
        5. Global + Vital-specific
        6. Global + All vitals (lowest priority)
        
        Args:
            patient_id: Patient user ID
            clinic_id: Clinic ID
            vital_name_id: Vital name ID
            
        Returns:
            VitalFrequency object or None
        """
        # Build query with priority order
        query = self.db.query(VitalFrequency).filter(
            and_(
                VitalFrequency.is_active == True,
                VitalFrequency.deleted_at.is_(None)
            )
        )
        
        # Priority 1: Patient-specific + Vital-specific
        if patient_id and vital_name_id:
            rule = query.filter(
                and_(
                    VitalFrequency.patient_id == patient_id,
                    VitalFrequency.vital_name_id == vital_name_id
                )
            ).first()
            if rule:
                return rule
        
        # Priority 2: Patient-specific + All vitals
        if patient_id:
            rule = query.filter(
                and_(
                    VitalFrequency.patient_id == patient_id,
                    VitalFrequency.vital_name_id.is_(None)
                )
            ).first()
            if rule:
                return rule
        
        # Priority 3: Clinic-specific + Vital-specific
        if clinic_id and vital_name_id:
            rule = query.filter(
                and_(
                    VitalFrequency.clinic_id == clinic_id,
                    VitalFrequency.patient_id.is_(None),
                    VitalFrequency.vital_name_id == vital_name_id
                )
            ).first()
            if rule:
                return rule
        
        # Priority 4: Clinic-specific + All vitals
        if clinic_id:
            rule = query.filter(
                and_(
                    VitalFrequency.clinic_id == clinic_id,
                    VitalFrequency.patient_id.is_(None),
                    VitalFrequency.vital_name_id.is_(None)
                )
            ).first()
            if rule:
                return rule
        
        # Priority 5: Global + Vital-specific
        if vital_name_id:
            rule = query.filter(
                and_(
                    VitalFrequency.patient_id.is_(None),
                    VitalFrequency.clinic_id.is_(None),
                    VitalFrequency.vital_name_id == vital_name_id
                )
            ).first()
            if rule:
                return rule
        
        # Priority 6: Global + All vitals
        rule = query.filter(
            and_(
                VitalFrequency.patient_id.is_(None),
                VitalFrequency.clinic_id.is_(None),
                VitalFrequency.vital_name_id.is_(None)
            )
        ).first()
        
        return rule
    
    def get_max_entries_per_day(
        self,
        patient_id: UUID,
        clinic_id: UUID,
        vital_name_id: UUID
    ) -> int:
        """
        Get maximum entries per day for a specific patient, clinic, and vital name
        
        Returns:
            Maximum entries per day (default: 1)
        """
        rule = self.get_frequency_rule(
            patient_id=patient_id,
            clinic_id=clinic_id,
            vital_name_id=vital_name_id
        )
        
        if rule:
            return rule.max_entries_per_day
        
        # Fallback: Check vital_name default
        vital_name = self.db.query(VitalName).filter(
            and_(
                VitalName.id == vital_name_id,
                VitalName.deleted_at.is_(None)
            )
        ).first()
        
        if vital_name and vital_name.max_entries_per_day:
            try:
                return int(vital_name.max_entries_per_day)
            except (ValueError, TypeError):
                pass
        
        # Default
        return 1
    
    def create_frequency_rule(
        self,
        max_entries_per_day: int,
        patient_id: Optional[UUID] = None,
        vital_name_id: Optional[UUID] = None,
        clinic_id: Optional[UUID] = None,
        frequency_type: Optional[str] = "daily",
        times_per_day: Optional[int] = None,
        preferred_times: Optional[List[str]] = None,
        is_active: bool = True
    ) -> VitalFrequency:
        """
        Create a new frequency rule
        
        Args:
            max_entries_per_day: Maximum entries allowed per day
            patient_id: Patient ID (optional)
            vital_name_id: Vital name ID (optional)
            clinic_id: Clinic ID (optional)
            frequency_type: Frequency type
            times_per_day: Number of times per day
            preferred_times: Preferred times list
            is_active: Whether rule is active
            
        Returns:
            Created VitalFrequency object
        """
        # Validate that at least one scope is provided
        if not patient_id and not clinic_id and not vital_name_id:
            raise ValidationException(
                message="At least one scope (patient_id, clinic_id, or vital_name_id) must be provided",
                errors={"scope": ["Cannot create a completely global rule without any scope"]}
            )
        
        # Validate vital_name_id exists if provided
        if vital_name_id:
            vital_name = self.db.query(VitalName).filter(
                and_(
                    VitalName.id == vital_name_id,
                    VitalName.deleted_at.is_(None)
                )
            ).first()
            if not vital_name:
                raise NotFoundException(f"Vital name with ID {vital_name_id} not found")
        
        # Validate patient_id exists if provided
        if patient_id:
            patient = self.db.query(User).filter(
                and_(
                    User.id == patient_id,
                    User.deleted_at.is_(None)
                )
            ).first()
            if not patient:
                raise NotFoundException(f"Patient with ID {patient_id} not found")
        
        # Validate clinic_id exists if provided
        if clinic_id:
            clinic = self.db.query(Clinic).filter(
                and_(
                    Clinic.id == clinic_id,
                    Clinic.deleted_at.is_(None)
                )
            ).first()
            if not clinic:
                raise NotFoundException(f"Clinic with ID {clinic_id} not found")
        
        # Check for duplicate rule
        existing = self.db.query(VitalFrequency).filter(
            and_(
                VitalFrequency.patient_id == (patient_id if patient_id else None),
                VitalFrequency.vital_name_id == (vital_name_id if vital_name_id else None),
                VitalFrequency.clinic_id == (clinic_id if clinic_id else None),
                VitalFrequency.deleted_at.is_(None)
            )
        ).first()
        
        if existing:
            raise ConflictException(
                message="Frequency rule already exists for this scope",
                errors={"scope": ["A frequency rule with this exact scope already exists"]}
            )
        
        # Create new rule
        frequency_rule = VitalFrequency(
            patient_id=patient_id,
            vital_name_id=vital_name_id,
            clinic_id=clinic_id,
            frequency_type=frequency_type or "daily",
            max_entries_per_day=max_entries_per_day,
            times_per_day=times_per_day,
            preferred_times=preferred_times,
            is_active=is_active
        )
        
        self.db.add(frequency_rule)
        self.db.commit()
        self.db.refresh(frequency_rule)
        
        logger.info(f"Created frequency rule: {frequency_rule}")
        
        return frequency_rule
    
    def get_all_frequency_rules(
        self,
        patient_id: Optional[UUID] = None,
        clinic_id: Optional[UUID] = None,
        vital_name_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> List[VitalFrequency]:
        """
        Get all frequency rules with optional filters
        
        Args:
            patient_id: Filter by patient ID
            clinic_id: Filter by clinic ID
            vital_name_id: Filter by vital name ID
            is_active: Filter by active status
            
        Returns:
            List of VitalFrequency objects
        """
        query = self.db.query(VitalFrequency).filter(
            VitalFrequency.deleted_at.is_(None)
        )
        
        if patient_id is not None:
            query = query.filter(VitalFrequency.patient_id == patient_id)
        
        if clinic_id is not None:
            query = query.filter(VitalFrequency.clinic_id == clinic_id)
        
        if vital_name_id is not None:
            query = query.filter(VitalFrequency.vital_name_id == vital_name_id)
        
        if is_active is not None:
            query = query.filter(VitalFrequency.is_active == is_active)
        
        # Order by priority (patient-specific first, then clinic, then global)
        query = query.order_by(
            case(
                (VitalFrequency.patient_id.isnot(None), 1),
                (VitalFrequency.clinic_id.isnot(None), 2),
                else_=3
            ),
            case(
                (VitalFrequency.vital_name_id.isnot(None), 1),
                else_=2
            )
        )
        
        return query.all()
    
    def get_frequency_rule_by_id(self, frequency_id: UUID) -> VitalFrequency:
        """
        Get frequency rule by ID
        
        Args:
            frequency_id: UUID of the frequency rule
            
        Returns:
            VitalFrequency object
            
        Raises:
            NotFoundException: If frequency rule not found
        """
        rule = self.db.query(VitalFrequency).filter(
            and_(
                VitalFrequency.id == frequency_id,
                VitalFrequency.deleted_at.is_(None)
            )
        ).first()
        
        if not rule:
            raise NotFoundException(f"Frequency rule with ID {frequency_id} not found")
        
        return rule
    
    def update_frequency_rule(
        self,
        frequency_id: UUID,
        frequency_type: Optional[str] = None,
        max_entries_per_day: Optional[int] = None,
        times_per_day: Optional[int] = None,
        preferred_times: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> VitalFrequency:
        """
        Update a frequency rule
        
        Args:
            frequency_id: UUID of the frequency rule to update
            frequency_type: New frequency type
            max_entries_per_day: New max entries per day
            times_per_day: New times per day
            preferred_times: New preferred times
            is_active: New active status
            
        Returns:
            Updated VitalFrequency object
        """
        rule = self.get_frequency_rule_by_id(frequency_id)
        
        if frequency_type is not None:
            rule.frequency_type = frequency_type
        if max_entries_per_day is not None:
            rule.max_entries_per_day = max_entries_per_day
        if times_per_day is not None:
            rule.times_per_day = times_per_day
        if preferred_times is not None:
            rule.preferred_times = preferred_times
        if is_active is not None:
            rule.is_active = is_active
        
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"Updated frequency rule: {rule}")
        
        return rule
    
    def delete_frequency_rule(self, frequency_id: UUID) -> None:
        """
        Delete a frequency rule (soft delete)
        
        Args:
            frequency_id: UUID of the frequency rule to delete
        """
        rule = self.get_frequency_rule_by_id(frequency_id)
        
        from datetime import datetime, timezone
        rule.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Deleted frequency rule: {rule}")

