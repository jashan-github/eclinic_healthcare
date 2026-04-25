"""
Doctor Search Service
Business logic for patient doctor search functionality
"""

from typing import Optional, List, Dict, Any, Set, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import time as time_type, date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, distinct, select, exists
from loguru import logger

from app.models.user import User
from app.models.profile import UserProfile, user_medical_services
from app.models.medical_service import MedicalService
from app.models.availability import DoctorAvailability
from app.models.service import Service
from app.models.doctor_service import DoctorService
from app.models.doctor_service_pricing import DoctorServicePricing
from app.models.doctor_service_availability_pricing import DoctorServiceAvailabilityPricing
from app.models.doctor_service_availability import DoctorServiceAvailability
from app.core.security import UserRole, ConsultationMode
from app.core.config import settings


class DoctorSearchService:
    """Service for doctor search operations"""

    # Hardcoded currency for patient doctor search response
    CURRENCY = "XCG"

    # Day name to day_of_week mapping (0=Monday, 6=Sunday)
    DAY_NAME_TO_INT = {
        "mon": 0, "monday": 0,
        "tue": 1, "tuesday": 1,
        "wed": 2, "wednesday": 2,
        "thu": 3, "thursday": 3,
        "fri": 4, "friday": 4,
        "sat": 5, "saturday": 5,
        "sun": 6, "sunday": 6
    }
    
    # Day of week integer to day name mapping
    INT_TO_DAY_NAME = {
        0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu",
        4: "Fri", 5: "Sat", 6: "Sun"
    }
    
    def __init__(self, db: Session):
        """
        Initialize doctor search service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def search_doctors(
        self,
        specialty_id: Optional[UUID] = None,
        availability_day: Optional[str] = None,
        availability_time: Optional[str] = None,
        availability_date: Optional[date_type] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for doctors with optional filters
        
        Args:
            specialty_id: Optional medical service/specialty ID to filter by
            availability_day: Optional day name (Mon, Tue, etc.) to filter by
            availability_time: Optional time (HH:MM) to filter by
            availability_date: Optional date for filtering services. If provided, only services available on this day are returned; if omitted, services are not filtered by day.
            page: Page number (default: 1)
            limit: Items per page (default: 20, max: 100)
            
        Returns:
            Dictionary with doctors list and pagination info
        """
        # Base query: Get all active doctors with complete profile only
        query = self.db.query(User).filter(
            User.role == UserRole.DOCTOR.value,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
        # Skip doctors whose profile is not complete:
        # first_name, gender, date_of_birth, education, years_of_experience, and at least one specialization
        query = query.join(UserProfile, UserProfile.user_id == User.id).filter(
            UserProfile.first_name.isnot(None),
            UserProfile.first_name != "",
            UserProfile.gender.isnot(None),
            UserProfile.gender != "",
            UserProfile.date_of_birth.isnot(None),
            UserProfile.education.isnot(None),
            UserProfile.education != "",
            UserProfile.years_of_experience.isnot(None),
        )
        # Must have at least one active medical service (specialization)
        has_specialization = exists(
            select(1)
            .select_from(user_medical_services)
            .join(MedicalService, MedicalService.id == user_medical_services.c.medical_service_id)
            .where(
                user_medical_services.c.user_id == User.id,
                MedicalService.status == True,
            )
        )
        query = query.filter(has_specialization)
        
        # Filter by specialty_id if provided
        if specialty_id:
            query = query.join(
                user_medical_services,
                user_medical_services.c.user_id == User.id
            ).join(
                MedicalService,
                and_(
                    MedicalService.id == user_medical_services.c.medical_service_id,
                    MedicalService.id == specialty_id,
                    MedicalService.status == True
                )
            ).distinct()
        
        # Filter by availability_day if provided
        availability_day_int = None
        if availability_day:
            availability_day_int = self._parse_day_name(availability_day)
            if availability_day_int is not None:
                # Join with doctor_availability and filter by day
                query = query.join(
                    DoctorAvailability,
                    and_(
                        DoctorAvailability.doctor_id == User.id,
                        DoctorAvailability.day_of_week == availability_day_int,
                        DoctorAvailability.is_active == True,
                        DoctorAvailability.deleted_at.is_(None)
                    )
                ).distinct()
        
        # Filter by availability_time if provided
        availability_time_obj = None
        if availability_time:
            availability_time_obj = self._parse_time(availability_time)
            if availability_time_obj is not None:
                # If we already joined DoctorAvailability, add time filter
                # Otherwise, join and filter
                if availability_day_int is None:
                    query = query.join(
                        DoctorAvailability,
                        and_(
                            DoctorAvailability.doctor_id == User.id,
                            DoctorAvailability.is_active == True,
                            DoctorAvailability.deleted_at.is_(None)
                        )
                    ).distinct()
                
                # Filter by time range: time should be between start_time and end_time
                query = query.filter(
                    and_(
                        DoctorAvailability.start_time <= availability_time_obj,
                        DoctorAvailability.end_time > availability_time_obj
                    )
                )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        doctors = query.offset(offset).limit(limit).all()
        
        # Build response data with efficient queries (no N+1)
        doctor_ids = [doctor.id for doctor in doctors]
        
        # Load profiles in bulk
        profiles = {
            profile.user_id: profile
            for profile in self.db.query(UserProfile).filter(
                UserProfile.user_id.in_(doctor_ids)
            ).all()
        }
        
        # Load medical services in bulk
        doctor_medical_services = {}
        if doctor_ids:
            medical_service_links = self.db.query(
                user_medical_services.c.user_id,
                MedicalService.id,
                MedicalService.name
            ).join(
                MedicalService,
                MedicalService.id == user_medical_services.c.medical_service_id
            ).filter(
                user_medical_services.c.user_id.in_(doctor_ids),
                MedicalService.status == True
            ).all()
            
            for user_id, service_id, service_name in medical_service_links:
                if user_id not in doctor_medical_services:
                    doctor_medical_services[user_id] = []
                doctor_medical_services[user_id].append({"id": str(service_id), "name": service_name})
        
        # Load availability in bulk
        doctor_availabilities = {}
        if doctor_ids:
            availabilities = self.db.query(DoctorAvailability).filter(
                DoctorAvailability.doctor_id.in_(doctor_ids),
                DoctorAvailability.is_active == True,
                DoctorAvailability.deleted_at.is_(None)
            ).all()
            
            for avail in availabilities:
                if avail.doctor_id not in doctor_availabilities:
                    doctor_availabilities[avail.doctor_id] = []
                doctor_availabilities[avail.doctor_id].append(avail.day_of_week)
        
        # Optional day filter: only when date is provided (0=Monday, 6=Sunday)
        target_day_of_week = None
        if availability_date is not None:
            target_day_of_week = availability_date.weekday()
        
        # Load pricing in bulk (for lowest consultation fee)
        doctor_prices = self._get_doctor_prices(doctor_ids)
        
        # Load doctor services with prices (filter by day only if availability_date was provided)
        doctor_services_data = self._get_doctor_services_with_prices(doctor_ids, day_of_week=target_day_of_week)
        
        # Build response
        doctors_data = []
        for doctor in doctors:
            profile = profiles.get(doctor.id)
            
            # Get primary specialty (first active medical service)
            specialty = None
            if doctor.id in doctor_medical_services and doctor_medical_services[doctor.id]:
                specialty = doctor_medical_services[doctor.id][0]["name"]
            
            # Get qualifications
            qualifications = None
            if profile and profile.education:
                qualifications = profile.education
            
            # Get years of experience
            years_of_experience = None
            if profile and profile.years_of_experience is not None:
                years_of_experience = profile.years_of_experience
            
            # Get lowest consultation fee (currency hardcoded to XCG)
            price_info = doctor_prices.get(doctor.id, {})
            lowest_fee = price_info.get("price")
            
            # Get available days (unique, sorted, max 5)
            available_days = []
            if doctor.id in doctor_availabilities:
                unique_days = sorted(set(doctor_availabilities[doctor.id]))
                available_days = [
                    self.INT_TO_DAY_NAME[day]
                    for day in unique_days[:5]
                    if day in self.INT_TO_DAY_NAME
                ]
            
            # Get profile image and construct full URL
            avatar_path = doctor.avatar or (profile.avatar if profile else None)
            profile_image_url = None
            if avatar_path:
                # Remove leading slash if present and ensure BASE_URL doesn't end with slash
                base_url = settings.BASE_URL.rstrip('/')
                avatar_path_clean = avatar_path.lstrip('/')
                profile_image_url = f"{base_url}/{avatar_path_clean}"
            
            # Get doctor's services with prices
            services = doctor_services_data.get(doctor.id, [])
            
            doctors_data.append({
                "id": doctor.id,
                "name": doctor.name,
                "profile_image": profile_image_url,
                "specialty": specialty,
                "qualifications": qualifications,
                "rating": None,  # Rating not available in current schema
                "years_of_experience": years_of_experience,
                "lowest_consultation_fee": float(lowest_fee) if lowest_fee else None,
                "currency": self.CURRENCY,
                "available_days": available_days,
                "services": services
            })
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        return {
            "doctors": doctors_data,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total": total,
                "total_pages": total_pages
            }
        }
    
    def _get_doctor_prices(self, doctor_ids: List[UUID]) -> Dict[UUID, Dict[str, Any]]:
        """
        Get lowest IN_CLINIC consultation fee for each doctor across all sources.
        Collects all candidate prices from availability pricing, doctor_service_pricing,
        and service base price; then takes the minimum per doctor.
        
        Returns:
            Dictionary mapping doctor_id to {price, currency}
        """
        if not doctor_ids:
            return {}
        
        # Collect all (doctor_id, price, currency) from all sources
        candidates: List[Tuple[UUID, Any, Optional[str]]] = []
        
        # Source 1: Availability-specific pricing (IN_CLINIC)
        availability_prices = self.db.query(
            DoctorAvailability.doctor_id,
            DoctorServiceAvailabilityPricing.price_amount,
            DoctorServiceAvailabilityPricing.currency
        ).select_from(
            DoctorServiceAvailabilityPricing
        ).join(
            DoctorServiceAvailability,
            DoctorServiceAvailability.id == DoctorServiceAvailabilityPricing.doctor_service_availability_id
        ).join(
            DoctorAvailability,
            DoctorAvailability.id == DoctorServiceAvailability.availability_id
        ).filter(
            DoctorAvailability.doctor_id.in_(doctor_ids),
            DoctorAvailability.is_active == True,
            DoctorAvailability.deleted_at.is_(None),
            DoctorServiceAvailabilityPricing.consultation_mode == ConsultationMode.IN_CLINIC.value,
            DoctorServiceAvailabilityPricing.price_amount.isnot(None)
        ).all()
        
        for doctor_id, price_amount, currency in availability_prices:
            if price_amount is not None:
                candidates.append((doctor_id, price_amount, currency))
        
        # Source 2: Doctor service pricing
        doctor_service_prices = self.db.query(
            DoctorServicePricing.doctor_id,
            DoctorServicePricing.price_amount,
            DoctorServicePricing.currency
        ).filter(
            DoctorServicePricing.doctor_id.in_(doctor_ids),
            DoctorServicePricing.price_amount.isnot(None)
        ).all()
        
        for doctor_id, price_amount, currency in doctor_service_prices:
            if price_amount is not None:
                candidates.append((doctor_id, price_amount, currency))
        
        # Source 3: Service base price via doctor_services
        doctor_services = self.db.query(
            DoctorService.doctor_id,
            Service.price,
            Service.currency
        ).join(
            Service,
            Service.id == DoctorService.service_id
        ).filter(
            DoctorService.doctor_id.in_(doctor_ids),
            DoctorService.is_active == True,
            Service.price.isnot(None),
            Service.deleted_at.is_(None)
        ).all()
        
        for doctor_id, base_price, currency in doctor_services:
            if base_price is not None:
                candidates.append((doctor_id, base_price, currency))
        
        # For each doctor, take the minimum price (and its currency)
        result = {}
        for doctor_id, price, currency in candidates:
            price_val = float(price) if price is not None else None
            if price_val is None:
                continue
            if doctor_id not in result or result[doctor_id].get("price") is None or price_val < result[doctor_id]["price"]:
                result[doctor_id] = {"price": price_val, "currency": self.CURRENCY}
        
        return result
    
    def _get_doctor_services_with_prices(
        self,
        doctor_ids: List[UUID],
        day_of_week: Optional[int] = None
    ) -> Dict[UUID, List[Dict[str, Any]]]:
        """
        Get services for each doctor with their prices.
        If day_of_week is provided (0=Monday, 6=Sunday), only returns services
        that are available on that day (via DoctorServiceAvailability + DoctorAvailability).
        
        Args:
            doctor_ids: List of doctor IDs
            day_of_week: Optional. Only include services available on this day. 0=Monday, 6=Sunday.
            
        Returns:
            Dictionary mapping doctor_id to list of services with prices
        """
        if not doctor_ids:
            return {}
        
        # When filtering by day: get (doctor_id, service_id) pairs available on that day
        available_doctor_services: Set[Tuple[UUID, UUID]] = set()
        if day_of_week is not None:
            rows = self.db.query(
                DoctorAvailability.doctor_id,
                DoctorServiceAvailability.service_id
            ).select_from(DoctorServiceAvailability).join(
                DoctorAvailability,
                DoctorAvailability.id == DoctorServiceAvailability.availability_id
            ).filter(
                DoctorAvailability.doctor_id.in_(doctor_ids),
                DoctorAvailability.day_of_week == day_of_week,
                DoctorAvailability.is_active == True,
                DoctorAvailability.deleted_at.is_(None)
            ).distinct().all()
            available_doctor_services = {(r.doctor_id, r.service_id) for r in rows}
        
        result = {}
        
        # Get doctor services: default (day_of_week IS NULL) or matching day
        doctor_service_q = self.db.query(
            DoctorService.doctor_id,
            DoctorService.service_id,
            Service.name.label('service_name'),
            Service.nickname.label('service_nickname'),
            Service.service_mode,
            Service.appointment_type,
            Service.price.label('base_price'),
            Service.currency.label('base_currency'),
            DoctorService.slot_duration_minutes
        ).join(
            Service,
            Service.id == DoctorService.service_id
        ).filter(
            DoctorService.doctor_id.in_(doctor_ids),
            DoctorService.is_active == True,
            Service.deleted_at.is_(None)
        )
        # DoctorService uses 0=Sunday, 1=Monday, ..., 6=Saturday; we use 0=Monday (Python weekday)
        if day_of_week is not None:
            doctor_service_day = (day_of_week + 1) % 7  # Mon(0)->1, Tue(1)->2, ..., Sun(6)->0
            doctor_service_q = doctor_service_q.filter(
                or_(
                    DoctorService.day_of_week.is_(None),
                    DoctorService.day_of_week == doctor_service_day
                )
            )
        else:
            doctor_service_q = doctor_service_q.filter(DoctorService.day_of_week.is_(None))
        
        doctor_service_records = doctor_service_q.all()
        
        # Get doctor-specific pricing from doctor_service_pricing
        doctor_pricing = {}
        pricing_records = self.db.query(
            DoctorServicePricing.doctor_id,
            DoctorServicePricing.service_id,
            DoctorServicePricing.price_amount,
            DoctorServicePricing.currency
        ).filter(
            DoctorServicePricing.doctor_id.in_(doctor_ids)
        ).all()
        
        for doctor_id, service_id, price_amount, currency in pricing_records:
            if doctor_id not in doctor_pricing:
                doctor_pricing[doctor_id] = {}
            doctor_pricing[doctor_id][service_id] = {
                "price": float(price_amount) if price_amount else None,
                "currency": self.CURRENCY
            }
        
        # Build result (when day_of_week set, only include services in available_doctor_services)
        for record in doctor_service_records:
            doctor_id = record.doctor_id
            service_id = record.service_id
            if day_of_week is not None and (doctor_id, service_id) not in available_doctor_services:
                continue
            
            # Check for doctor-specific pricing first, then fall back to base price
            price_info = None
            if doctor_id in doctor_pricing and service_id in doctor_pricing[doctor_id]:
                price_info = doctor_pricing[doctor_id][service_id]
            elif record.base_price is not None:
                price_info = {
                    "price": float(record.base_price),
                    "currency": self.CURRENCY
                }
            
            service_data = {
                "id": str(service_id),
                "name": record.service_name,
                "nickname": record.service_nickname,
                "service_mode": record.service_mode,
                "appointment_type": record.appointment_type,
                "slot_duration_minutes": record.slot_duration_minutes,
                "price": price_info.get("price") if price_info else None,
                "currency": self.CURRENCY
            }
            
            if doctor_id not in result:
                result[doctor_id] = []
            result[doctor_id].append(service_data)
        
        return result
    
    def _parse_day_name(self, day_name: str) -> Optional[int]:
        """
        Parse day name to day_of_week integer
        
        Args:
            day_name: Day name (Mon, Tue, etc.)
            
        Returns:
            Day of week integer (0=Monday, 6=Sunday) or None if invalid
        """
        day_lower = day_name.lower().strip()
        return self.DAY_NAME_TO_INT.get(day_lower)
    
    def _parse_time(self, time_str: str) -> Optional[time_type]:
        """
        Parse time string (HH:MM) to time object
        
        Args:
            time_str: Time string in HH:MM format
            
        Returns:
            time object or None if invalid
        """
        try:
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                return None
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                return None
            
            return time_type(hour, minute)
        except (ValueError, IndexError):
            logger.warning(f"Invalid time format: {time_str}")
            return None
