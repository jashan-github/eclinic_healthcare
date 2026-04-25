"""
Availability Service
Business logic for doctor availability and time-off management
"""

from typing import Optional, List, Dict, Any
from datetime import time, datetime, date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from loguru import logger

from app.models.user import User
from app.models.availability import DoctorAvailability, DoctorTimeOff
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityResponse,
    TimeOffCreate,
    TimeOffResponse
)
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ConflictException,
    ValidationException
)
from app.core.security import CurrentUser


class AvailabilityService:
    """
    Service for managing doctor availability and time-off
    
    Responsibilities:
    - Create/update/delete availability slots
    - Prevent overlapping availability slots
    - Manage time-off periods
    - Enforce access control (doctor manages own, admin manages any)
    - Enforce clinic isolation
    """
    
    def __init__(self, db: Session):
        """
        Initialize availability service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _check_doctor_role(self, user_id: UUID) -> User:
        """
        Verify that user is a doctor
        
        Args:
            user_id: User ID to check
            
        Returns:
            User object
            
        Raises:
            NotFoundException: If user not found
            ValidationException: If user is not a doctor
        """
        user = self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise NotFoundException(
                message="Doctor not found",
                errors={"doctor_id": ["Doctor with this ID does not exist"]}
            )
        
        if user.role != "doctor":
            raise ValidationException(
                message="User is not a doctor",
                errors={"doctor_id": ["User must have role 'doctor'"]}
            )
        
        return user
    
    def _check_permission(
        self,
        doctor_id: UUID,
        current_user: CurrentUser
    ) -> None:
        """
        Check if current user can manage availability for doctor
        
        Args:
            doctor_id: Doctor ID
            current_user: Current authenticated user
            
        Raises:
            ForbiddenException: If user doesn't have permission
        """
        # Get role as string (handle both UserRole enum and string)
        if hasattr(current_user.role, 'value'):
            role_str = current_user.role.value
        else:
            role_str = str(current_user.role)
        
        # Admin can manage any doctor
        if role_str in ["super_admin", "clinic_admin"]:
            return
        
        # Doctor can only manage own availability
        if role_str == "doctor" and str(current_user.id) == str(doctor_id):
            return
        
        # Otherwise, forbidden
        raise ForbiddenException(
            message="You do not have permission to manage this doctor's availability",
            errors={"permission": ["Only the doctor or an admin can manage availability"]}
        )
    
    def _check_overlap(
        self,
        doctor_id: UUID,
        clinic_id: UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if availability slot overlaps with existing slots
        
        Args:
            doctor_id: Doctor ID
            clinic_id: Clinic ID
            day_of_week: Day of week (0-6)
            start_time: Start time
            end_time: End time
            exclude_id: Availability ID to exclude from check (for updates)
            
        Returns:
            True if overlap exists, False otherwise
        """
        query = self.db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.clinic_id == clinic_id,
            DoctorAvailability.day_of_week == day_of_week,
            DoctorAvailability.deleted_at.is_(None)
        )
        
        if exclude_id:
            query = query.filter(DoctorAvailability.id != exclude_id)
        
        existing_slots = query.all()
        
        for slot in existing_slots:
            # Check for overlap: slots overlap if they share any time
            # Slot A overlaps Slot B if:
            # - A starts before B ends AND A ends after B starts
            if start_time < slot.end_time and end_time > slot.start_time:
                return True
        
        return False
    
    def _check_time_off_overlap(
        self,
        doctor_id: UUID,
        clinic_id: UUID,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if time-off period overlaps with existing time-off
        
        Args:
            doctor_id: Doctor ID
            clinic_id: Clinic ID
            start_datetime: Start datetime
            end_datetime: End datetime
            exclude_id: Time-off ID to exclude from check (for updates)
            
        Returns:
            True if overlap exists, False otherwise
        """
        query = self.db.query(DoctorTimeOff).filter(
            DoctorTimeOff.doctor_id == doctor_id,
            DoctorTimeOff.clinic_id == clinic_id,
            DoctorTimeOff.deleted_at.is_(None)
        )
        
        if exclude_id:
            query = query.filter(DoctorTimeOff.id != exclude_id)
        
        existing_time_offs = query.all()
        
        for time_off in existing_time_offs:
            # Check for overlap
            if start_datetime < time_off.end_datetime and end_datetime > time_off.start_datetime:
                return True
        
        return False
    
    def get_availability(
        self,
        doctor_id: UUID,
        clinic_id: Optional[UUID] = None,
        current_user: Optional[CurrentUser] = None
    ) -> List[AvailabilityResponse]:
        """
        Get availability slots for a doctor
        
        Args:
            doctor_id: Doctor ID
            clinic_id: Optional clinic ID filter
            current_user: Current authenticated user (for permission check)
            
        Returns:
            List of availability slots
        """
        # Verify doctor exists and is a doctor
        self._check_doctor_role(doctor_id)
        
        # Check permissions if current_user provided
        if current_user:
            self._check_permission(doctor_id, current_user)
        
        # Build query
        query = self.db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.deleted_at.is_(None)
        )
        
        if clinic_id:
            query = query.filter(DoctorAvailability.clinic_id == clinic_id)
        
        # Get all availability slots
        slots = query.order_by(
            DoctorAvailability.day_of_week,
            DoctorAvailability.start_time
        ).all()
        
        # Convert to response format
        return [
            AvailabilityResponse(
                id=slot.id,
                doctor_id=slot.doctor_id,
                clinic_id=slot.clinic_id,
                day_of_week=slot.day_of_week,
                start_time=slot.start_time.isoformat(),
                end_time=slot.end_time.isoformat(),
                is_active=slot.is_active,
                created_at=slot.created_at,
                updated_at=slot.updated_at
            )
            for slot in slots
        ]
    
    def create_availability(
        self,
        doctor_id: UUID,
        availability_data: AvailabilityCreate,
        current_user: CurrentUser
    ) -> AvailabilityResponse:
        """
        Create a new availability slot
        
        Args:
            doctor_id: Doctor ID
            availability_data: Availability data
            current_user: Current authenticated user
            
        Returns:
            Created availability slot
            
        Raises:
            ForbiddenException: If user doesn't have permission
            ConflictException: If slot overlaps with existing slot
        """
        # Verify doctor exists and is a doctor
        self._check_doctor_role(doctor_id)
        
        # Check permissions
        self._check_permission(doctor_id, current_user)
        
        # Check for overlaps
        if self._check_overlap(
            doctor_id=doctor_id,
            clinic_id=availability_data.clinic_id,
            day_of_week=availability_data.day_of_week,
            start_time=availability_data.start_time,
            end_time=availability_data.end_time
        ):
            raise ConflictException(
                message="Availability slot overlaps with existing slot",
                errors={
                    "availability": ["This time slot overlaps with an existing availability slot"]
                }
            )
        
        # Create availability slot
        availability = DoctorAvailability(
            doctor_id=doctor_id,
            clinic_id=availability_data.clinic_id,
            day_of_week=availability_data.day_of_week,
            start_time=availability_data.start_time,
            end_time=availability_data.end_time,
            is_active=availability_data.is_active
        )
        
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        
        logger.info(
            f"Created availability slot for doctor {doctor_id} at clinic {availability_data.clinic_id}"
        )
        
        return AvailabilityResponse(
            id=availability.id,
            doctor_id=availability.doctor_id,
            clinic_id=availability.clinic_id,
            day_of_week=availability.day_of_week,
            start_time=availability.start_time.isoformat(),
            end_time=availability.end_time.isoformat(),
            is_active=availability.is_active,
            created_at=availability.created_at,
            updated_at=availability.updated_at
        )
    
    def update_availability(
        self,
        availability_id: UUID,
        availability_data: AvailabilityUpdate,
        current_user: CurrentUser
    ) -> AvailabilityResponse:
        """
        Update an availability slot
        
        Args:
            availability_id: Availability slot ID
            availability_data: Updated availability data
            current_user: Current authenticated user
            
        Returns:
            Updated availability slot
            
        Raises:
            NotFoundException: If availability slot not found
            ForbiddenException: If user doesn't have permission
            ConflictException: If updated slot overlaps with existing slot
        """
        # Get availability slot
        availability = self.db.query(DoctorAvailability).filter(
            DoctorAvailability.id == availability_id,
            DoctorAvailability.deleted_at.is_(None)
        ).first()
        
        if not availability:
            raise NotFoundException(
                message="Availability slot not found",
                errors={"availability_id": ["Availability slot with this ID does not exist"]}
            )
        
        # Check permissions
        self._check_permission(availability.doctor_id, current_user)
        
        # Prepare update data
        update_data = availability_data.model_dump(exclude_unset=True)
        
        # Get new values (use existing if not provided)
        new_day = update_data.get("day_of_week", availability.day_of_week)
        new_start = update_data.get("start_time", availability.start_time)
        new_end = update_data.get("end_time", availability.end_time)
        
        # Check for overlaps (excluding current slot)
        if self._check_overlap(
            doctor_id=availability.doctor_id,
            clinic_id=availability.clinic_id,
            day_of_week=new_day,
            start_time=new_start,
            end_time=new_end,
            exclude_id=availability_id
        ):
            raise ConflictException(
                message="Updated availability slot overlaps with existing slot",
                errors={
                    "availability": ["This time slot overlaps with an existing availability slot"]
                }
            )
        
        # Update fields
        for key, value in update_data.items():
            setattr(availability, key, value)
        
        self.db.commit()
        self.db.refresh(availability)
        
        logger.info(f"Updated availability slot {availability_id}")
        
        return AvailabilityResponse(
            id=availability.id,
            doctor_id=availability.doctor_id,
            clinic_id=availability.clinic_id,
            day_of_week=availability.day_of_week,
            start_time=availability.start_time.isoformat(),
            end_time=availability.end_time.isoformat(),
            is_active=availability.is_active,
            created_at=availability.created_at,
            updated_at=availability.updated_at
        )
    
    def delete_availability(
        self,
        availability_id: UUID,
        current_user: CurrentUser
    ) -> None:
        """
        Delete (soft delete) an availability slot
        
        Args:
            availability_id: Availability slot ID
            current_user: Current authenticated user
            
        Raises:
            NotFoundException: If availability slot not found
            ForbiddenException: If user doesn't have permission
        """
        # Get availability slot
        availability = self.db.query(DoctorAvailability).filter(
            DoctorAvailability.id == availability_id,
            DoctorAvailability.deleted_at.is_(None)
        ).first()
        
        if not availability:
            raise NotFoundException(
                message="Availability slot not found",
                errors={"availability_id": ["Availability slot with this ID does not exist"]}
            )
        
        # Check permissions
        self._check_permission(availability.doctor_id, current_user)
        
        # Soft delete
        availability.soft_delete()
        self.db.commit()
        
        logger.info(f"Deleted availability slot {availability_id}")
    
    def get_time_off(
        self,
        doctor_id: UUID,
        clinic_id: Optional[UUID] = None,
        current_user: Optional[CurrentUser] = None
    ) -> List[TimeOffResponse]:
        """
        Get time-off periods for a doctor
        
        Args:
            doctor_id: Doctor ID
            clinic_id: Optional clinic ID filter
            current_user: Current authenticated user (for permission check)
            
        Returns:
            List of time-off periods
        """
        # Verify doctor exists and is a doctor
        self._check_doctor_role(doctor_id)
        
        # Check permissions if current_user provided
        if current_user:
            self._check_permission(doctor_id, current_user)
        
        # Build query
        query = self.db.query(DoctorTimeOff).filter(
            DoctorTimeOff.doctor_id == doctor_id,
            DoctorTimeOff.deleted_at.is_(None)
        )
        
        if clinic_id:
            query = query.filter(DoctorTimeOff.clinic_id == clinic_id)
        
        # Get all time-off periods
        time_offs = query.order_by(DoctorTimeOff.start_datetime).all()
        
        # Convert to response format
        return [
            TimeOffResponse(
                id=time_off.id,
                doctor_id=time_off.doctor_id,
                clinic_id=time_off.clinic_id,
                start_datetime=time_off.start_datetime,
                end_datetime=time_off.end_datetime,
                reason=time_off.reason,
                created_at=time_off.created_at
            )
            for time_off in time_offs
        ]
    
    def create_time_off(
        self,
        doctor_id: UUID,
        time_off_data: TimeOffCreate,
        current_user: CurrentUser
    ) -> TimeOffResponse:
        """
        Create a new time-off period
        
        Args:
            doctor_id: Doctor ID
            time_off_data: Time-off data
            current_user: Current authenticated user
            
        Returns:
            Created time-off period
            
        Raises:
            ForbiddenException: If user doesn't have permission
            ConflictException: If time-off overlaps with existing time-off
        """
        # Verify doctor exists and is a doctor
        self._check_doctor_role(doctor_id)
        
        # Check permissions
        self._check_permission(doctor_id, current_user)
        
        # Check for overlaps
        if self._check_time_off_overlap(
            doctor_id=doctor_id,
            clinic_id=time_off_data.clinic_id,
            start_datetime=time_off_data.start_datetime,
            end_datetime=time_off_data.end_datetime
        ):
            raise ConflictException(
                message="Time-off period overlaps with existing time-off",
                errors={
                    "time_off": ["This time-off period overlaps with an existing time-off period"]
                }
            )
        
        # Create time-off period
        time_off = DoctorTimeOff(
            doctor_id=doctor_id,
            clinic_id=time_off_data.clinic_id,
            start_datetime=time_off_data.start_datetime,
            end_datetime=time_off_data.end_datetime,
            reason=time_off_data.reason
        )
        
        self.db.add(time_off)
        self.db.commit()
        self.db.refresh(time_off)
        
        logger.info(
            f"Created time-off period for doctor {doctor_id} at clinic {time_off_data.clinic_id}"
        )
        
        return TimeOffResponse(
            id=time_off.id,
            doctor_id=time_off.doctor_id,
            clinic_id=time_off.clinic_id,
            start_datetime=time_off.start_datetime,
            end_datetime=time_off.end_datetime,
            reason=time_off.reason,
            created_at=time_off.created_at
        )
    
    def delete_time_off(
        self,
        time_off_id: UUID,
        current_user: CurrentUser
    ) -> None:
        """
        Delete (soft delete) a time-off period
        
        Args:
            time_off_id: Time-off period ID
            current_user: Current authenticated user
            
        Raises:
            NotFoundException: If time-off period not found
            ForbiddenException: If user doesn't have permission
        """
        # Get time-off period
        time_off = self.db.query(DoctorTimeOff).filter(
            DoctorTimeOff.id == time_off_id,
            DoctorTimeOff.deleted_at.is_(None)
        ).first()
        
        if not time_off:
            raise NotFoundException(
                message="Time-off period not found",
                errors={"time_off_id": ["Time-off period with this ID does not exist"]}
            )
        
        # Check permissions
        self._check_permission(time_off.doctor_id, current_user)
        
        # Soft delete
        time_off.soft_delete()
        self.db.commit()
        
        logger.info(f"Deleted time-off period {time_off_id}")


from fastapi import Depends
from app.core.database import get_db


def get_availability_service(db: Session = Depends(get_db)) -> AvailabilityService:
    """
    Dependency injection for AvailabilityService
    
    Args:
        db: Database session (injected by FastAPI)
        
    Returns:
        AvailabilityService instance
    """
    return AvailabilityService(db)
