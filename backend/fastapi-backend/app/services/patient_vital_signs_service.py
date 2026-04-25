"""
Patient Vital Signs Service
Business logic for patient vital signs management
"""

from typing import Optional, List, Union, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, distinct

from app.models.patient_vital_signs import PatientVitalSigns
from app.models.vital_name import VitalName
from app.services.vital_frequency_service import VitalFrequencyService
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException
from loguru import logger


class PatientVitalSignsService:
    """Service for managing patient vital signs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.frequency_service = VitalFrequencyService(db)
    
    def _check_max_entries_per_day(
        self,
        patient_id: UUID,
        clinic_id: UUID,
        vital_name_id: UUID,
        record_date: datetime,
        max_entries: int
    ) -> None:
        """
        Check if maximum entries per day limit is reached for a specific vital
        
        Args:
            patient_id: Patient user ID
            clinic_id: Clinic ID
            vital_name_id: Vital name ID
            record_date: Date of the record
            max_entries: Maximum allowed entries per day for this vital
            
        Raises:
            ValidationException: If maximum entries limit is reached
        """
        # Get start and end of the day in UTC
        day_start = record_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = record_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Count existing records for this patient, clinic, vital_name, and date
        count = self.db.query(PatientVitalSigns).filter(
            and_(
                PatientVitalSigns.patient_id == patient_id,
                PatientVitalSigns.clinic_id == clinic_id,
                PatientVitalSigns.vital_name_id == vital_name_id,
                PatientVitalSigns.record_date >= day_start,
                PatientVitalSigns.record_date <= day_end,
                PatientVitalSigns.deleted_at.is_(None)
            )
        ).count()
        
        if count >= max_entries:
            vital_name = self.db.query(VitalName).filter(VitalName.id == vital_name_id).first()
            vital_display_name = vital_name.name if vital_name else "this vital"
            
            raise ValidationException(
                message=f"Maximum entries per day limit reached for {vital_display_name}",
                errors={
                    "max_entries": [
                        f"You have reached the maximum limit of {max_entries} entries per day for {vital_display_name}. "
                        f"Please wait until tomorrow or contact an administrator to increase the limit."
                    ]
                }
            )
    
    def _validate_vital_value(
        self,
        vital_name: VitalName,
        value: Union[float, int, str]
    ) -> tuple[Optional[Decimal], Optional[str]]:
        """
        Validate and convert vital value based on data_type
        
        Args:
            vital_name: VitalName object
            value: Value to validate
            
        Returns:
            Tuple of (numeric_value, text_value)
            
        Raises:
            ValidationException: If value is invalid
        """
        numeric_value = None
        text_value = None
        
        if vital_name.data_type == "number":
            try:
                numeric_value = Decimal(str(value))
            except (ValueError, TypeError):
                raise ValidationException(
                    message=f"Invalid numeric value for {vital_name.name}",
                    errors={"value": [f"Value must be a number for {vital_name.name}"]}
                )
        elif vital_name.data_type == "select":
            # Validate against options
            if vital_name.options:
                import json
                try:
                    options = json.loads(vital_name.options)
                    if isinstance(options, list) and str(value) not in options:
                        raise ValidationException(
                            message=f"Invalid option for {vital_name.name}",
                            errors={"value": [f"Value must be one of: {', '.join(options)}"]}
                        )
                except (json.JSONDecodeError, TypeError):
                    pass  # If options is invalid JSON, allow any value
            text_value = str(value)
        else:  # text or other
            text_value = str(value) if value is not None else None
        
        return numeric_value, text_value
    
    def create_vital_signs_records(
        self,
        patient_id: UUID,
        clinic_id: UUID,
        vitals: List[dict],
        doctor_id: Optional[UUID] = None,
        appointment_id: Optional[UUID] = None,
        record_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        check_max_entries: bool = True,
        share_with_doctor: Optional[bool] = None
    ) -> List[PatientVitalSigns]:
        """
        Create multiple vital signs records (one per vital)
        
        Args:
            patient_id: Patient user ID
            clinic_id: Clinic ID
            vitals: List of vital readings, each with 'vital_name_id' and 'value'
            doctor_id: Doctor user ID who recorded (NULL = patient recorded)
            appointment_id: Associated appointment ID
            record_date: Date when vital signs were recorded (defaults to now)
            notes: Additional notes
            check_max_entries: Whether to check max entries per day limit
            share_with_doctor: Patient consent to share with doctor (None = defaults to False for patients, True for doctors)
            
        Returns:
            List of created PatientVitalSigns objects
            
        Raises:
            ValidationException: If validation fails
        """
        if not vitals:
            raise ValidationException(
                message="At least one vital reading is required",
                errors={"vitals": ["At least one vital reading must be provided"]}
            )
        
        # Use current time if record_date not provided
        if record_date is None:
            record_date = datetime.now(timezone.utc)
        
        # Determine consent default: True if doctor records, False if patient records
        if share_with_doctor is None:
            share_with_doctor = doctor_id is not None  # True if doctor records, False if patient records
        
        created_records = []
        
        # Process each vital
        for vital_input in vitals:
            vital_name_id = vital_input.get('vital_name_id')
            value = vital_input.get('value')
            
            if not vital_name_id:
                raise ValidationException(
                    message="vital_name_id is required for each vital",
                    errors={"vitals": ["Each vital must have a vital_name_id"]}
                )
            
            if value is None:
                raise ValidationException(
                    message="value is required for each vital",
                    errors={"vitals": ["Each vital must have a value"]}
                )
            
            # Get vital name
            vital_name = self.db.query(VitalName).filter(
                and_(
                    VitalName.id == vital_name_id,
                    VitalName.deleted_at.is_(None)
                )
            ).first()
            
            if not vital_name:
                raise NotFoundException(f"Vital name with ID {vital_name_id} not found")
            
            if not vital_name.is_active:
                raise ValidationException(
                    message=f"Vital name '{vital_name.name}' is not active",
                    errors={"vital_name_id": [f"Vital name '{vital_name.name}' is not active"]}
                )
            
            # Check max entries per day if enabled (allow at least 20 so patient/doctor can add multiple times)
            if check_max_entries:
                max_entries = self.frequency_service.get_max_entries_per_day(
                    patient_id=patient_id,
                    clinic_id=clinic_id,
                    vital_name_id=vital_name_id
                )
                max_entries = max(max_entries, 20)
                
                self._check_max_entries_per_day(
                    patient_id=patient_id,
                    clinic_id=clinic_id,
                    vital_name_id=vital_name_id,
                    record_date=record_date,
                    max_entries=max_entries
                )
            
            # Validate and convert value
            numeric_value, text_value = self._validate_vital_value(vital_name, value)
            
            # Create record
            vital_record = PatientVitalSigns(
                patient_id=patient_id,
                clinic_id=clinic_id,
                vital_name_id=vital_name_id,
                doctor_id=doctor_id,
                appointment_id=appointment_id,
                record_date=record_date,
                numeric_value=numeric_value,
                text_value=text_value,
                unit=vital_name.unit,
                notes=notes,
                share_with_doctor=share_with_doctor
            )
            
            self.db.add(vital_record)
            created_records.append(vital_record)
        
        # Commit all records
        self.db.commit()
        
        # Refresh all records
        for record in created_records:
            self.db.refresh(record)
        
        logger.info(f"Created {len(created_records)} vital signs records for patient {patient_id} on {record_date.date()}")
        
        return created_records
    
    def get_patient_vital_signs(
        self,
        patient_id: UUID,
        vital_name_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        for_doctor: bool = False
    ) -> tuple[List[PatientVitalSigns], int]:
        """
        Get patient vital signs with optional filters
        
        Args:
            patient_id: Patient user ID
            vital_name_id: Filter by vital name ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records to return
            offset: Number of records to skip
            for_doctor: If True, only return records where share_with_doctor=True
            
        Returns:
            Tuple of (list of records, total count)
        """
        query = self.db.query(PatientVitalSigns).filter(
            and_(
                PatientVitalSigns.patient_id == patient_id,
                PatientVitalSigns.deleted_at.is_(None)
            )
        )
        
        # Filter by consent if querying for doctor
        # Use is_(True) for proper boolean comparison in SQLAlchemy
        if for_doctor:
            query = query.filter(PatientVitalSigns.share_with_doctor.is_(True))
        
        if vital_name_id:
            query = query.filter(PatientVitalSigns.vital_name_id == vital_name_id)
        
        if start_date:
            query = query.filter(PatientVitalSigns.record_date >= start_date)
        
        if end_date:
            query = query.filter(PatientVitalSigns.record_date <= end_date)
        
        # Get total count
        total = query.count()
        
        # Apply ordering and pagination
        query = query.order_by(PatientVitalSigns.record_date.desc())
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        records = query.all()
        
        return records, total
    
    def get_current_vital_signs(
        self,
        patient_id: UUID,
        for_doctor: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get current vital signs for a patient (today's date only).
        
        Returns vital sign records for the **current date (today UTC)** only.
        For each vital type, if the patient recorded it today, that record is returned;
        if they recorded it on a previous day only, null/empty is returned.
        Includes all active vitals; vitals not recorded today have null/empty values.
        If multiple entries exist for the same vital today, the latest one (by id) is used.
        
        Args:
            patient_id: Patient user ID
            for_doctor: If True, only return records where share_with_doctor=True
            
        Returns:
            List of dictionaries with vital sign data (one per active vital type)
            Format: [
                {
                    "vital_name_id": UUID,
                    "record": PatientVitalSigns or None,
                    "vital_name": VitalName
                },
                ...
            ]
        """
        from app.services.vital_name_service import VitalNameService
        
        # Get all active vital names
        vital_name_service = VitalNameService(self.db)
        all_active_vitals = vital_name_service.get_all_vital_names(is_active=True)
        
        # Build base filter conditions
        base_filters = [
            PatientVitalSigns.patient_id == patient_id,
            PatientVitalSigns.deleted_at.is_(None)
        ]
        
        # Add consent filter if querying for doctor
        # Use is_(True) for proper boolean comparison in SQLAlchemy
        if for_doctor:
            base_filters.append(PatientVitalSigns.share_with_doctor.is_(True))
        
        # Current vitals = only records for the current date (today UTC).
        # If multiple entries for same vital today, use the latest one (by record_date then id).
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(now.date(), datetime.max.time()).replace(tzinfo=timezone.utc)
        base_filters.append(PatientVitalSigns.record_date >= today_start)
        base_filters.append(PatientVitalSigns.record_date <= today_end)
        
        # Subquery: latest record_date per vital_name_id (max works on timestamp)
        latest_date_subq = (
            self.db.query(
                PatientVitalSigns.vital_name_id,
                func.max(PatientVitalSigns.record_date).label('max_date')
            )
            .filter(and_(*base_filters))
            .group_by(PatientVitalSigns.vital_name_id)
            .subquery()
        )
        # All records matching that latest date per vital; order by id desc so newest wins when building map
        recorded_vitals_query = (
            self.db.query(PatientVitalSigns)
            .join(
                latest_date_subq,
                and_(
                    PatientVitalSigns.vital_name_id == latest_date_subq.c.vital_name_id,
                    PatientVitalSigns.record_date == latest_date_subq.c.max_date
                )
            )
            .filter(and_(*base_filters))
            .order_by(PatientVitalSigns.id.desc())
        )
        recorded_vitals = recorded_vitals_query.all()
        # One record per vital_name_id (first occurrence = highest id when same max_date)
        recorded_vitals_map = {}
        for r in recorded_vitals:
            key = str(r.vital_name_id)
            if key not in recorded_vitals_map:
                recorded_vitals_map[key] = r
        
        # Build result: include all active vitals, with records where available
        result = []
        for vital_name in all_active_vitals:
            vital_name_id_str = str(vital_name.id)
            record = recorded_vitals_map.get(vital_name_id_str)
            
            result.append({
                "vital_name_id": vital_name.id,
                "record": record,
                "vital_name": vital_name
            })
        
        return result
    
    def get_historical_vital_signs_by_date(
        self,
        patient_id: UUID,
        days_back: Optional[int] = None,
        for_doctor: bool = False
    ) -> Dict[str, Any]:
        """
        Get historical vital signs grouped by date
        
        Groups vital signs records by date (YYYY-MM-DD format).
        Each date contains all active vitals, with records where available.
        Vitals without recorded values on a date will have null/empty values.
        
        **Important**: Excludes current date records - only returns past dates (historical data).
        
        Args:
            patient_id: Patient user ID
            days_back: Number of days to go back (None = all dates, excluding today)
            for_doctor: If True, only return records where share_with_doctor=True
            
        Returns:
            Dictionary with dates as keys (YYYY-MM-DD format) and arrays of vital signs as values
            Format: {
                "2025-01-07": [
                    {"vital_name_id": UUID, "record": PatientVitalSigns or None, "vital_name": VitalName},
                    ...
                ],
                "2025-01-05": [...],
                ...
            }
            Note: Today's date is excluded from results
        """
        from datetime import datetime, timedelta
        from app.services.vital_name_service import VitalNameService
        
        # Get all active vital names
        vital_name_service = VitalNameService(self.db)
        all_active_vitals = vital_name_service.get_all_vital_names(is_active=True)
        active_vital_ids = {vital.id for vital in all_active_vitals}
        
        # Calculate date range
        now = datetime.now(timezone.utc)
        today = now.date()  # Get today's date for exclusion
        
        if days_back:
            start_date = now - timedelta(days=days_back)
        else:
            # Get all records (no date limit)
            start_date = None
        
        # Build query
        base_filters = [
            PatientVitalSigns.patient_id == patient_id,
            PatientVitalSigns.deleted_at.is_(None)
        ]
        
        # Add consent filter if querying for doctor
        # Use is_(True) for proper boolean comparison in SQLAlchemy
        if for_doctor:
            base_filters.append(PatientVitalSigns.share_with_doctor.is_(True))
        
        query = self.db.query(PatientVitalSigns).filter(
            and_(*base_filters)
        )
        
        # Check total records before date filters (for debugging)
        total_before_date_filter = query.count()
        logger.info(f"Query before date filters: patient_id={patient_id}, for_doctor={for_doctor}, total_records={total_before_date_filter}")
        
        if start_date:
            query = query.filter(PatientVitalSigns.record_date >= start_date)
        
        # Exclude today's records - only get historical (past) records
        # Use timezone-aware date comparison to handle timezone properly
        # Convert today to datetime at start of day in UTC for proper comparison
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        logger.info(f"Filtering records before: {today_start} (today={today})")
        
        # Count before applying today filter
        count_before_today_filter = query.count()
        logger.info(f"Records after start_date filter: {count_before_today_filter}")
        
        query = query.filter(PatientVitalSigns.record_date < today_start)
        
        # Count after applying today filter
        count_after_today_filter = query.count()
        logger.info(f"Records after today filter: {count_after_today_filter}")
        
        # Order by date descending
        records = query.order_by(PatientVitalSigns.record_date.desc()).all()
        
        # Log query details for debugging
        logger.info(f"Final query result: patient_id={patient_id}, for_doctor={for_doctor}, found {len(records)} records")
        
        # Log sample record dates if any found
        if records:
            sample_dates = [r.record_date for r in records[:3]]
            logger.info(f"Sample record dates: {sample_dates}")
        
        # Group by date (YYYY-MM-DD format)
        dates_dict: Dict[str, Dict[UUID, PatientVitalSigns]] = {}
        
        for record in records:
            record_date = record.record_date
            if record_date.tzinfo is None:
                record_date = record_date.replace(tzinfo=timezone.utc)
            
            # Get date in YYYY-MM-DD format
            record_date_only = record_date.date()
            date_key = record_date_only.isoformat()
            
            # Skip today's date (double check to be safe)
            if record_date_only >= today:
                continue
            
            if date_key not in dates_dict:
                dates_dict[date_key] = {}
            
            # Only include if vital is still active
            if record.vital_name_id in active_vital_ids:
                dates_dict[date_key][record.vital_name_id] = record
        
        # Convert to response format: include all active vitals for each date as an array
        result = {}
        sorted_dates = sorted(dates_dict.keys(), reverse=True)
        
        for date_key in sorted_dates:
            date_records = dates_dict[date_key]
            # Build an array with all active vitals for this date
            date_vitals_list = []
            for vital_name in all_active_vitals:
                record = date_records.get(vital_name.id)
                date_vitals_list.append({
                    "vital_name_id": vital_name.id,
                    "record": record,
                    "vital_name": vital_name
                })
            
            result[date_key] = date_vitals_list
        
        return result
    
    def get_vital_signs_by_id(self, vital_signs_id: UUID) -> PatientVitalSigns:
        """
        Get vital signs record by ID
        
        Args:
            vital_signs_id: UUID of the vital signs record
            
        Returns:
            PatientVitalSigns object
            
        Raises:
            NotFoundException: If record not found
        """
        record = self.db.query(PatientVitalSigns).filter(
            and_(
                PatientVitalSigns.id == vital_signs_id,
                PatientVitalSigns.deleted_at.is_(None)
            )
        ).first()
        
        if not record:
            raise NotFoundException(f"Vital signs record with ID {vital_signs_id} not found")
        
        return record
    
    def update_vital_signs_record(
        self,
        vital_signs_id: UUID,
        numeric_value: Optional[Union[float, int, Decimal]] = None,
        text_value: Optional[str] = None,
        notes: Optional[str] = None,
        record_date: Optional[datetime] = None,
        share_with_doctor: Optional[bool] = None
    ) -> PatientVitalSigns:
        """
        Update a vital signs record
        
        Args:
            vital_signs_id: UUID of the record to update
            numeric_value: New numeric value
            text_value: New text value
            notes: New notes
            record_date: New record date
            
        Returns:
            Updated PatientVitalSigns object
        """
        record = self.get_vital_signs_by_id(vital_signs_id)
        
        # Get vital name to validate value type
        vital_name = self.db.query(VitalName).filter(
            and_(
                VitalName.id == record.vital_name_id,
                VitalName.deleted_at.is_(None)
            )
        ).first()
        
        if not vital_name:
            raise NotFoundException(f"Vital name for this record not found")
        
        # Update values
        if numeric_value is not None:
            if vital_name.data_type != "number":
                raise ValidationException(
                    message=f"Cannot set numeric_value for {vital_name.name} (data_type is {vital_name.data_type})",
                    errors={"numeric_value": [f"This vital uses {vital_name.data_type} data type, not number"]}
                )
            record.numeric_value = Decimal(str(numeric_value))
            record.text_value = None  # Clear text value if setting numeric
        
        if text_value is not None:
            if vital_name.data_type == "number":
                raise ValidationException(
                    message=f"Cannot set text_value for {vital_name.name} (data_type is number)",
                    errors={"text_value": [f"This vital uses number data type"]}
                )
            record.text_value = text_value
            record.numeric_value = None  # Clear numeric value if setting text
        
        if notes is not None:
            record.notes = notes
        
        if record_date is not None:
            record.record_date = record_date
        
        if share_with_doctor is not None:
            record.share_with_doctor = share_with_doctor
        
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(f"Updated vital signs record {vital_signs_id}")
        
        return record
    
    def update_all_consent(
        self,
        patient_id: UUID,
        share_with_doctor: bool
    ) -> int:
        """
        Update consent for ALL vital sign records of a patient
        
        Only the patient can update consent for their own records.
        
        Args:
            patient_id: Patient user ID
            share_with_doctor: New consent value to apply to all records
            
        Returns:
            Number of records updated
            
        Raises:
            ForbiddenException: If patient doesn't own the records
        """
        # Update all non-deleted records for this patient
        updated_count = self.db.query(PatientVitalSigns).filter(
            and_(
                PatientVitalSigns.patient_id == patient_id,
                PatientVitalSigns.deleted_at.is_(None)
            )
        ).update(
            {"share_with_doctor": share_with_doctor},
            synchronize_session=False
        )
        
        self.db.commit()
        
        logger.info(f"Updated consent for {updated_count} vital signs records (patient {patient_id}): {share_with_doctor}")
        
        return updated_count
    
    def delete_vital_signs_record(self, vital_signs_id: UUID) -> None:
        """
        Delete a vital signs record (soft delete)
        
        Args:
            vital_signs_id: UUID of the record to delete
        """
        record = self.get_vital_signs_by_id(vital_signs_id)
        
        from datetime import datetime, timezone
        record.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Deleted vital signs record {vital_signs_id}")
