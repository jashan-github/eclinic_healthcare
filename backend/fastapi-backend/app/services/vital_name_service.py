"""
Vital Name Service
Business logic for vital name management
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.vital_name import VitalName
from app.core.exceptions import NotFoundException, ConflictException, ValidationException
from loguru import logger


class VitalNameService:
    """Service for managing vital names"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_vital_name(
        self,
        name: str,
        unit: Optional[str] = None,
        display_order: Optional[str] = "0",
        is_active: bool = True,
        data_type: Optional[str] = "number",
        options: Optional[str] = None,
        max_entries_per_day: Optional[str] = "1"
    ) -> VitalName:
        """
        Create a new vital name
        
        Args:
            name: Vital sign name
            unit: Unit of measurement
            display_order: Display order for sorting
            is_active: Whether this vital name is active
            data_type: Data type (number, text, select, etc.)
            options: JSON string for select options
            
        Returns:
            Created VitalName object
            
        Raises:
            ConflictException: If vital name with same name already exists
        """
        # Check if vital name with same name already exists
        existing = self.db.query(VitalName).filter(
            and_(
                VitalName.name == name,
                VitalName.deleted_at.is_(None)
            )
        ).first()
        
        if existing:
            raise ConflictException(
                message="Vital name already exists",
                errors={"name": ["A vital name with this name already exists"]}
            )
        
        # Create new vital name
        vital_name = VitalName(
            name=name,
            unit=unit,
            display_order=display_order or "0",
            is_active=is_active,
            data_type=data_type or "number",
            options=options,
            max_entries_per_day=max_entries_per_day or "1"
        )
        
        self.db.add(vital_name)
        self.db.commit()
        self.db.refresh(vital_name)
        
        logger.info(f"Created vital name: {name} (id: {vital_name.id})")
        
        return vital_name
    
    def get_all_vital_names(
        self,
        is_active: Optional[bool] = None
    ) -> List[VitalName]:
        """
        Get all vital names
        
        Args:
            is_active: Filter by active status (None = all)
            
        Returns:
            List of VitalName objects
        """
        query = self.db.query(VitalName).filter(
            VitalName.deleted_at.is_(None)
        )
        
        if is_active is not None:
            query = query.filter(VitalName.is_active == is_active)
        
        # Order by display_order, then by name
        vital_names = query.order_by(
            VitalName.display_order.asc(),
            VitalName.name.asc()
        ).all()
        
        return vital_names
    
    def get_vital_name_by_id(self, vital_name_id: UUID) -> VitalName:
        """
        Get vital name by ID
        
        Args:
            vital_name_id: UUID of the vital name
            
        Returns:
            VitalName object
            
        Raises:
            NotFoundException: If vital name not found
        """
        vital_name = self.db.query(VitalName).filter(
            and_(
                VitalName.id == vital_name_id,
                VitalName.deleted_at.is_(None)
            )
        ).first()
        
        if not vital_name:
            raise NotFoundException(f"Vital name with ID {vital_name_id} not found")
        
        return vital_name
    
    def update_vital_name(
        self,
        vital_name_id: UUID,
        name: Optional[str] = None,
        unit: Optional[str] = None,
        display_order: Optional[str] = None,
        is_active: Optional[bool] = None,
        data_type: Optional[str] = None,
        options: Optional[str] = None,
        max_entries_per_day: Optional[str] = None
    ) -> VitalName:
        """
        Update a vital name
        
        Args:
            vital_name_id: UUID of the vital name to update
            name: New vital sign name
            unit: New unit of measurement
            display_order: New display order
            is_active: New active status
            data_type: New data type
            options: New options JSON string
            
        Returns:
            Updated VitalName object
            
        Raises:
            NotFoundException: If vital name not found
            ConflictException: If new name conflicts with existing vital name
        """
        vital_name = self.get_vital_name_by_id(vital_name_id)
        
        # Check for name conflict if name is being changed
        if name and name != vital_name.name:
            existing = self.db.query(VitalName).filter(
                and_(
                    VitalName.name == name,
                    VitalName.id != vital_name_id,
                    VitalName.deleted_at.is_(None)
                )
            ).first()
            
            if existing:
                raise ConflictException(
                    message="Vital name already exists",
                    errors={"name": ["A vital name with this name already exists"]}
                )
        
        # Update fields
        if name is not None:
            vital_name.name = name
        if unit is not None:
            vital_name.unit = unit
        if display_order is not None:
            vital_name.display_order = display_order
        if is_active is not None:
            vital_name.is_active = is_active
        if data_type is not None:
            vital_name.data_type = data_type
        if options is not None:
            vital_name.options = options
        # Always set max_entries_per_day to "1" (handled in backend)
        vital_name.max_entries_per_day = max_entries_per_day or "1"
        
        self.db.commit()
        self.db.refresh(vital_name)
        
        logger.info(f"Updated vital name: {vital_name.name} (id: {vital_name.id})")
        
        return vital_name
    
    def delete_vital_name(self, vital_name_id: UUID) -> None:
        """
        Delete a vital name (soft delete)
        
        Args:
            vital_name_id: UUID of the vital name to delete
            
        Raises:
            NotFoundException: If vital name not found
        """
        vital_name = self.get_vital_name_by_id(vital_name_id)
        
        # Soft delete
        from datetime import datetime, timezone
        vital_name.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Deleted vital name: {vital_name.name} (id: {vital_name.id})")

