"""
Slot Generation Utility
Dynamically generates appointment slots based on doctor availability and service duration
Slots are NOT persisted - generated on-demand
"""

from typing import List, Optional
from datetime import date, datetime, time, timedelta
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import exists
from loguru import logger

from app.models.availability import DoctorAvailability, DoctorTimeOff
from app.models.doctor_service import DoctorService
from app.models.doctor_service_availability import DoctorServiceAvailability
from app.core.security import ConsultationMode


@dataclass
class TimeSlot:
    """
    Represents a single bookable time slot (mode-aware)
    """
    start_datetime: datetime
    end_datetime: datetime
    doctor_id: UUID
    service_id: UUID
    clinic_id: UUID
    duration_minutes: int
    consultation_mode: str  # IN_CLINIC or TELECONSULTATION
    
    def to_dict(self) -> dict:
        """Convert slot to dictionary"""
        return {
            "start_datetime": self.start_datetime.isoformat(),
            "end_datetime": self.end_datetime.isoformat(),
            "doctor_id": str(self.doctor_id),
            "service_id": str(self.service_id),
            "clinic_id": str(self.clinic_id),
            "duration_minutes": self.duration_minutes,
            "consultation_mode": self.consultation_mode,
        }


class SlotGenerator:
    """
    Dynamically generates appointment slots (mode-aware)
    
    Uses:
    - doctor_availability for weekly schedule
    - doctor_service_availability for availability-specific service durations (PRIORITY 1)
    - doctor_services.slot_duration_minutes for day-specific durations (PRIORITY 2 - fallback)
    - doctor_time_off to exclude blocked periods
    
    Duration Priority:
    1. doctor_service_availability (availability-specific, service-specific, mode-specific)
    2. doctor_services (day-specific or default)
    3. Reject if neither exists
    
    Mode-Aware Logic:
    - For each availability block, loads services grouped by consultation_mode
    - Generates slots separately for each mode (IN_CLINIC and TELECONSULTATION)
    - Does NOT mix slots from different modes
    
    Slots are NOT persisted in database.
    """
    
    def __init__(self, db: Session):
        """
        Initialize slot generator
        
        Args:
            db: Database session
        """
        self.db = db
    
    def generate_slots(
        self,
        doctor_id: UUID,
        service_id: UUID,
        start_date: date,
        end_date: date,
        timezone_offset_hours: int = 0
    ) -> List[TimeSlot]:
        """
        Generate available slots for a doctor-service combination
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            start_date: Start date for slot generation
            end_date: End date for slot generation (inclusive)
            timezone_offset_hours: Timezone offset from UTC (default 0)
            
        Returns:
            List of available TimeSlot objects
        """
        # Get clinic_id - try from doctor_service first, or from availability
        clinic_id = self._get_clinic_id(doctor_id, service_id)
        if not clinic_id:
            logger.warning(f"No clinic found for doctor={doctor_id}, service={service_id}")
            return []
        
        # Get availability schedule
        availabilities = self._get_availabilities(doctor_id, clinic_id)
        if not availabilities:
            logger.debug(f"No availability found for doctor={doctor_id}")
            return []
        
        # Get time-off periods
        time_offs = self._get_time_offs(doctor_id, clinic_id, start_date, end_date)
        
        # Generate slots for each day (mode-aware)
        all_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            # Python weekday(): 0=Monday, 6=Sunday
            python_weekday = current_date.weekday()
            
            # Get availabilities for this day (using Python weekday for availability table)
            day_availabilities = [a for a in availabilities if a.day_of_week == python_weekday]
            
            for availability in day_availabilities:
                # Get all service assignments for this availability, grouped by consultation_mode
                service_assignments_by_mode = self._get_service_assignments_by_mode(
                    availability_id=availability.id,
                    doctor_id=doctor_id,
                    service_id=service_id,
                    current_date=current_date
                )
                
                # Generate slots separately for each mode (do NOT mix modes)
                for consultation_mode, slot_duration in service_assignments_by_mode.items():
                    if slot_duration is None:
                        # No valid assignment for this mode, skip
                        continue
                    
                    slots = self._generate_slots_for_availability(
                        availability=availability,
                        current_date=current_date,
                        slot_duration=slot_duration,
                        doctor_id=doctor_id,
                        service_id=service_id,
                        clinic_id=clinic_id,
                        consultation_mode=consultation_mode,
                        time_offs=time_offs
                    )
                    all_slots.extend(slots)
            
            current_date += timedelta(days=1)
        
        # Sort by start time
        all_slots.sort(key=lambda s: s.start_datetime)
        
        logger.debug(f"Generated {len(all_slots)} slots for doctor={doctor_id}, service={service_id} (mode-aware)")
        
        return all_slots
    
    def generate_slots_for_date(
        self,
        doctor_id: UUID,
        service_id: UUID,
        target_date: date
    ) -> List[TimeSlot]:
        """
        Generate slots for a specific date
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            target_date: Target date
            
        Returns:
            List of available TimeSlot objects for that date
        """
        return self.generate_slots(
            doctor_id=doctor_id,
            service_id=service_id,
            start_date=target_date,
            end_date=target_date
        )
    
    def _get_clinic_id(self, doctor_id: UUID, service_id: UUID) -> Optional[UUID]:
        """
        Get clinic_id for doctor-service combination
        
        Tries doctor_service_availability first, then doctor_services
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            
        Returns:
            Clinic ID or None
        """
        # Try from doctor_service_availability (join with availability)
        # Use explicit join to avoid EXISTS subquery issues
        try:
            # Join DoctorServiceAvailability with DoctorAvailability to get clinic_id
            # This avoids the exists() subquery which can cause parameter binding issues
            clinic_id_result = self.db.query(DoctorAvailability.clinic_id).join(
                DoctorServiceAvailability,
                DoctorServiceAvailability.availability_id == DoctorAvailability.id
            ).filter(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.is_active == True,
                DoctorAvailability.deleted_at.is_(None),
                DoctorServiceAvailability.service_id == service_id
            ).distinct().first()
            
            # Extract scalar value from result (first() can return None or the scalar value)
            if clinic_id_result is not None:
                # If it's already a scalar (UUID), return it directly
                # If it's a Row/tuple, extract the first element
                if hasattr(clinic_id_result, '__iter__') and not isinstance(clinic_id_result, (str, UUID)):
                    try:
                        return clinic_id_result[0] if len(clinic_id_result) > 0 else None
                    except (TypeError, IndexError):
                        return clinic_id_result
                return clinic_id_result
        except Exception as e:
            logger.error(f"Error getting clinic_id from availability: {e}", exc_info=True)
            # Fall through to fallback
        
        # Fallback to doctor_services
        doctor_service = self._get_any_doctor_service(doctor_id, service_id)
        if doctor_service:
            return doctor_service.clinic_id
        
        return None
    
    def _get_any_doctor_service(self, doctor_id: UUID, service_id: UUID) -> Optional[DoctorService]:
        """
        Get any active doctor-service assignment (for clinic_id lookup)
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            
        Returns:
            DoctorService or None
        """
        return self.db.query(DoctorService).filter(
            DoctorService.doctor_id == doctor_id,
            DoctorService.service_id == service_id,
            DoctorService.is_active == True
        ).first()
    
    def _get_service_assignments_by_mode(
        self,
        availability_id: UUID,
        doctor_id: UUID,
        service_id: UUID,
        current_date: date
    ) -> dict[str, Optional[int]]:
        """
        Get service assignments grouped by consultation_mode
        
        For each mode, returns slot duration with priority:
        1. doctor_service_availability (availability-specific, mode-specific)
        2. doctor_services (day-specific or default)
        3. None if neither exists
        
        Args:
            availability_id: Availability block ID
            doctor_id: Doctor user ID
            service_id: Service ID
            current_date: Current date for day-specific lookup
            
        Returns:
            Dictionary mapping consultation_mode to slot_duration (or None)
            Example: {"IN_CLINIC": 30, "TELECONSULTATION": 45}
        """
        result = {}
        
        # Get all service assignments for this availability + service (grouped by mode)
        service_availabilities = self.db.query(DoctorServiceAvailability).filter(
            DoctorServiceAvailability.availability_id == availability_id,
            DoctorServiceAvailability.service_id == service_id
        ).all()
        
        # Process each mode separately
        for mode in [ConsultationMode.IN_CLINIC.value, ConsultationMode.TELECONSULTATION.value]:
            # PRIORITY 1: Check doctor_service_availability for this specific mode
            mode_specific_assignment = next(
                (sa for sa in service_availabilities if sa.consultation_mode == mode),
                None
            )
            
            if mode_specific_assignment:
                result[mode] = mode_specific_assignment.slot_duration_minutes
            else:
                # PRIORITY 2: Fallback to doctor_services (day-specific or default)
                # Convert Python weekday to our day_of_week (0=Sunday)
                python_weekday = current_date.weekday()
                day_of_week = (python_weekday + 1) % 7
                
                result[mode] = self._get_slot_duration_for_day(doctor_id, service_id, day_of_week)
        
        return result
    
    def _get_slot_duration_for_availability(
        self,
        availability_id: UUID,
        doctor_id: UUID,
        service_id: UUID,
        current_date: date,
        consultation_mode: str
    ) -> Optional[int]:
        """
        Get slot duration for a specific availability + mode combination
        
        Priority:
        1. doctor_service_availability (availability-specific, mode-specific)
        2. doctor_services (day-specific or default)
        3. None if neither exists
        
        Args:
            availability_id: Availability block ID
            doctor_id: Doctor user ID
            service_id: Service ID
            current_date: Current date for day-specific lookup
            consultation_mode: Consultation mode (IN_CLINIC or TELECONSULTATION)
            
        Returns:
            Slot duration in minutes, or None if no assignment found
        """
        # PRIORITY 1: Check doctor_service_availability for this specific mode
        service_availability = self.db.query(DoctorServiceAvailability).filter(
            DoctorServiceAvailability.availability_id == availability_id,
            DoctorServiceAvailability.service_id == service_id,
            DoctorServiceAvailability.consultation_mode == consultation_mode
        ).first()
        
        if service_availability:
            return service_availability.slot_duration_minutes
        
        # PRIORITY 2: Fallback to doctor_services (day-specific or default)
        # Convert Python weekday to our day_of_week (0=Sunday)
        python_weekday = current_date.weekday()
        day_of_week = (python_weekday + 1) % 7
        
        return self._get_slot_duration_for_day(doctor_id, service_id, day_of_week)
    
    def _get_slot_duration_for_day(
        self,
        doctor_id: UUID,
        service_id: UUID,
        day_of_week: int
    ) -> Optional[int]:
        """
        Get slot duration for a specific day of week
        
        Priority:
        1. Try to find day-specific assignment (day_of_week = day)
        2. Fallback to default assignment (day_of_week IS NULL)
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            day_of_week: Day of week (0=Sunday, 6=Saturday)
            
        Returns:
            Slot duration in minutes, or None if no assignment found
        """
        # First try day-specific assignment
        day_specific = self.db.query(DoctorService).filter(
            DoctorService.doctor_id == doctor_id,
            DoctorService.service_id == service_id,
            DoctorService.day_of_week == day_of_week,
            DoctorService.is_active == True
        ).first()
        
        if day_specific:
            return day_specific.slot_duration_minutes
        
        # Fallback to default (day_of_week IS NULL)
        default_assignment = self.db.query(DoctorService).filter(
            DoctorService.doctor_id == doctor_id,
            DoctorService.service_id == service_id,
            DoctorService.day_of_week.is_(None),
            DoctorService.is_active == True
        ).first()
        
        if default_assignment:
            return default_assignment.slot_duration_minutes
        
        return None
    
    def _get_doctor_service_for_datetime(
        self,
        doctor_id: UUID,
        service_id: UUID,
        slot_datetime: datetime
    ) -> Optional[DoctorService]:
        """
        Get doctor-service assignment for a specific datetime
        
        Uses day-specific duration if available, otherwise default.
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            slot_datetime: Slot datetime
            
        Returns:
            DoctorService or None
        """
        # Convert Python weekday to our day_of_week (0=Sunday)
        python_weekday = slot_datetime.weekday()
        day_of_week = (python_weekday + 1) % 7
        
        # First try day-specific assignment
        day_specific = self.db.query(DoctorService).filter(
            DoctorService.doctor_id == doctor_id,
            DoctorService.service_id == service_id,
            DoctorService.day_of_week == day_of_week,
            DoctorService.is_active == True
        ).first()
        
        if day_specific:
            return day_specific
        
        # Fallback to default (day_of_week IS NULL)
        return self.db.query(DoctorService).filter(
            DoctorService.doctor_id == doctor_id,
            DoctorService.service_id == service_id,
            DoctorService.day_of_week.is_(None),
            DoctorService.is_active == True
        ).first()
    
    def _get_availabilities(self, doctor_id: UUID, clinic_id: UUID) -> List[DoctorAvailability]:
        """
        Get doctor's active availability schedule
        
        Args:
            doctor_id: Doctor user ID
            clinic_id: Clinic ID
            
        Returns:
            List of DoctorAvailability objects
        """
        return self.db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.clinic_id == clinic_id,
            DoctorAvailability.is_active == True,
            DoctorAvailability.deleted_at.is_(None)
        ).order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time).all()
    
    def _get_time_offs(
        self,
        doctor_id: UUID,
        clinic_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[DoctorTimeOff]:
        """
        Get doctor's time-off periods overlapping with date range
        
        Args:
            doctor_id: Doctor user ID
            clinic_id: Clinic ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of DoctorTimeOff objects
        """
        # Convert dates to datetime for comparison
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        
        return self.db.query(DoctorTimeOff).filter(
            DoctorTimeOff.doctor_id == doctor_id,
            DoctorTimeOff.clinic_id == clinic_id,
            DoctorTimeOff.deleted_at.is_(None),
            # Time-off overlaps with date range
            DoctorTimeOff.start_datetime <= end_dt,
            DoctorTimeOff.end_datetime >= start_dt
        ).all()
    
    def _generate_slots_for_availability(
        self,
        availability: DoctorAvailability,
        current_date: date,
        slot_duration: int,
        doctor_id: UUID,
        service_id: UUID,
        clinic_id: UUID,
        consultation_mode: str,
        time_offs: List[DoctorTimeOff]
    ) -> List[TimeSlot]:
        """
        Generate slots for a single availability window on a specific date (mode-aware)
        
        Args:
            availability: DoctorAvailability object
            current_date: Date to generate slots for
            slot_duration: Slot duration in minutes
            doctor_id: Doctor user ID
            service_id: Service ID
            clinic_id: Clinic ID
            consultation_mode: Consultation mode (IN_CLINIC or TELECONSULTATION)
            time_offs: List of time-off periods
            
        Returns:
            List of TimeSlot objects (all with the same consultation_mode)
        """
        slots = []
        
        # Create datetime from date + availability times
        avail_start = datetime.combine(current_date, availability.start_time)
        avail_end = datetime.combine(current_date, availability.end_time)
        
        # Split availability window into slots
        current_slot_start = avail_start
        slot_delta = timedelta(minutes=slot_duration)
        
        while current_slot_start + slot_delta <= avail_end:
            current_slot_end = current_slot_start + slot_delta
            
            # Check if slot overlaps with any time-off
            if not self._is_blocked_by_time_off(current_slot_start, current_slot_end, time_offs):
                slots.append(TimeSlot(
                    start_datetime=current_slot_start,
                    end_datetime=current_slot_end,
                    doctor_id=doctor_id,
                    service_id=service_id,
                    clinic_id=clinic_id,
                    duration_minutes=slot_duration,
                    consultation_mode=consultation_mode
                ))
            
            current_slot_start = current_slot_end
        
        return slots
    
    def _is_blocked_by_time_off(
        self,
        slot_start: datetime,
        slot_end: datetime,
        time_offs: List[DoctorTimeOff]
    ) -> bool:
        """
        Check if a slot overlaps with any time-off period
        
        Args:
            slot_start: Slot start datetime
            slot_end: Slot end datetime
            time_offs: List of time-off periods
            
        Returns:
            True if blocked, False otherwise
        """
        for time_off in time_offs:
            # Check for any overlap
            # Overlap exists if: slot_start < time_off_end AND slot_end > time_off_start
            if slot_start < time_off.end_datetime and slot_end > time_off.start_datetime:
                return True
        
        return False
    
    def get_available_slots_count(
        self,
        doctor_id: UUID,
        service_id: UUID,
        start_date: date,
        end_date: date
    ) -> int:
        """
        Get count of available slots (for quick availability check)
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Number of available slots
        """
        slots = self.generate_slots(doctor_id, service_id, start_date, end_date)
        return len(slots)
    
    def is_slot_available(
        self,
        doctor_id: UUID,
        service_id: UUID,
        slot_start: datetime,
        slot_end: datetime,
        consultation_mode: Optional[str] = None
    ) -> bool:
        """
        Check if a specific slot is available (mode-aware)
        
        Uses priority logic:
        1. doctor_service_availability (availability-specific, mode-specific)
        2. doctor_services (day-specific or default)
        3. Reject if neither exists
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            slot_start: Slot start datetime
            slot_end: Slot end datetime
            consultation_mode: Optional consultation mode (defaults to IN_CLINIC if not provided)
            
        Returns:
            True if slot is available, False otherwise
        """
        # Normalize consultation_mode
        if consultation_mode:
            try:
                mode = ConsultationMode(consultation_mode)
                consultation_mode = mode.value
            except ValueError:
                consultation_mode = ConsultationMode.default()
        else:
            consultation_mode = ConsultationMode.default()
        
        slot_date = slot_start.date()
        python_weekday = slot_date.weekday()  # 0=Monday, 6=Sunday
        
        # Get clinic_id
        clinic_id = self._get_clinic_id(doctor_id, service_id)
        if not clinic_id:
            return False
        
        # Check if slot falls within any availability window
        availabilities = self._get_availabilities(doctor_id, clinic_id)
        matching_availability = None
        
        for avail in availabilities:
            if avail.day_of_week != python_weekday:
                continue
            
            avail_start = datetime.combine(slot_date, avail.start_time)
            avail_end = datetime.combine(slot_date, avail.end_time)
            
            if slot_start >= avail_start and slot_end <= avail_end:
                matching_availability = avail
                break
        
        if not matching_availability:
            return False
        
        # Get slot duration with priority logic (mode-aware)
        slot_duration = self._get_slot_duration_for_availability(
            availability_id=matching_availability.id,
            doctor_id=doctor_id,
            service_id=service_id,
            current_date=slot_date,
            consultation_mode=consultation_mode
        )
        
        if slot_duration is None:
            # No valid assignment found for this mode
            return False
        
        # Check duration matches the expected duration
        actual_duration = int((slot_end - slot_start).total_seconds() / 60)
        if actual_duration != slot_duration:
            return False
        
        # Check for time-off conflicts
        time_offs = self._get_time_offs(doctor_id, clinic_id, slot_date, slot_date)
        if self._is_blocked_by_time_off(slot_start, slot_end, time_offs):
            return False
        
        return True


def get_slot_generator(db: Session) -> SlotGenerator:
    """
    Get slot generator instance (for dependency injection)
    
    Args:
        db: Database session
        
    Returns:
        SlotGenerator instance
    """
    return SlotGenerator(db)
