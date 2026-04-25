"""
Appointment Service
Business logic for appointment creation with pricing snapshot
"""

from typing import Optional
from uuid import UUID
from datetime import date, time, datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from loguru import logger

from app.models.appointment import Appointment
from app.models.appointment_request import AppointmentRequest
from app.models.appointment_payment import AppointmentPayment
from app.models.user import User
from app.utils.pricing_resolver import PricingResolver
from app.utils.slot_generator import SlotGenerator
from app.services.audit_service import AuditService
from app.services.service_commission_service import set_payment_commission
from app.core.security import CurrentUser, UserRole
from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException
)
from app.utils.waiver_helper import get_request_price_display


class AppointmentService:
    """
    Service for managing appointments
    
    Key features:
    - Stores pricing snapshot at booking time
    - Price never changes after booking
    - No recalculation on reschedule
    """
    
    def __init__(self, db: Session):
        """
        Initialize appointment service
        
        Args:
            db: Database session
        """
        self.db = db
        self.audit_service = AuditService(db)
        self.pricing_resolver = PricingResolver(db)
        self.slot_generator = SlotGenerator(db)
    
    def create_appointment(
        self,
        current_user: CurrentUser,
        doctor_id: UUID,
        service_id: UUID,
        appointment_date: date,
        start_time: time,
        end_time: time,
        doctor_service_availability_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Appointment:
        """
        Create a new appointment with pricing snapshot
        
        Pricing snapshot is captured at booking time and stored:
        - price_amount: Price at booking time
        - currency: Currency at booking time (from pricing source)
        - pricing_source: Source of price (availability | doctor | global)
        
        Rules:
        - Price must never change after booking
        - No recalculation on reschedule
        - Currency comes from pricing source, not defaulted
        
        Args:
            current_user: Current user (patient)
            doctor_id: Doctor user ID
            service_id: Service ID
            appointment_date: Appointment date
            start_time: Appointment start time
            end_time: Appointment end time
            doctor_service_availability_id: Optional availability assignment ID
            currency: Optional expected currency (for validation only, no default)
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created Appointment object
            
        Raises:
            NotFoundException: If doctor, service, or patient not found
            ForbiddenException: If access denied
            BadRequestException: If validation fails or no price found
        """
        # Get patient user
        patient = self.db.query(User).filter(
            User.id == current_user.id,
            User.deleted_at.is_(None)
        ).first()
        
        if not patient:
            raise NotFoundException(
                message="Patient not found",
                errors={"patient_id": ["Patient account not found"]}
            )
        
        # Validate doctor exists
        doctor = self.db.query(User).filter(
            User.id == doctor_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not doctor:
            raise NotFoundException(
                message="Doctor not found",
                errors={"doctor_id": ["Doctor account not found"]}
            )
        
        if not doctor.has_role(UserRole.DOCTOR):
            raise BadRequestException(
                message="Invalid doctor",
                errors={"doctor_id": ["The specified user is not a doctor"]}
            )
        
        # Validate service exists
        from app.models.service import Service
        service = self.db.query(Service).filter(
            Service.id == service_id,
            Service.deleted_at.is_(None)
        ).first()
        
        if not service:
            raise NotFoundException(
                message="Service not found",
                errors={"service_id": ["Service not found"]}
            )
        
        # Validate clinic match
        if doctor.clinic_id != service.clinic_id:
            raise BadRequestException(
                message="Clinic mismatch",
                errors={"clinic_id": ["Doctor and service must be in the same clinic"]}
            )
        
        # Get consultation_mode and validate service exists for availability + mode
        consultation_mode = None
        duration_minutes = None
        
        if doctor_service_availability_id:
            from app.models.doctor_service_availability import DoctorServiceAvailability
            from app.models.availability import DoctorAvailability
            
            # Get availability assignment and validate service exists for this availability + mode
            availability_assignment = self.db.query(DoctorServiceAvailability).join(
                DoctorAvailability,
                DoctorServiceAvailability.availability_id == DoctorAvailability.id
            ).filter(
                DoctorServiceAvailability.id == doctor_service_availability_id,
                DoctorServiceAvailability.service_id == service_id,
                DoctorAvailability.doctor_id == doctor_id
            ).first()
            
            if not availability_assignment:
                raise BadRequestException(
                    message="Service not available for this availability",
                    errors={
                        "doctor_service_availability_id": [
                            "The specified service is not assigned to this availability block"
                        ]
                    }
                )
            
            consultation_mode = availability_assignment.consultation_mode
            duration_minutes = availability_assignment.slot_duration_minutes
            
            # Validate consultation_mode is valid
            from app.core.security import ConsultationMode
            try:
                ConsultationMode(consultation_mode)
            except ValueError:
                raise BadRequestException(
                    message="Invalid consultation mode",
                    errors={
                        "consultation_mode": [f"Invalid consultation mode: {consultation_mode}"]
                    }
                )
        else:
            # No availability assignment - use default mode and get duration from doctor_services
            from app.core.security import ConsultationMode
            consultation_mode = ConsultationMode.default()
            
            # Get slot duration from doctor_services (day-specific or default)
            python_weekday = appointment_date.weekday()
            day_of_week = (python_weekday + 1) % 7  # Convert to 0=Sunday format
            
            from app.models.doctor_service import DoctorService
            doctor_service = self.db.query(DoctorService).filter(
                DoctorService.doctor_id == doctor_id,
                DoctorService.service_id == service_id,
                DoctorService.is_active == True,
                DoctorService.day_of_week == day_of_week
            ).first()
            
            if not doctor_service:
                # Try default (day_of_week IS NULL)
                doctor_service = self.db.query(DoctorService).filter(
                    DoctorService.doctor_id == doctor_id,
                    DoctorService.service_id == service_id,
                    DoctorService.is_active == True,
                    DoctorService.day_of_week.is_(None)
                ).first()
            
            if not doctor_service:
                raise BadRequestException(
                    message="Service not assigned to doctor",
                    errors={
                        "service_id": ["This service is not assigned to the doctor for this day"]
                    }
                )
            
            duration_minutes = doctor_service.slot_duration_minutes
        
        # Validate slot duration matches expected duration
        actual_duration = int((datetime.combine(appointment_date, end_time) - datetime.combine(appointment_date, start_time)).total_seconds() / 60)
        if actual_duration != duration_minutes:
            raise BadRequestException(
                message="Slot duration mismatch",
                errors={
                    "start_time": [f"Expected slot duration is {duration_minutes} minutes, but provided duration is {actual_duration} minutes"],
                    "end_time": [f"Slot duration must match the service duration of {duration_minutes} minutes"]
                }
            )
        
        # Validate slot availability (mode-aware)
        slot_start = datetime.combine(appointment_date, start_time)
        slot_end = datetime.combine(appointment_date, end_time)
        
        if not self.slot_generator.is_slot_available(
            doctor_id=doctor_id,
            service_id=service_id,
            slot_start=slot_start,
            slot_end=slot_end,
            consultation_mode=consultation_mode
        ):
            raise BadRequestException(
                message="Slot not available",
                errors={
                    "appointment_date": ["The selected time slot is not available"],
                    "start_time": ["Please select a different time"]
                }
            )
        
        # Resolve pricing (snapshot at booking time, mode-aware)
        try:
            price_amount, resolved_currency, pricing_source = self.pricing_resolver.resolve_price(
                doctor_id=doctor_id,
                service_id=service_id,
                doctor_service_availability_id=doctor_service_availability_id,
                consultation_mode=consultation_mode,
                currency=currency
            )
        except BadRequestException as e:
            # Re-raise with context
            raise BadRequestException(
                message="Pricing unavailable",
                errors=e.errors or {"price": ["Unable to determine price for this appointment"]}
            )
        
        # Create appointment with complete snapshot (immutable after creation)
        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient.id,
            service_id=service_id,
            clinic_id=doctor.clinic_id,
            doctor_service_availability_id=doctor_service_availability_id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status='SCHEDULED',
            # Complete snapshot (immutable after creation)
            consultation_mode=consultation_mode,
            duration_minutes=duration_minutes,
            price_amount=price_amount,
            currency=resolved_currency,
            pricing_source=pricing_source
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        # Audit log: Appointment created (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=patient.id,
            action="APPOINTMENT_CREATED",
            entity_type="appointment",
            entity_id=appointment.id,
            audit_metadata={
                "doctor_id": str(doctor_id),
                "service_id": str(service_id),
                "appointment_date": appointment_date.isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Audit log: Appointment booked with mode (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=patient.id,
            action="APPOINTMENT_BOOKED_WITH_MODE",
            entity_type="appointment",
            entity_id=appointment.id,
            audit_metadata={
                "appointment_id": str(appointment.id),
                "service_id": str(service_id),
                "consultation_mode": consultation_mode,
                "duration_minutes": duration_minutes
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Audit log: Price locked (immutable snapshot) (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=patient.id,
            action="APPOINTMENT_PRICE_LOCKED",
            entity_type="appointment",
            entity_id=appointment.id,
            audit_metadata={
                "appointment_id": str(appointment.id),
                "consultation_mode": consultation_mode,
                "duration_minutes": duration_minutes,
                "price_amount": float(price_amount),
                "currency": resolved_currency,
                "pricing_source": pricing_source
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            f"Appointment created: {appointment.id} by patient {patient.id} "
            f"with mode={consultation_mode}, duration={duration_minutes}min, "
            f"price={price_amount} {resolved_currency} (source: {pricing_source}) locked"
        )
        
        return appointment
    
    def reschedule_appointment(
        self,
        current_user: CurrentUser,
        appointment_id: UUID,
        new_appointment_date: date,
        new_start_time: time,
        new_end_time: time,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Appointment:
        """
        Reschedule an appointment
        
        Important: Pricing snapshot is NOT recalculated.
        Original price from booking time is preserved.
        
        Args:
            current_user: Current user
            appointment_id: Appointment ID
            new_appointment_date: New appointment date
            new_start_time: New start time
            new_end_time: New end time
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated Appointment object
            
        Raises:
            NotFoundException: If appointment not found
            ForbiddenException: If not authorized
            BadRequestException: If validation fails
        """
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if not appointment:
            raise NotFoundException(
                message="Appointment not found",
                errors={"appointment_id": ["Appointment not found"]}
            )
        
        # Validate ownership (patient or doctor can reschedule)
        if appointment.patient_id != current_user.id and appointment.doctor_id != current_user.id:
            raise ForbiddenException(
                message="Access denied",
                errors={"appointment_id": ["You can only reschedule your own appointments"]}
            )
        
        # Get consultation_mode from original appointment's availability assignment
        consultation_mode = None
        if appointment.doctor_service_availability_id:
            from app.models.doctor_service_availability import DoctorServiceAvailability
            availability_assignment = self.db.query(DoctorServiceAvailability).filter(
                DoctorServiceAvailability.id == appointment.doctor_service_availability_id
            ).first()
            if availability_assignment:
                consultation_mode = availability_assignment.consultation_mode
        
        # Validate new slot availability (mode-aware)
        slot_start = datetime.combine(new_appointment_date, new_start_time)
        slot_end = datetime.combine(new_appointment_date, new_end_time)
        
        if not self.slot_generator.is_slot_available(
            doctor_id=appointment.doctor_id,
            service_id=appointment.service_id,
            slot_start=slot_start,
            slot_end=slot_end,
            consultation_mode=consultation_mode
        ):
            raise BadRequestException(
                message="Slot not available",
                errors={
                    "appointment_date": ["The selected time slot is not available"],
                    "start_time": ["Please select a different time"]
                }
            )
        
        # Update appointment (pricing snapshot remains unchanged)
        appointment.appointment_date = new_appointment_date
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        
        self.db.commit()
        self.db.refresh(appointment)
        
        # Audit log (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="APPOINTMENT_RESCHEDULED",
            entity_type="appointment",
            entity_id=appointment.id,
            audit_metadata={
                "appointment_id": str(appointment_id),
                "new_appointment_date": new_appointment_date.isoformat(),
                "price_amount": float(appointment.price_amount),  # Original price preserved
                "pricing_source": appointment.pricing_source  # Original source preserved
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            f"Appointment {appointment_id} rescheduled. "
            f"Original price {appointment.price_amount} {appointment.currency} preserved."
        )
        
        return appointment

    def _get_avatar_url(self, avatar_path: Optional[str]) -> Optional[str]:
        """
        Generate full URL for avatar image
        
        Args:
            avatar_path: Relative path to avatar (e.g., "uploads/avatars/user_id.jpg")
        
        Returns:
            Full URL (e.g., "http://localhost:8000/uploads/avatars/user_id.jpg") or None
        """
        if not avatar_path:
            return None
        
        # Remove leading slash if present
        avatar_path = avatar_path.lstrip('/')
        
        # Construct full URL
        base_url = settings.BASE_URL.rstrip('/')
        return f"{base_url}/{avatar_path}"

    def _get_chat_room_id(self, doctor_id: UUID, patient_id: UUID, appointment_id: Optional[UUID] = None) -> Optional[UUID]:
        """
        Get chat room ID for a doctor-patient pair.
        Returns None if chat room doesn't exist or if chat service is not accessible.
        """
        try:
            # Try to query chat_rooms table directly (if in same database)
            # Using raw SQL to avoid import issues if table doesn't exist
            from sqlalchemy import text
            
            query = text("""
                SELECT id 
                FROM chat_rooms 
                WHERE doctor_id = :doctor_id 
                  AND patient_id = :patient_id 
                  AND status = 'active'
                LIMIT 1
            """)
            
            result = self.db.execute(
                query,
                {"doctor_id": str(doctor_id), "patient_id": str(patient_id)}
            ).first()
            
            if result:
                return UUID(result[0])
            return None
        except Exception as e:
            # If table doesn't exist or query fails, return None
            # This is expected if chat service is in a separate database
            logger.debug(f"Could not fetch chat room ID: {str(e)}")
            return None
    
    def list_patient_appointments_grouped(self, current_user: CurrentUser) -> dict:
        """
        List patient appointments grouped by Upcoming, Pending, and Past

        Upcoming: Appointments that are accepted by the doctor (created from ACCEPTED requests) 
                  with appointment_date >= today
        Pending: AppointmentRequests that are NOT yet accepted by the doctor (status: PENDING)
        Past: Appointments whose appointment_date has passed (appointment_date < today)
        """
        from app.models.appointment import Appointment
        from app.models.appointment_request import AppointmentRequest
        from app.models.appointment_payment import AppointmentPayment
        from app.models.user import User
        from app.models.service import Service
        from datetime import date

        today = date.today()

        # Get all appointment requests for this patient to check which ones have appointments
        # Also fetch all payments in one query to avoid N+1
        all_requests = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.patient_id == current_user.id,
            AppointmentRequest.deleted_at.is_(None)
        ).all()
        
        request_ids = [req.id for req in all_requests]
        
        # Fetch all payments for these requests in one query
        all_payments = {}
        if request_ids:
            payments = self.db.query(AppointmentPayment).filter(
                AppointmentPayment.appointment_request_id.in_(request_ids)
            ).all()
            for payment in payments:
                all_payments[payment.appointment_request_id] = payment
        
        # Fetch all chat rooms for this patient in one query to avoid N+1
        chat_rooms_map = {}  # {(doctor_id, patient_id): chat_room_id}
        try:
            from sqlalchemy import text
            query = text("""
                SELECT id, doctor_id, patient_id, appointment_id
                FROM chat_rooms 
                WHERE patient_id = :patient_id 
                  AND status = 'active'
            """)
            result = self.db.execute(
                query,
                {"patient_id": str(current_user.id)}
            ).fetchall()
            
            for row in result:
                try:
                    # Access columns by index for reliability with raw SQL
                    if len(row) >= 3:
                        chat_room_id = UUID(str(row[0])) if row[0] else None
                        doctor_id = UUID(str(row[1])) if row[1] else None
                        patient_id = UUID(str(row[2])) if row[2] else None
                        if chat_room_id and doctor_id and patient_id:
                            key = (doctor_id, patient_id)
                            chat_rooms_map[key] = chat_room_id
                except (ValueError, TypeError, IndexError) as e:
                    logger.debug(f"Error processing chat room row: {e}")
                    continue
        except Exception as e:
            # If table doesn't exist or query fails, chat_rooms_map will remain empty
            logger.debug(f"Could not fetch chat rooms: {str(e)}")
        
        # Get request IDs that have corresponding appointments (paid/accepted requests)
        request_ids_with_appointments = set()
        # Map to store payment status for requests
        request_payment_status = {}  # {request_id: "paid" or "pending"}
        
        for req in all_requests:
            payment = all_payments.get(req.id)
            
            if payment and payment.status == 'COMPLETED':
                # Check if appointment exists
                appointment = self.db.query(Appointment).filter(
                    Appointment.doctor_id == req.doctor_id,
                    Appointment.patient_id == req.patient_id,
                    Appointment.service_id == req.service_id,
                    Appointment.appointment_date == req.preferred_date,
                    Appointment.start_time == req.preferred_time,
                    Appointment.deleted_at.is_(None)
                ).first()
                if appointment:
                    request_ids_with_appointments.add(req.id)
                    request_payment_status[req.id] = "paid"
                else:
                    request_payment_status[req.id] = "processing"  # Payment completed but appointment not created yet
            elif payment:
                # Payment exists but not completed
                request_payment_status[req.id] = payment.status.lower()  # "pending", "processing", "failed", "cancelled"
            else:
                # No payment record - payment is pending
                request_payment_status[req.id] = "pending"

        # Create a reverse map: appointment details -> request_id (to find payment status for appointments)
        # This helps us find the payment status for appointments via their corresponding requests
        appointment_to_request_map = {}  # Maps appointment key to request_id
        for req in all_requests:
            if req.id in request_ids_with_appointments:
                # Create a key from appointment details
                key = (
                    str(req.doctor_id),
                    str(req.patient_id),
                    str(req.service_id),
                    str(req.preferred_date),
                    str(req.preferred_time)
                )
                appointment_to_request_map[key] = req.id

        # Fetch all chat rooms for this patient in one query to avoid N+1
        # Only check by doctor_id and patient_id (not appointment_id)
        chat_rooms_map = {}  # {(doctor_id, patient_id): chat_room_id}
        try:
            from sqlalchemy import text
            # Use CAST for UUID type conversion
            query = text("""
                SELECT id, doctor_id, patient_id
                FROM chat_rooms 
                WHERE patient_id = CAST(:patient_id AS uuid)
                  AND status = 'active'
            """)
            result = self.db.execute(
                query,
                {"patient_id": str(current_user.id)}
            ).fetchall()
            
            logger.info(f"Found {len(result)} chat rooms for patient {current_user.id}")
            for row in result:
                try:
                    # Handle UUID conversion - PostgreSQL returns UUID objects or strings
                    chat_room_id = row[0] if isinstance(row[0], UUID) else UUID(str(row[0]))
                    doctor_id = row[1] if isinstance(row[1], UUID) else UUID(str(row[1]))
                    patient_id = row[2] if isinstance(row[2], UUID) else UUID(str(row[2]))
                    key = (doctor_id, patient_id)
                    chat_rooms_map[key] = chat_room_id
                    logger.info(f"Mapped chat room {chat_room_id} for doctor {doctor_id} and patient {patient_id}")
                except Exception as e:
                    logger.warning(f"Error processing chat room row: {row}, error: {str(e)}", exc_info=True)
                    continue
        except Exception as e:
            # If table doesn't exist or query fails, chat_rooms_map will remain empty
            logger.warning(f"Could not fetch chat rooms for patient {current_user.id}: {str(e)}", exc_info=True)

        # Upcoming: Appointments with appointment_date >= today (these are accepted and paid)
        upcoming_q = self.db.query(Appointment).options(
            joinedload(Appointment.doctor).joinedload(User.medical_services),
            joinedload(Appointment.service)
        ).filter(
            Appointment.patient_id == current_user.id,
            Appointment.deleted_at.is_(None),
            Appointment.appointment_date >= today
        ).order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc()).all()

        # Also include ACCEPTED appointment requests that haven't been paid yet (upcoming but need payment)
        accepted_upcoming_query = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.patient_id == current_user.id,
            AppointmentRequest.deleted_at.is_(None),
            AppointmentRequest.status == 'ACCEPTED',
            AppointmentRequest.preferred_date >= today
        )
        if request_ids_with_appointments:
            accepted_upcoming_query = accepted_upcoming_query.filter(
                ~AppointmentRequest.id.in_(request_ids_with_appointments)
            )
        accepted_upcoming_requests = accepted_upcoming_query.order_by(
            AppointmentRequest.preferred_date.asc(), 
            AppointmentRequest.preferred_time.asc()
        ).all()

        # Past: Appointments with appointment_date < today (dates that have passed)
        past_q = self.db.query(Appointment).options(
            joinedload(Appointment.doctor).joinedload(User.medical_services),
            joinedload(Appointment.service)
        ).filter(
            Appointment.patient_id == current_user.id,
            Appointment.deleted_at.is_(None),
            Appointment.appointment_date < today
        ).order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc()).all()

        # Pending: AppointmentRequests with status PENDING (not yet accepted by doctor)
        pending_q = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.patient_id == current_user.id,
            AppointmentRequest.deleted_at.is_(None),
            AppointmentRequest.status == 'PENDING'
        ).order_by(AppointmentRequest.created_at.desc()).all()

        # Fetch video sessions for all appointments (from shared database)
        # Note: video_sessions table is managed by webinar-service, query directly
        from sqlalchemy import text
        appointment_ids = [a.id for a in upcoming_q] + [a.id for a in past_q]
        video_sessions_map = {}  # {appointment_id: video_session}
        if appointment_ids:
            try:
                # Query video_sessions table directly (model moved to webinar-service)
                # Use individual queries per appointment (safer, handles errors gracefully)
                for appointment_id in appointment_ids:
                    try:
                        query = text("""
                            SELECT appointment_id, session_id, channel_name
                            FROM video_sessions
                            WHERE appointment_id = :appointment_id AND deleted_at IS NULL
                            ORDER BY 
                                CASE 
                                    WHEN status IN ('scheduled', 'waiting_room', 'joining', 'doctor_joined', 'in_call', 'grace', 'completed') THEN 0
                                    ELSE 1
                                END,
                                created_at DESC,
                                retry_count DESC
                            LIMIT 1
                        """)
                        result = self.db.execute(query, {"appointment_id": str(appointment_id)})
                        row = result.fetchone()
                        if row and len(row) >= 3 and row[0]:  # row[0] = appointment_id, row[1] = session_id, row[2] = channel_name
                            # Access columns by index for reliability with raw SQL
                            fetched_appointment_id = UUID(str(row[0])) if row[0] else None
                            if fetched_appointment_id:
                                video_sessions_map[fetched_appointment_id] = {
                                    "session_id": str(row[1]) if row[1] else None,
                                    "channel_name": str(row[2]) if row[2] else None
                                }
                    except Exception as e:
                        # Skip this appointment if query fails
                        logger.debug(f"Failed to fetch video session for appointment {appointment_id}: {e}")
                        continue
            except Exception as e:
                # If video session query fails, continue without video session data
                logger.warning(f"Failed to fetch video sessions: {e}")
                video_sessions_map = {}

        def appointment_to_item(
            a: Appointment,
            chat_rooms_map: dict,
            video_sessions_map: dict,
            appointment_to_request_map: Optional[dict] = None,
            all_payments: Optional[dict] = None
        ) -> dict:
            doctor = a.doctor
            service = a.service
            # doctor profile avatar may be on profile or user
            profile_image_path = None
            try:
                profile_image_path = doctor.avatar or (doctor.profile.avatar if hasattr(doctor, 'profile') and doctor.profile else None)
            except Exception:
                profile_image_path = None
            
            # Generate full URL for profile image
            profile_image = self._get_avatar_url(profile_image_path) if profile_image_path else None

            # Get specialties from medical_services (comma-separated)
            specialty = None
            try:
                if doctor and hasattr(doctor, 'medical_services') and doctor.medical_services:
                    specialty_names = [ms.name for ms in doctor.medical_services if ms.name]
                    if specialty_names:
                        specialty = ", ".join(specialty_names)
            except Exception:
                specialty = None

            # Check payment status for this appointment
            # Fetch from appointment_payments table via the corresponding appointment_request
            payment_status = "paid"  # Default to paid since appointment exists (appointments require payment)
            try:
                # Use the reverse map to find the corresponding request_id
                appointment_key = (
                    str(a.doctor_id),
                    str(a.patient_id),
                    str(a.service_id),
                    str(a.appointment_date),
                    str(a.start_time)
                )
                request_id = appointment_to_request_map.get(appointment_key)
                
                if request_id:
                    # Use pre-fetched payment data from appointment_payments table
                    payment = all_payments.get(request_id)
                    if payment:
                        # Get status from appointment_payments table
                        if payment.status == 'COMPLETED':
                            payment_status = "paid"
                        else:
                            payment_status = payment.status.lower()  # "pending", "processing", "failed", "cancelled"
                else:
                    # If no matching request found, try direct query (edge case)
                    appointment_request = self.db.query(AppointmentRequest).filter(
                        AppointmentRequest.doctor_id == a.doctor_id,
                        AppointmentRequest.patient_id == a.patient_id,
                        AppointmentRequest.service_id == a.service_id,
                        AppointmentRequest.preferred_date == a.appointment_date,
                        AppointmentRequest.preferred_time == a.start_time,
                        AppointmentRequest.deleted_at.is_(None)
                    ).first()
                    
                    if appointment_request:
                        payment = self.db.query(AppointmentPayment).filter(
                            AppointmentPayment.appointment_request_id == appointment_request.id
                        ).first()
                        if payment:
                            payment_status = "paid" if payment.status == 'COMPLETED' else payment.status.lower()
            except Exception:
                # If we can't find payment, assume paid since appointment exists
                payment_status = "paid"

            # Get chat room ID from pre-fetched map
            lookup_key = (a.doctor_id, a.patient_id)
            chat_room_id = chat_rooms_map.get(lookup_key)
            if not chat_room_id:
                # Log for debugging
                logger.debug(f"No chat room found for appointment {a.id}, doctor {a.doctor_id}, patient {a.patient_id}")
                logger.debug(f"Available chat room keys: {list(chat_rooms_map.keys())[:5]}")  # Show first 5 keys

            # Get video session information
            video_session = video_sessions_map.get(a.id)
            channel_name = video_session.get("channel_name") if video_session else None
            session_id = video_session.get("session_id") if video_session else None

            # Waiver data from payment (appointment.price_amount is already the paid/waived amount)
            amount_before_waiver = None
            waiver_percent = None
            if appointment_to_request_map and all_payments:
                appointment_key = (
                    str(a.doctor_id),
                    str(a.patient_id),
                    str(a.service_id),
                    str(a.appointment_date),
                    str(a.start_time)
                )
                request_id = appointment_to_request_map.get(appointment_key)
                if request_id:
                    payment = all_payments.get(request_id)
                    if payment:
                        amount_before_waiver = float(payment.amount_before_waiver) if payment.amount_before_waiver is not None else None
                        waiver_percent = payment.waiver_percent

            return {
                "id": a.id,
                "doctor_id": a.doctor_id,
                "doctor_name": doctor.name if doctor else None,
                "doctor_profile_image": profile_image,
                "specialty": specialty,
                "service_id": a.service_id,
                "service_name": service.name if service else None,
                "consultation_mode": a.consultation_mode,
                "appointment_date": a.appointment_date,
                "start_time": a.start_time,
                "end_time": a.end_time,
                "status": a.status,
                "price_amount": float(a.price_amount) if a.price_amount is not None else None,
                "amount_before_waiver": amount_before_waiver,
                "waiver_percent": waiver_percent,
                "currency": a.currency,
                "duration_minutes": a.duration_minutes,
                "payment_status": payment_status,
                "chat_room_id": str(chat_room_id) if chat_room_id else None,
                "channel_name": channel_name,
                "session_id": session_id
            }

        def request_to_item(r: AppointmentRequest, chat_rooms_map: dict) -> dict:
            # Eager load medical_services relationship to avoid N+1 queries
            doctor = self.db.query(User).options(
                joinedload(User.medical_services)
            ).filter(User.id == r.doctor_id).first()
            service = self.db.query(Service).filter(Service.id == r.service_id).first()
            
            # Get profile image path (from user.avatar or profile.avatar)
            profile_image_path = None
            try:
                profile_image_path = doctor.avatar or (doctor.profile.avatar if hasattr(doctor, 'profile') and doctor.profile else None)
            except Exception:
                profile_image_path = None
            
            # Generate full URL for profile image
            profile_image = self._get_avatar_url(profile_image_path) if profile_image_path else None

            # Get specialties from medical_services (comma-separated)
            specialty = None
            try:
                if doctor and doctor.medical_services:
                    # Get names of all medical services and join with comma
                    specialty_names = [ms.name for ms in doctor.medical_services if ms.name]
                    if specialty_names:
                        specialty = ", ".join(specialty_names)
            except Exception:
                specialty = None

            # Get payment status for this appointment request
            # Use the pre-computed map if available, otherwise check directly
            payment_status = request_payment_status.get(r.id, "pending")
            
            # Get chat room ID from pre-fetched map
            lookup_key = (r.doctor_id, r.patient_id)
            chat_room_id = chat_rooms_map.get(lookup_key)
            if not chat_room_id:
                # Log for debugging
                logger.debug(f"No chat room found for request {r.id}, doctor {r.doctor_id}, patient {r.patient_id}")
                logger.debug(f"Available chat room keys: {list(chat_rooms_map.keys())[:5]}")  # Show first 5 keys

            # Apply waiver for display (price_amount = amount after waiver)
            price_after, amount_before, waiver_pct = get_request_price_display(
                self.db, float(r.price_amount) if r.price_amount is not None else None,
                doctor_waiver_percent=getattr(r, "waiver_percent", None),
            )
            return {
                "id": r.id,
                "doctor_id": r.doctor_id,
                "doctor_name": doctor.name if doctor else None,
                "doctor_profile_image": profile_image,
                "doctor_specialty": specialty,
                "service_id": r.service_id,
                "consultation_mode": r.consultation_mode,
                "preferred_date": r.preferred_date,
                "preferred_time": r.preferred_time,
                "status": r.status,
                "duration_minutes": r.duration_minutes,
                "price_amount": price_after,
                "amount_before_waiver": amount_before,
                "waiver_percent": waiver_pct,
                "currency": r.currency,
                "reason": r.reason,
                "payment_status": payment_status,
                "chat_room_id": str(chat_room_id) if chat_room_id else None
            }

        # Combine upcoming appointments and accepted requests (that haven't been paid)
        upcoming_items = [
            appointment_to_item(a, chat_rooms_map, video_sessions_map, appointment_to_request_map, all_payments)
            for a in upcoming_q
        ]
        upcoming_items.extend([request_to_item(r, chat_rooms_map) for r in accepted_upcoming_requests])
        # Sort by date and time (handle both appointment_date and preferred_date keys)
        def get_sort_key(item):
            date_val = item.get('appointment_date') or item.get('preferred_date')
            time_val = item.get('start_time') or item.get('preferred_time')
            # Use tuple for sorting - None values will be treated as smallest (sorts last)
            # Convert to string representation for comparison if needed, but date/time objects sort naturally
            return (date_val if date_val else date(2099, 12, 31), time_val if time_val else time(23, 59, 59))
        upcoming_items.sort(key=get_sort_key)

        return {
            "upcoming": upcoming_items,
            "pending": [request_to_item(r, chat_rooms_map) for r in pending_q],
            "past": [
                appointment_to_item(a, chat_rooms_map, video_sessions_map, appointment_to_request_map, all_payments)
                for a in past_q
            ]
        }
    
    def list_doctor_appointments_grouped(
        self, 
        current_user: CurrentUser,
        page: int = 1,
        per_page: int = 20,
        appointment_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> dict:
        """
        List doctor appointments grouped by Today, Upcoming, and Completed with pagination

        Today: Appointments where appointment_date == today
        Upcoming: Appointments where appointment_date > today
        Completed: Appointments where appointment_date < today OR status == 'COMPLETED'
        
        Args:
            current_user: Current doctor user
            page: Page number (default: 1)
            per_page: Items per page (default: 20)
            appointment_type: Filter by type - 'today', 'upcoming', or 'completed' (optional)
            search: Search by patient name (optional)
        """
        from app.models.appointment import Appointment
        from app.models.user import User
        from app.models.service import Service
        from datetime import date, time, datetime
        from sqlalchemy import or_, func
        from app.core.config import settings

        # Use timezone from settings for date comparison (consistent with appointment_request_service)
        app_timezone = settings.get_timezone()
        today = datetime.now(app_timezone).date()

        # Import AppointmentRequest model
        from app.models.appointment_request import AppointmentRequest
        
        # Base query for confirmed appointments with eager loading
        appointments_query = self.db.query(Appointment).options(
            joinedload(Appointment.patient).joinedload(User.profile),
            joinedload(Appointment.service)
        ).filter(
            Appointment.doctor_id == current_user.id,
            Appointment.deleted_at.is_(None)
        )
        
        # Query for accepted appointment requests (not yet converted to appointments)
        # Exclude requests that have COMPLETED payments (which means appointment was created)
        requests_query = self.db.query(AppointmentRequest).options(
            joinedload(AppointmentRequest.patient).joinedload(User.profile),
            joinedload(AppointmentRequest.service)
        ).outerjoin(
            AppointmentPayment,
            and_(
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
                AppointmentPayment.status == 'COMPLETED'
            )
        ).filter(
            AppointmentRequest.doctor_id == current_user.id,
            AppointmentRequest.status == 'ACCEPTED',
            AppointmentRequest.deleted_at.is_(None),
            AppointmentPayment.id.is_(None)  # Exclude requests with COMPLETED payments
        )
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search.lower()}%"
            # Filter appointments by patient name
            appointments_query = appointments_query.join(User, Appointment.patient_id == User.id).filter(
                func.lower(User.name).like(search_term)
            )
            # Filter requests by patient name
            requests_query = requests_query.join(User, AppointmentRequest.patient_id == User.id).filter(
                func.lower(User.name).like(search_term)
            )
        
        # Fetch all appointments and accepted requests
        all_appointments = appointments_query.all()
        all_accepted_requests = requests_query.all()
        
        # Build payment map for waiver data: (doctor_id, patient_id, service_id, appointment_date, start_time) -> payment
        payment_map = {}
        completed_payments = self.db.query(AppointmentPayment).options(
            joinedload(AppointmentPayment.appointment_request)
        ).join(
            AppointmentRequest, AppointmentPayment.appointment_request_id == AppointmentRequest.id
        ).filter(
            AppointmentRequest.doctor_id == current_user.id,
            AppointmentPayment.status == 'COMPLETED'
        ).all()
        for payment in completed_payments:
            req = payment.appointment_request
            if req:
                key = (req.doctor_id, req.patient_id, req.service_id, req.preferred_date, req.preferred_time)
                payment_map[key] = payment
        
        # Convert accepted requests to appointment-like objects for processing
        # Create a unified list that includes both appointments and accepted requests
        class AppointmentLike:
            """Wrapper to make AppointmentRequest look like Appointment for filtering"""
            def __init__(self, request: AppointmentRequest):
                self.id = request.id
                self.patient_id = request.patient_id
                self.patient = request.patient
                self.service_id = request.service_id
                self.service = request.service
                self.appointment_date = request.preferred_date
                self.start_time = request.preferred_time
                # Calculate end_time from start_time + duration
                if request.preferred_time and request.duration_minutes:
                    from datetime import timedelta
                    start_datetime = datetime.combine(request.preferred_date, request.preferred_time)
                    end_datetime = start_datetime + timedelta(minutes=request.duration_minutes)
                    self.end_time = end_datetime.time()
                else:
                    self.end_time = None
                self.status = 'ACCEPTED'  # Accepted requests are treated as accepted status
                self.price_amount = request.price_amount
                self.currency = request.currency
                self.duration_minutes = request.duration_minutes
                self.consultation_mode = request.consultation_mode
                self.is_request = True  # Flag to identify this is from a request
                self.request_id = request.id
                self.waiver_percent = getattr(request, "waiver_percent", None)
        
        # Convert accepted requests to appointment-like objects
        accepted_requests_as_appointments = [AppointmentLike(req) for req in all_accepted_requests]
        
        # Combine appointments and accepted requests
        all_items = list(all_appointments) + accepted_requests_as_appointments

        # Fetch video sessions for all appointments (from shared database)
        # Note: video_sessions table is managed by webinar-service, query directly
        from sqlalchemy import text
        appointment_ids = [a.id for a in all_appointments]
        video_sessions_map = {}  # {appointment_id: video_session}
        if appointment_ids:
            try:
                # Query video_sessions table directly (model moved to webinar-service)
                # Use individual queries per appointment (safer, handles errors gracefully)
                for appointment_id in appointment_ids:
                    try:
                        query = text("""
                            SELECT appointment_id, session_id, channel_name
                            FROM video_sessions
                            WHERE appointment_id = :appointment_id AND deleted_at IS NULL
                            ORDER BY 
                                CASE 
                                    WHEN status IN ('scheduled', 'waiting_room', 'joining', 'doctor_joined', 'in_call', 'grace', 'completed') THEN 0
                                    ELSE 1
                                END,
                                created_at DESC,
                                retry_count DESC
                            LIMIT 1
                        """)
                        result = self.db.execute(query, {"appointment_id": str(appointment_id)})
                        row = result.fetchone()
                        if row and len(row) >= 3 and row[0]:  # row[0] = appointment_id, row[1] = session_id, row[2] = channel_name
                            # Access columns by index for reliability with raw SQL
                            fetched_appointment_id = UUID(str(row[0])) if row[0] else None
                            if fetched_appointment_id:
                                video_sessions_map[fetched_appointment_id] = {
                                    "session_id": str(row[1]) if row[1] else None,
                                    "channel_name": str(row[2]) if row[2] else None
                                }
                    except Exception as e:
                        # Skip this appointment if query fails
                        logger.debug(f"Failed to fetch video session for appointment {appointment_id}: {e}")
                        continue
            except Exception as e:
                # If video session query fails, continue without video session data
                logger.warning(f"Failed to fetch video sessions: {e}")
                video_sessions_map = {}

        def appointment_to_item(a, payment_map: dict) -> dict:
            patient = a.patient
            service = a.service
            
            # Get patient profile image
            profile_image_path = None
            try:
                profile_image_path = patient.avatar or (patient.profile.avatar if hasattr(patient, 'profile') and patient.profile else None)
            except Exception:
                profile_image_path = None
            
            # Generate full URL for profile image
            profile_image = self._get_avatar_url(profile_image_path) if profile_image_path else None

            # Get patient gender and age from profile
            gender = None
            age = None
            try:
                if patient and hasattr(patient, 'profile') and patient.profile:
                    profile = patient.profile
                    gender = profile.gender
                    if profile.date_of_birth:
                        dob = profile.date_of_birth
                        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except Exception:
                pass

            # Check if this is from an appointment request
            is_request = getattr(a, 'is_request', False)
            request_id = getattr(a, 'request_id', None)

            # Waiver data: for requests use current waiver; for appointments use payment record
            price_amount = float(a.price_amount) if a.price_amount is not None else None
            amount_before_waiver = None
            waiver_percent = None
            if is_request:
                price_after, amount_before, waiver_pct = get_request_price_display(
                    self.db, price_amount,
                    doctor_waiver_percent=getattr(a, "waiver_percent", None),
                )
                price_amount = price_after
                amount_before_waiver = amount_before
                waiver_percent = waiver_pct
            else:
                key = (a.doctor_id, a.patient_id, a.service_id, a.appointment_date, a.start_time)
                payment = payment_map.get(key)
                if payment:
                    amount_before_waiver = float(payment.amount_before_waiver) if payment.amount_before_waiver is not None else None
                    waiver_percent = payment.waiver_percent

            # Get video session information (only for actual appointments, not requests)
            channel_name = None
            session_id = None
            if not is_request and hasattr(a, 'id'):
                video_session = video_sessions_map.get(a.id)
                if video_session:
                    channel_name = video_session.get("channel_name")
                    session_id = video_session.get("session_id")

            return {
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "patient_name": patient.name if patient else None,
                "patient_profile_image": profile_image,
                "patient_gender": gender,
                "patient_age": age,
                "service_id": str(a.service_id),
                "service_name": service.name if service else None,
                "consultation_mode": a.consultation_mode,
                "appointment_date": a.appointment_date.isoformat() if a.appointment_date else None,
                "start_time": str(a.start_time) if a.start_time else None,
                "end_time": str(a.end_time) if a.end_time else None,
                "status": a.status,
                "price_amount": price_amount,
                "amount_before_waiver": amount_before_waiver,
                "waiver_percent": waiver_percent,
                "currency": "XCG",
                "duration_minutes": a.duration_minutes,
                "is_appointment_request": is_request,  # Indicate if this is from a request
                "appointment_request_id": str(request_id) if request_id else None,
                "channel_name": channel_name,
                "session_id": session_id
            }

        # Helper function to paginate a list
        def paginate_list(items: list, page: int, per_page: int) -> dict:
            total = len(items)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_items = items[start:end]
            return {
                "data": paginated_items,
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "last_page": (total + per_page - 1) // per_page if total > 0 else 1,
                "from": start + 1 if total > 0 else 0,
                "to": min(end, total) if total > 0 else 0
            }

        # Today: appointments and accepted requests where appointment_date == today
        today_appts = [a for a in all_items if a.appointment_date and a.appointment_date == today]
        # Sort by start_time (earliest first)
        today_appts.sort(key=lambda a: a.start_time or time(23, 59, 59))
        today_appointments = [appointment_to_item(a, payment_map) for a in today_appts]
        
        logger.info(f"Today appointments: {len(today_appts)} found for date {today} (appointments: {len(all_appointments)}, accepted requests: {len(all_accepted_requests)})")

        # Upcoming: appointments and accepted requests where appointment_date > today (only future dates, NOT today)
        # This ensures upcoming only shows future appointments, not today's
        upcoming_appts = [a for a in all_items if a.appointment_date and a.appointment_date > today]
        # Sort by appointment_date (soonest first), then start_time
        upcoming_appts.sort(key=lambda a: (a.appointment_date or date(2099, 12, 31), a.start_time or time(23, 59, 59)))
        upcoming_appointments = [appointment_to_item(a, payment_map) for a in upcoming_appts]
        
        logger.info(f"Upcoming appointments: {len(upcoming_appts)} found (date > {today})")

        # Completed: appointments where appointment_date < today OR status == 'COMPLETED'
        # Note: Only include confirmed appointments in completed (not accepted requests)
        completed_appts = [
            a for a in all_appointments 
            if a.appointment_date and (a.appointment_date < today or a.status == 'COMPLETED')
        ]
        # Sort by appointment_date descending (most recent first), then start_time
        completed_appts.sort(
            key=lambda a: (a.appointment_date or date(1900, 1, 1), a.start_time or time(23, 59, 59)),
            reverse=True
        )
        completed_appointments = [appointment_to_item(a, payment_map) for a in completed_appts]

        # Apply type filter if provided
        if appointment_type:
            appointment_type_lower = appointment_type.lower()
            if appointment_type_lower == 'today':
                result_data = paginate_list(today_appointments, page, per_page)
                return {
                    "today": result_data,
                    "upcoming": {"data": [], "current_page": 1, "per_page": per_page, "total": 0, "last_page": 1, "from": 0, "to": 0},
                    "completed": {"data": [], "current_page": 1, "per_page": per_page, "total": 0, "last_page": 1, "from": 0, "to": 0}
                }
            elif appointment_type_lower == 'upcoming':
                result_data = paginate_list(upcoming_appointments, page, per_page)
                return {
                    "today": {"data": [], "current_page": 1, "per_page": per_page, "total": 0, "last_page": 1, "from": 0, "to": 0},
                    "upcoming": result_data,
                    "completed": {"data": [], "current_page": 1, "per_page": per_page, "total": 0, "last_page": 1, "from": 0, "to": 0}
                }
            elif appointment_type_lower == 'completed':
                result_data = paginate_list(completed_appointments, page, per_page)
                return {
                    "today": {"data": [], "current_page": 1, "per_page": per_page, "total": 0, "last_page": 1, "from": 0, "to": 0},
                    "upcoming": {"data": [], "current_page": 1, "per_page": per_page, "total": 0, "last_page": 1, "from": 0, "to": 0},
                    "completed": result_data
                }

        # Return all groups with pagination
        return {
            "today": paginate_list(today_appointments, page, per_page),
            "upcoming": paginate_list(upcoming_appointments, page, per_page),
            "completed": paginate_list(completed_appointments, page, per_page)
        }
    
    def get_doctor_appointments_grouped_by_id(
        self, 
        doctor_id: UUID,
        appointment_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """
        Get doctor appointments with pagination, search, and type filter for a specific doctor ID
        
        This method is similar to list_doctor_appointments_grouped but accepts a doctor_id
        instead of using current_user. Useful for staff viewing their assigned doctor's appointments.
        
        Includes both confirmed appointments and ACCEPTED appointment requests.
        Uses application timezone (from settings) for consistent date comparisons.
        
        Args:
            doctor_id: Doctor user ID to get appointments for
            appointment_type: Filter by type - 'today' or 'upcoming' (optional)
            search: Search by patient name (optional)
            page: Page number (default: 1)
            per_page: Items per page (default: 20)
            
        Returns:
            Dictionary with paginated appointment list and pagination metadata
        """
        from app.models.appointment import Appointment
        from app.models.user import User
        from app.models.service import Service
        from datetime import date, time, datetime
        from sqlalchemy import or_, func
        from app.core.config import settings

        # Use timezone from settings for date comparison (consistent with appointment_request_service)
        app_timezone = settings.get_timezone()
        today = datetime.now(app_timezone).date()

        # Import AppointmentRequest model
        from app.models.appointment_request import AppointmentRequest
        
        # Base query for confirmed appointments with eager loading
        appointments_query = self.db.query(Appointment).options(
            joinedload(Appointment.patient).joinedload(User.profile),
            joinedload(Appointment.service)
        ).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.deleted_at.is_(None)
        )
        
        # Query for accepted appointment requests (not yet converted to appointments)
        # Exclude requests that have COMPLETED payments (which means appointment was created)
        requests_query = self.db.query(AppointmentRequest).options(
            joinedload(AppointmentRequest.patient).joinedload(User.profile),
            joinedload(AppointmentRequest.service)
        ).outerjoin(
            AppointmentPayment,
            and_(
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
                AppointmentPayment.status == 'COMPLETED'
            )
        ).filter(
            AppointmentRequest.doctor_id == doctor_id,
            AppointmentRequest.status == 'ACCEPTED',
            AppointmentRequest.deleted_at.is_(None),
            AppointmentPayment.id.is_(None)  # Exclude requests with COMPLETED payments
        )
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search.lower()}%"
            # Filter appointments by patient name
            appointments_query = appointments_query.join(User, Appointment.patient_id == User.id).filter(
                func.lower(User.name).like(search_term)
            )
            # Filter requests by patient name
            requests_query = requests_query.join(User, AppointmentRequest.patient_id == User.id).filter(
                func.lower(User.name).like(search_term)
            )
        
        # Fetch all appointments and accepted requests
        all_appointments = appointments_query.all()
        all_accepted_requests = requests_query.all()
        
        # Build appointment -> request_id map and fetch payments for payment_status
        # Map: (doctor_id, patient_id, service_id, appointment_date, start_time) -> request_id
        appointment_to_request_map = {}
        # Get all requests for this doctor that have COMPLETED payment (these created appointments)
        completed_payments_query = self.db.query(AppointmentRequest.id, AppointmentRequest.doctor_id, AppointmentRequest.patient_id, AppointmentRequest.service_id, AppointmentRequest.preferred_date, AppointmentRequest.preferred_time).join(
            AppointmentPayment,
            and_(
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
                AppointmentPayment.status == 'COMPLETED'
            )
        ).filter(
            AppointmentRequest.doctor_id == doctor_id,
            AppointmentRequest.deleted_at.is_(None)
        )
        for row in completed_payments_query.all():
            key = (str(doctor_id), str(row.patient_id), str(row.service_id), row.preferred_date, row.preferred_time)
            appointment_to_request_map[key] = row.id
        request_ids_for_payments = set(appointment_to_request_map.values()) | {r.id for r in all_accepted_requests}
        all_payments = {}
        if request_ids_for_payments:
            payments = self.db.query(AppointmentPayment).filter(
                AppointmentPayment.appointment_request_id.in_(request_ids_for_payments)
            ).all()
            for p in payments:
                all_payments[p.appointment_request_id] = p
        
        # Convert accepted requests to appointment-like objects for processing
        class AppointmentLike:
            """Wrapper to make AppointmentRequest look like Appointment for filtering"""
            def __init__(self, request: AppointmentRequest):
                self.id = request.id
                self.patient_id = request.patient_id
                self.patient = request.patient
                self.service_id = request.service_id
                self.service = request.service
                self.appointment_date = request.preferred_date
                self.start_time = request.preferred_time
                # Calculate end_time from start_time + duration
                if request.preferred_time and request.duration_minutes:
                    from datetime import timedelta
                    start_datetime = datetime.combine(request.preferred_date, request.preferred_time)
                    end_datetime = start_datetime + timedelta(minutes=request.duration_minutes)
                    self.end_time = end_datetime.time()
                else:
                    self.end_time = None
                self.status = 'ACCEPTED'  # Accepted requests are treated as accepted status
                self.price_amount = request.price_amount
                self.currency = request.currency
                self.duration_minutes = request.duration_minutes
                self.consultation_mode = request.consultation_mode
                self.is_request = True  # Flag to identify this is from a request
                self.request_id = request.id
                self.waiver_percent = getattr(request, "waiver_percent", None)
        
        # Convert accepted requests to appointment-like objects
        accepted_requests_as_appointments = [AppointmentLike(req) for req in all_accepted_requests]
        
        # Combine appointments and accepted requests
        all_items = list(all_appointments) + accepted_requests_as_appointments
        
        # Filter by appointment type
        if appointment_type == 'today':
            # Today: appointments and accepted requests where appointment_date == today
            filtered_items = [a for a in all_items if a.appointment_date and a.appointment_date == today]
            # Sort by start_time (earliest first)
            filtered_items.sort(key=lambda a: a.start_time or time(23, 59, 59))
        elif appointment_type == 'upcoming':
            # Upcoming: appointments and accepted requests where appointment_date > today (only future dates, NOT today)
            filtered_items = [a for a in all_items if a.appointment_date and a.appointment_date > today]
            # Sort by appointment_date (soonest first), then start_time
            filtered_items.sort(key=lambda a: (a.appointment_date or date(2099, 12, 31), a.start_time or time(23, 59, 59)))
        else:
            # If no type specified, include both today and upcoming (exclude completed)
            filtered_items = [a for a in all_items if a.appointment_date and a.appointment_date >= today]
            # Sort by appointment_date (soonest first), then start_time
            filtered_items.sort(key=lambda a: (a.appointment_date or date(2099, 12, 31), a.start_time or time(23, 59, 59)))
        
        logger.info(f"Staff view - Doctor {doctor_id}: Found {len(filtered_items)} items (appointments: {len(all_appointments)}, accepted requests: {len(all_accepted_requests)}, type: {appointment_type}, date: {today})")

        def appointment_to_item(a) -> dict:
            patient = a.patient
            service = a.service
            
            # Get patient profile image
            profile_image_path = None
            try:
                profile_image_path = patient.avatar or (patient.profile.avatar if hasattr(patient, 'profile') and patient.profile else None)
            except Exception:
                profile_image_path = None
            
            # Generate full URL for profile image
            profile_image = self._get_avatar_url(profile_image_path) if profile_image_path else None

            # Get patient gender and age from profile
            gender = None
            age = None
            try:
                if patient and hasattr(patient, 'profile') and patient.profile:
                    profile = patient.profile
                    gender = profile.gender
                    if profile.date_of_birth:
                        dob = profile.date_of_birth
                        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except Exception:
                pass
            
            # Check if this is from an appointment request
            is_request = getattr(a, 'is_request', False)
            request_id = getattr(a, 'request_id', None)
            
            # Payment status: for appointments use map to find request/payment; for requests use request_id
            payment_status = "paid"
            try:
                if is_request and request_id:
                    payment = all_payments.get(request_id)
                    if payment:
                        payment_status = "paid" if payment.status == 'COMPLETED' else payment.status.lower()
                    else:
                        payment_status = "pending"
                else:
                    # Real appointment: find request that created it
                    appointment_key = (
                        str(doctor_id),
                        str(a.patient_id),
                        str(a.service_id),
                        a.appointment_date,
                        a.start_time
                    )
                    rid = appointment_to_request_map.get(appointment_key)
                    if rid:
                        payment = all_payments.get(rid)
                        if payment:
                            payment_status = "paid" if payment.status == 'COMPLETED' else payment.status.lower()
                    # else: already default "paid" for existing appointment
            except Exception:
                payment_status = "paid" if not is_request else "pending"

            return {
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "patient_name": patient.name if patient else None,
                "patient_profile_image": profile_image,
                "patient_gender": gender,
                "patient_age": age,
                "service_id": str(a.service_id),
                "service_name": service.name if service else None,
                "consultation_mode": a.consultation_mode,
                "appointment_date": a.appointment_date.isoformat() if a.appointment_date else None,
                "start_time": str(a.start_time) if a.start_time else None,
                "end_time": str(a.end_time) if a.end_time else None,
                "status": a.status,
                "price_amount": float(a.price_amount) if a.price_amount is not None else None,
                "currency": a.currency,
                "duration_minutes": a.duration_minutes,
                "is_appointment_request": is_request,  # Indicate if this is from a request
                "appointment_request_id": str(request_id) if request_id else None,
                "payment_status": payment_status
            }

        # Convert to items
        appointments_list = [appointment_to_item(a) for a in filtered_items]
        
        # Get total count
        total = len(appointments_list)
        
        # Apply pagination
        offset = (page - 1) * per_page
        paginated_items = appointments_list[offset:offset + per_page]
        
        # Calculate pagination metadata
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return {
            "appointments": paginated_items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    def process_payment_and_create_appointment(
        self,
        current_user: CurrentUser,
        appointment_request_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> dict:
        """
        Process payment for an accepted appointment request and create appointment
        
        This is a temporary implementation that marks payment as completed without
        actual payment gateway integration. For production, replace with real payment processing.
        
        Rules:
        - Request must belong to authenticated patient
        - Request must be ACCEPTED status
        - Request must have valid price
        - No existing payment or appointment for this request
        - Creates AppointmentPayment with COMPLETED status
        - Creates Appointment with CONFIRMED status
        
        Args:
            current_user: Current patient user
            appointment_request_id: Appointment request ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Dictionary with appointment and payment details
            
        Raises:
            NotFoundException: If request not found
            ForbiddenException: If not authorized
            BadRequestException: If validation fails
        """
        from datetime import datetime as dt_class, timedelta, timezone
        
        # Validate patient role
        if current_user.role != UserRole.PATIENT.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only patients can process payments"]}
            )
        
        logger.info(f"Processing payment for appointment request {appointment_request_id} by patient {current_user.id}")
        
        # Get appointment request
        appointment_request = self.db.query(AppointmentRequest).filter(
            AppointmentRequest.id == appointment_request_id,
            AppointmentRequest.deleted_at.is_(None)
        ).first()
        
        if not appointment_request:
            logger.warning(f"Appointment request {appointment_request_id} not found")
            raise NotFoundException(
                message="Appointment request not found",
                errors={"appointment_request_id": ["Request does not exist"]}
            )
        
        # Validate ownership
        if str(appointment_request.patient_id) != str(current_user.id):
            logger.warning(f"Patient {current_user.id} attempted to pay for request {appointment_request_id} belonging to patient {appointment_request.patient_id}")
            raise ForbiddenException(
                message="Access denied",
                errors={"appointment_request_id": ["You can only pay for your own appointment requests"]}
            )
        
        # Validate status - must be ACCEPTED
        if appointment_request.status != 'ACCEPTED':
            logger.warning(f"Appointment request {appointment_request_id} has status {appointment_request.status}, expected ACCEPTED")
            raise BadRequestException(
                message="Payment cannot be processed",
                errors={"status": [f"Request must be ACCEPTED to process payment. Current status: {appointment_request.status}"]}
            )
        
        # Validate price exists
        if not appointment_request.price_amount or appointment_request.price_amount <= 0:
            logger.error(f"Appointment request {appointment_request_id} has invalid price: {appointment_request.price_amount}")
            raise BadRequestException(
                message="Payment cannot be processed",
                errors={"price": ["Appointment request does not have a valid price"]}
            )
        
        # Check if payment already exists
        existing_payment = self.db.query(AppointmentPayment).filter(
            AppointmentPayment.appointment_request_id == appointment_request_id
        ).first()
        
        if existing_payment:
            logger.warning(f"Payment already exists for request {appointment_request_id}: {existing_payment.id} with status {existing_payment.status}")
            
            # If payment is already completed, check if appointment exists
            if existing_payment.status == 'COMPLETED':
                existing_appointment = self.db.query(Appointment).filter(
                    Appointment.doctor_id == appointment_request.doctor_id,
                    Appointment.patient_id == appointment_request.patient_id,
                    Appointment.service_id == appointment_request.service_id,
                    Appointment.appointment_date == appointment_request.preferred_date,
                    Appointment.start_time == appointment_request.preferred_time,
                    Appointment.deleted_at.is_(None)
                ).first()
                
                if existing_appointment:
                    logger.info(f"Appointment already exists for request {appointment_request_id}: {existing_appointment.id}")
                    raise BadRequestException(
                        message="Payment already processed",
                        errors={"payment": ["This appointment request has already been paid and appointment created"]}
                    )
                else:
                    # Payment marked as completed but appointment missing - create it
                    logger.info(f"Payment completed but appointment missing for request {appointment_request_id}, creating appointment")
            else:
                raise BadRequestException(
                    message="Payment already exists",
                    errors={"payment": [f"Payment already exists with status: {existing_payment.status}"]}
                )
        
        # Check if appointment already exists (duplicate check)
        existing_appointment = self.db.query(Appointment).filter(
            Appointment.doctor_id == appointment_request.doctor_id,
            Appointment.patient_id == appointment_request.patient_id,
            Appointment.service_id == appointment_request.service_id,
            Appointment.appointment_date == appointment_request.preferred_date,
            Appointment.start_time == appointment_request.preferred_time,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if existing_appointment:
            logger.warning(f"Appointment already exists for request {appointment_request_id}: {existing_appointment.id}")
            raise BadRequestException(
                message="Appointment already exists",
                errors={"appointment": ["An appointment already exists for this request"]}
            )
        
        try:
            # Calculate end time
            start_datetime = dt_class.combine(appointment_request.preferred_date, appointment_request.preferred_time)
            end_datetime = start_datetime + timedelta(minutes=appointment_request.duration_minutes)
            end_time = end_datetime.time()
            
            # Create or update payment record
            if existing_payment:
                # Update existing payment to COMPLETED
                existing_payment.status = 'COMPLETED'
                existing_payment.updated_at = dt_class.now(timezone.utc)
                payment = existing_payment
                logger.info(f"Updated existing payment {payment.id} to COMPLETED status")
            else:
                # Create new payment record with COMPLETED status
                payment = AppointmentPayment(
                    appointment_request_id=appointment_request_id,
                    amount=appointment_request.price_amount,
                    currency=appointment_request.currency,
                    status='COMPLETED'
                )
                self.db.add(payment)
                logger.info(f"Created new payment record {payment.id} with COMPLETED status")
            
            # Lock commission at completion (only upcoming: rate changes do not affect past payments)
            set_payment_commission(self.db, payment)
            
            # Commit payment first
            self.db.commit()
            self.db.refresh(payment)
            
            # Create confirmed appointment
            appointment = Appointment(
                doctor_id=appointment_request.doctor_id,
                patient_id=appointment_request.patient_id,
                service_id=appointment_request.service_id,
                clinic_id=appointment_request.clinic_id,
                doctor_service_availability_id=appointment_request.doctor_service_availability_id,
                appointment_date=appointment_request.preferred_date,
                start_time=appointment_request.preferred_time,
                end_time=end_time,
                status='CONFIRMED',  # Confirmed after payment
                consultation_mode=appointment_request.consultation_mode,
                duration_minutes=appointment_request.duration_minutes,
                price_amount=payment.amount,
                currency=appointment_request.currency,
                pricing_source=appointment_request.pricing_source
            )
            
            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)
            
            logger.info(
                f"Payment processed successfully: payment_id={payment.id}, "
                f"appointment_request_id={appointment_request_id}, "
                f"appointment_id={appointment.id}, "
                f"amount={appointment_request.price_amount} {appointment_request.currency}"
            )
            
            # Audit log: Payment completed (NO PHI)
            self.audit_service.create_audit_log(
                actor_user_id=current_user.id,
                action="PAYMENT_COMPLETED",
                entity_type="appointment_payment",
                entity_id=payment.id,
                audit_metadata={
                    "appointment_request_id": str(appointment_request_id),
                    "appointment_id": str(appointment.id),
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "payment_method": "manual"  # Mark as manual payment (temporary)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Audit log: Appointment confirmed (NO PHI)
            self.audit_service.create_audit_log(
                actor_user_id=current_user.id,
                action="APPOINTMENT_CONFIRMED",
                entity_type="appointment",
                entity_id=appointment.id,
                audit_metadata={
                    "appointment_id": str(appointment.id),
                    "appointment_request_id": str(appointment_request_id),
                    "consultation_mode": appointment_request.consultation_mode,
                    "price_amount": float(appointment_request.price_amount),
                    "currency": appointment_request.currency,
                    "appointment_date": appointment_request.preferred_date.isoformat(),
                    "start_time": appointment_request.preferred_time.isoformat()
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "appointment": appointment,
                "payment": payment,
                "appointment_request_id": str(appointment_request_id)
            }
            
        except Exception as e:
            self.db.rollback()
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(
                f"Error processing payment for request {appointment_request_id}: {error_type}: {error_msg}",
                exc_info=True
            )
            # Re-raise with full error details
            raise BadRequestException(
                message=f"Error processing payment: {error_type}: {error_msg}",
                errors={"general": [f"{error_type}: {error_msg}"]}
            )
    
    def start_visit(
        self,
        current_user: CurrentUser,
        appointment_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Appointment:
        """
        Start a visit/consultation for a confirmed appointment
        
        Rules:
        - Only assigned doctor can start visit
        - Appointment must be CONFIRMED (payment completed)
        - Updates status to IN_PROGRESS
        
        Args:
            current_user: Current doctor user
            appointment_id: Appointment ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated Appointment object
            
        Raises:
            NotFoundException: If appointment not found
            ForbiddenException: If not authorized
            BadRequestException: If validation fails
        """
        # Validate doctor role
        if current_user.role != UserRole.DOCTOR.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors can start visits"]}
            )
        
        # Get appointment
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if not appointment:
            raise NotFoundException(
                message="Appointment not found",
                errors={"appointment_id": ["Appointment does not exist"]}
            )
        
        # Validate ownership
        if str(appointment.doctor_id) != str(current_user.id):
            raise ForbiddenException(
                message="Access denied",
                errors={"appointment_id": ["You can only start visits for your own appointments"]}
            )
        
        # Validate status - must be CONFIRMED (payment completed)
        if appointment.status != 'CONFIRMED':
            raise BadRequestException(
                message="Visit cannot be started",
                errors={"status": [f"Appointment must be CONFIRMED to start visit. Current status: {appointment.status}"]}
            )
        
        # Update status to IN_PROGRESS
        appointment.status = 'IN_PROGRESS'
        
        self.db.commit()
        self.db.refresh(appointment)
        
        # Audit log: Visit started (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="VISIT_STARTED",
            entity_type="appointment",
            entity_id=appointment.id,
            audit_metadata={
                "appointment_id": str(appointment_id),
                "patient_id": str(appointment.patient_id),
                "consultation_mode": appointment.consultation_mode
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Visit started for appointment {appointment_id} by doctor {current_user.id}")
        
        return appointment
    
    def complete_visit(
        self,
        current_user: CurrentUser,
        appointment_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Appointment:
        """
        Complete a visit/consultation
        
        Rules:
        - Only assigned doctor can complete visit
        - Appointment must be IN_PROGRESS
        - Updates status to COMPLETED
        
        Args:
            current_user: Current doctor user
            appointment_id: Appointment ID
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated Appointment object
            
        Raises:
            NotFoundException: If appointment not found
            ForbiddenException: If not authorized
            BadRequestException: If validation fails
        """
        # Validate doctor role
        if current_user.role != UserRole.DOCTOR.value:
            raise ForbiddenException(
                message="Access denied",
                errors={"role": ["Only doctors can complete visits"]}
            )
        
        # Get appointment
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if not appointment:
            raise NotFoundException(
                message="Appointment not found",
                errors={"appointment_id": ["Appointment does not exist"]}
            )
        
        # Validate ownership
        if str(appointment.doctor_id) != str(current_user.id):
            raise ForbiddenException(
                message="Access denied",
                errors={"appointment_id": ["You can only complete visits for your own appointments"]}
            )
        
        # Validate status - must be IN_PROGRESS
        if appointment.status != 'IN_PROGRESS':
            raise BadRequestException(
                message="Visit cannot be completed",
                errors={"status": [f"Appointment must be IN_PROGRESS to complete visit. Current status: {appointment.status}"]}
            )
        
        # Update status to COMPLETED
        appointment.status = 'COMPLETED'
        
        self.db.commit()
        self.db.refresh(appointment)
        
        # Audit log: Visit completed (NO PHI)
        self.audit_service.create_audit_log(
            actor_user_id=current_user.id,
            action="VISIT_COMPLETED",
            entity_type="appointment",
            entity_id=appointment.id,
            audit_metadata={
                "appointment_id": str(appointment_id),
                "patient_id": str(appointment.patient_id),
                "consultation_mode": appointment.consultation_mode
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Visit completed for appointment {appointment_id} by doctor {current_user.id}")
        
        return appointment