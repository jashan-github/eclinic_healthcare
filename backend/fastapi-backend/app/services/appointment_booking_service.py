"""
Appointment Booking Service
Business logic for patient appointment booking flow
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from loguru import logger

from app.models.user import User
from app.models.profile import UserProfile, user_medical_services
from app.models.medical_service import MedicalService
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.doctor_service_availability import DoctorServiceAvailability
from app.models.availability import DoctorAvailability
from app.utils.pricing_resolver import PricingResolver
from app.utils.slot_generator import SlotGenerator, TimeSlot
from app.core.security import CurrentUser, ConsultationMode, UserRole
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException
)
from app.core.config import settings
from app.services.admin_settings_service import AdminSettingsService
from app.utils.waiver_helper import get_display_amounts


class AppointmentBookingService:
    """Service for patient appointment booking operations"""
    
    def __init__(self, db: Session):
        """
        Initialize appointment booking service
        
        Args:
            db: Database session
        """
        self.db = db
        self.pricing_resolver = PricingResolver(db)
        self.slot_generator = SlotGenerator(db)
        self.admin_settings_service = AdminSettingsService(db)
    
    def get_doctor_summary(
        self,
        doctor_id: UUID,
        service_id: UUID,
        consultation_mode: Optional[str] = None,
        booking_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get doctor summary with pricing for appointment booking.
        Price is resolved for the given date when the doctor has availability-specific
        pricing for that day; otherwise falls back to doctor-service or service base price.
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            consultation_mode: Optional consultation mode (defaults to IN_CLINIC)
            booking_date: Optional date for pricing (default: today). Used to pick availability-specific price when available.
            
        Returns:
            Dictionary with doctor summary and pricing
        """
        # Get doctor
        doctor = self.db.query(User).filter(
            User.id == doctor_id,
            User.role == UserRole.DOCTOR.value,
            User.is_active == True,
            User.deleted_at.is_(None)
        ).first()
        
        if not doctor:
            raise NotFoundException(
                message="Doctor not found",
                errors={"doctor_id": ["Doctor does not exist or is not active"]}
            )
        
        # Get service
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise NotFoundException(
                message="Service not found",
                errors={"service_id": ["Service does not exist"]}
            )
        
        # Get doctor profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == doctor_id
        ).first()
        
        # Get primary specialty
        specialty = None
        medical_services = self.db.query(MedicalService).join(
            user_medical_services,
            user_medical_services.c.medical_service_id == MedicalService.id
        ).filter(
            user_medical_services.c.user_id == doctor_id,
            MedicalService.status == True
        ).limit(1).all()
        
        if medical_services:
            specialty = medical_services[0].name
        
        # Resolve pricing for the consultation mode (for booking_date when possible)
        consultation_mode = consultation_mode or ConsultationMode.default()
        target_date = booking_date if booking_date is not None else date.today()
        day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday (matches DoctorAvailability)

        # Find an availability assignment for this doctor+service+mode on the target day (for date-specific pricing)
        doctor_service_availability_id = None
        availability_assignment = self.db.query(DoctorServiceAvailability).join(
            DoctorAvailability,
            DoctorAvailability.id == DoctorServiceAvailability.availability_id
        ).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.day_of_week == day_of_week,
            DoctorAvailability.is_active == True,
            DoctorAvailability.deleted_at.is_(None),
            DoctorServiceAvailability.service_id == service_id,
            DoctorServiceAvailability.consultation_mode == consultation_mode
        ).first()
        if availability_assignment:
            doctor_service_availability_id = availability_assignment.id

        try:
            price_amount, currency, pricing_source = self.pricing_resolver.resolve_price(
                doctor_id=doctor_id,
                service_id=service_id,
                doctor_service_availability_id=doctor_service_availability_id,
                consultation_mode=consultation_mode,
                currency=None  # No currency validation - get from pricing source
            )
        except BadRequestException:
            # No price found - set to None
            price_amount = None
            currency = service.currency  # Use service currency if available, can be None
        
        # Intake fee (not in current schema - return 0 for now)
        intake_fee = Decimal('0.00')
        
        # Apply admin waiver for display
        consultation_fee_after = None
        amount_before_waiver = None
        waiver_percent = None
        if price_amount is not None:
            after, waiver_percent, amount_before_waiver = get_display_amounts(self.db, price_amount)
            consultation_fee_after = float(after)
            amount_before_waiver = float(amount_before_waiver)
        
        total_fee = None
        if consultation_fee_after is not None:
            total_fee = consultation_fee_after + float(intake_fee)
        
        # Build full profile image URL
        avatar_path = doctor.avatar or (profile.avatar if profile else None)
        profile_image_url = None
        if avatar_path:
            base_url = settings.BASE_URL.rstrip('/')
            avatar_path_clean = avatar_path.lstrip('/')
            profile_image_url = f"{base_url}/{avatar_path_clean}"
        
        return {
            "id": doctor.id,
            "name": doctor.name,
            "profile_image": profile_image_url,
            "specialty": specialty,
            "years_of_experience": profile.years_of_experience if profile else None,
            "rating": None,  # Rating not available in current schema
            "consultation_fee": consultation_fee_after,
            "intake_fee": float(intake_fee),
            "total_fee": total_fee,
            "amount_before_waiver": amount_before_waiver,
            "waiver_percent": waiver_percent,
            "currency": "XCG",  # Fixed currency
            "date": target_date.isoformat(),  # Date for which price was resolved
        }
    
    def get_available_consultation_modes(
        self,
        doctor_id: UUID,
        service_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get available consultation modes for a doctor-service combination
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            
        Returns:
            List of available consultation modes with pricing
            Only returns modes that match the service's service_mode
        """
        # First, get the service to check its service_mode
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise NotFoundException(
                message="Service not found",
                errors={"service_id": ["Service does not exist"]}
            )
        
        modes: List[Dict[str, Any]] = []

        # Return both consultation modes (IN_CLINIC and TELECONSULTATION) and indicate
        # whether the doctor has availability for each mode for the given service.
        for mode in [ConsultationMode.IN_CLINIC.value, ConsultationMode.TELECONSULTATION.value]:
            # Check if doctor has availability assignments for this mode
            has_availability = self.db.query(DoctorServiceAvailability).join(
                DoctorAvailability,
                DoctorServiceAvailability.availability_id == DoctorAvailability.id
            ).filter(
                DoctorServiceAvailability.service_id == service_id,
                DoctorAvailability.doctor_id == doctor_id,
                DoctorServiceAvailability.consultation_mode == mode,
                DoctorAvailability.is_active == True,
                DoctorAvailability.deleted_at.is_(None)
            ).first() is not None

            # Resolve pricing for this mode (best-effort)
            try:
                price_amount, currency, _ = self.pricing_resolver.resolve_price(
                    doctor_id=doctor_id,
                    service_id=service_id,
                    doctor_service_availability_id=None,
                    consultation_mode=mode,
                    currency=None  # No currency validation - get from pricing source
                )
            except BadRequestException:
                price_amount = None
                currency = None  # No currency if no price

            # Intake fee (not in current schema)
            intake_fee = Decimal('0.00')

            # Apply admin waiver for display
            consultation_fee_after = None
            amount_before_waiver = None
            waiver_percent = None
            if price_amount is not None:
                after, waiver_percent, amount_before_waiver = get_display_amounts(self.db, price_amount)
                consultation_fee_after = float(after)
                amount_before_waiver = float(amount_before_waiver)

            total_fee = None
            if consultation_fee_after is not None:
                total_fee = consultation_fee_after + float(intake_fee)

            modes.append({
                "mode": mode,
                "label": "In-Clinic" if mode == ConsultationMode.IN_CLINIC.value else "Teleconsultation",
                "consultation_fee": consultation_fee_after,
                "intake_fee": float(intake_fee),
                "total_fee": total_fee,
                "amount_before_waiver": amount_before_waiver,
                "waiver_percent": waiver_percent,
                "currency": "XCG",  # Fixed currency, not dynamic
                "is_available": has_availability
            })

        return modes
    
    def get_available_time_slots(
        self,
        doctor_id: UUID,
        service_id: UUID,
        preferred_date: date,
        consultation_mode: str
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for a specific date and consultation mode
        
        Args:
            doctor_id: Doctor user ID
            service_id: Service ID
            preferred_date: Preferred appointment date
            consultation_mode: Consultation mode (IN_CLINIC or TELECONSULTATION)
            
        Returns:
            List of time slots with availability status (is_available field)
        """
        from app.models.appointment import Appointment
        from app.models.appointment_request import AppointmentRequest
        from datetime import datetime
        
        # Validate consultation mode
        try:
            mode = ConsultationMode(consultation_mode)
            consultation_mode = mode.value
        except ValueError:
            raise BadRequestException(
                message="Invalid consultation mode",
                errors={"consultation_mode": [f"Must be one of: {[m.value for m in ConsultationMode]}"]}
            )
        
        # Generate slots for the preferred date
        slots = self.slot_generator.generate_slots(
            doctor_id=doctor_id,
            service_id=service_id,
            start_date=preferred_date,
            end_date=preferred_date
        )
        
        # Filter slots by consultation mode
        mode_slots = [
            slot for slot in slots
            if slot.consultation_mode == consultation_mode
        ]
        
        # Get all confirmed appointments (these block the slot)
        confirmed_appointments = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == preferred_date,
            Appointment.status == 'CONFIRMED',
            Appointment.deleted_at.is_(None)
        ).all()
        
        # Get all pending or accepted appointment requests (these block the slot)
        # Note: REJECTED/CANCELLED appointment requests do NOT block slots (is_available = true)
        # ACCEPTED requests should also block the slot even if they haven't yet been converted
        # to a confirmed appointment (e.g. waiting for payment). Include both PENDING and ACCEPTED.
        pending_requests = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.doctor_id == doctor_id,
            AppointmentRequest.preferred_date == preferred_date,
            AppointmentRequest.status.in_(['PENDING', 'ACCEPTED']),
            AppointmentRequest.deleted_at.is_(None)
        ).all()
        
        # Create sets of booked times for quick lookup
        booked_times = set()
        for appointment in confirmed_appointments:
            booked_times.add(appointment.start_time)
        
        for request in pending_requests:
            booked_times.add(request.preferred_time)
        
        # Exclude past slots for the selected date (app timezone)
        from app.services.appointment_request_service import get_est_datetime, get_app_timezone
        now_app = get_est_datetime()
        tz = get_app_timezone()

        # Convert to response format with availability status
        all_slots = []
        for slot in mode_slots:
            slot_start_naive = slot.start_datetime
            slot_start = slot_start_naive if slot_start_naive.tzinfo else tz.localize(slot_start_naive)
            if slot_start <= now_app:
                continue  # Skip past slots so UI does not show them
            slot_time = slot.start_datetime.time()
            # Check if slot is booked by confirmed appointments or pending requests
            # REJECTED/CANCELLED requests don't block (is_available = true)
            is_available = slot_time not in booked_times

            all_slots.append({
                "date": slot.start_datetime.date().isoformat(),
                "time": slot.start_datetime.time().isoformat(),
                "duration_minutes": slot.duration_minutes,
                "consultation_mode": slot.consultation_mode,
                "is_available": is_available
            })

        # Sort by time
        all_slots.sort(key=lambda x: x["time"])

        return all_slots
    
    def create_appointment_request(
        self,
        current_user: CurrentUser,
        doctor_id: UUID,
        service_id: UUID,
        consultation_mode: str,
        preferred_date: date,
        preferred_time: time,
        reason: Optional[str] = None,
        doctor_service_availability_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Appointment:
        """
        Create an appointment request (status: SCHEDULED)
        
        Args:
            current_user: Current patient user
            doctor_id: Doctor user ID
            service_id: Service ID
            consultation_mode: Consultation mode
            preferred_date: Preferred appointment date
            preferred_time: Preferred appointment time
            reason: Optional reason/symptoms
            doctor_service_availability_id: Optional availability assignment ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created Appointment object
        """
        # Validate consultation mode
        try:
            mode = ConsultationMode(consultation_mode)
            consultation_mode = mode.value
        except ValueError:
            raise BadRequestException(
                message="Invalid consultation mode",
                errors={"consultation_mode": [f"Must be one of: {[m.value for m in ConsultationMode]}"]}
            )
        
        # Get patient
        patient = self.db.query(User).filter(
            User.id == current_user.id,
            User.role == UserRole.PATIENT.value,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient does not exist"]}
            )
        
        # Get doctor
        doctor = self.db.query(User).filter(
            User.id == doctor_id,
            User.role == UserRole.DOCTOR.value,
            User.is_active == True,
            User.deleted_at.is_(None)
        ).first()
        
        if not doctor:
            raise NotFoundException(
                message="Doctor not found",
                errors={"doctor_id": ["Doctor does not exist or is not active"]}
            )
        
        # Get service
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.is_bookable == True,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise NotFoundException(
                message="Service not found or not bookable",
                errors={"service_id": ["Service does not exist or is not available for booking"]}
            )
        
        # Validate booking date against admin settings
        is_valid_date, date_error = self.admin_settings_service.validate_booking_date(preferred_date)
        if not is_valid_date:
            raise BadRequestException(
                message="Invalid booking date",
                errors={"preferred_date": [date_error]}
            )
        
        # Reject past time: requested slot start must be after current time (app timezone)
        from app.services.appointment_request_service import get_est_datetime, get_app_timezone
        now_app = get_est_datetime()
        requested_start_naive = datetime.combine(preferred_date, preferred_time)
        tz = get_app_timezone()
        requested_start = requested_start_naive if requested_start_naive.tzinfo else tz.localize(requested_start_naive)
        if requested_start <= now_app:
            raise BadRequestException(
                message="Cannot book a slot in the past",
                errors={
                    "preferred_date": ["The selected date and time must be in the future."],
                    "preferred_time": ["Please select a time that is after the current time."]
                }
            )
        
        # Calculate end time based on slot duration
        # Get duration from availability assignment or doctor service
        duration_minutes = None
        
        if doctor_service_availability_id:
            availability_assignment = self.db.query(DoctorServiceAvailability).join(
                DoctorAvailability,
                DoctorServiceAvailability.availability_id == DoctorAvailability.id
            ).filter(
                DoctorServiceAvailability.id == doctor_service_availability_id,
                DoctorServiceAvailability.service_id == service_id,
                DoctorAvailability.doctor_id == doctor_id,
                DoctorServiceAvailability.consultation_mode == consultation_mode
            ).first()
            
            if availability_assignment:
                duration_minutes = availability_assignment.slot_duration_minutes
        
        if not duration_minutes:
            # Fallback to doctor service default
            from app.models.doctor_service import DoctorService
            python_weekday = preferred_date.weekday()
            day_of_week = (python_weekday + 1) % 7
            
            doctor_service = self.db.query(DoctorService).filter(
                DoctorService.doctor_id == doctor_id,
                DoctorService.service_id == service_id,
                DoctorService.is_active == True,
                DoctorService.day_of_week == day_of_week
            ).first()
            
            if not doctor_service:
                doctor_service = self.db.query(DoctorService).filter(
                    DoctorService.doctor_id == doctor_id,
                    DoctorService.service_id == service_id,
                    DoctorService.is_active == True,
                    DoctorService.day_of_week.is_(None)
                ).first()
            
            if not doctor_service:
                raise BadRequestException(
                    message="Service not assigned to doctor",
                    errors={"service_id": ["This service is not assigned to the doctor for this day"]}
                )
            
            duration_minutes = doctor_service.slot_duration_minutes
        
        # Calculate end time
        start_datetime = datetime.combine(preferred_date, preferred_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_time = end_datetime.time()
        
        # Validate slot availability
        if not self.slot_generator.is_slot_available(
            doctor_id=doctor_id,
            service_id=service_id,
            slot_start=start_datetime,
            slot_end=end_datetime,
            consultation_mode=consultation_mode
        ):
            raise BadRequestException(
                message="Time slot not available",
                errors={
                    "preferred_time": ["The selected time slot is no longer available. Please select another time."]
                }
            )
        
        # Check for existing appointments at the same time
        existing_appointment = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == preferred_date,
            Appointment.start_time == preferred_time,
            Appointment.status.in_(['SCHEDULED', 'CONFIRMED']),
            Appointment.deleted_at.is_(None)
        ).first()
        
        if existing_appointment:
            raise BadRequestException(
                message="Time slot already booked",
                errors={
                    "preferred_time": ["This time slot has already been booked. Please select another time."]
                }
            )
        
        # Resolve pricing
        try:
            price_amount, currency, pricing_source = self.pricing_resolver.resolve_price(
                doctor_id=doctor_id,
                service_id=service_id,
                doctor_service_availability_id=doctor_service_availability_id,
                consultation_mode=consultation_mode,
                currency=None  # No currency validation - get from pricing source
            )
        except BadRequestException as e:
            raise BadRequestException(
                message="Pricing unavailable",
                errors=e.errors or {"price": ["Unable to determine price for this appointment"]}
            )
        
        # Create appointment (status: SCHEDULED for appointment request)
        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient.id,
            service_id=service_id,
            clinic_id=doctor.clinic_id,
            doctor_service_availability_id=doctor_service_availability_id,
            appointment_date=preferred_date,
            start_time=preferred_time,
            end_time=end_time,
            status='SCHEDULED',  # Appointment request status
            consultation_mode=consultation_mode,
            duration_minutes=duration_minutes,
            price_amount=price_amount,
            currency=currency,
            pricing_source=pricing_source
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        logger.info(
            f"Appointment request created: {appointment.id} by patient {patient.id} "
            f"for doctor {doctor_id} on {preferred_date} at {preferred_time} "
            f"(mode: {consultation_mode}, price: {price_amount} {currency})"
        )
        
        return appointment
