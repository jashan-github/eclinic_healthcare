"""
Clinic Location Service
Business logic for clinic location management
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.clinic_location import ClinicLocation
from app.models.location import Country, State, City
from app.models.user import Clinic
from app.core.exceptions import NotFoundException, ValidationException
from loguru import logger


class ClinicLocationService:
    """Service for managing clinic locations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_location(
        self,
        clinic_id: UUID,
        name: str,
        branch_type: Optional[str],
        address: Optional[str],
        country_id: UUID,
        state_id: UUID,
        city_id: UUID,
        phone: Optional[str],
        email: Optional[str],
        is_primary: bool = False
    ) -> ClinicLocation:
        """
        Create a new clinic location
        
        Args:
            clinic_id: ID of the clinic
            name: Location name
            branch_type: Type of branch
            address: Full address
            country_id: Country ID
            state_id: State ID
            city_id: City ID
            phone: Contact phone
            email: Contact email
            is_primary: Whether this is the primary location
            
        Returns:
            Created ClinicLocation object
            
        Raises:
            NotFoundException: If clinic, country, state, or city not found
            ValidationException: If validation fails
        """
        # Verify clinic exists
        clinic = self.db.query(Clinic).filter(
            and_(
                Clinic.id == clinic_id,
                Clinic.deleted_at.is_(None)
            )
        ).first()
        
        if not clinic:
            raise NotFoundException(
                message="Clinic not found",
                errors={"clinic_id": ["Clinic with this ID does not exist"]}
            )
        
        # Verify country, state, and city exist
        country = self.db.query(Country).filter(Country.id == country_id).first()
        if not country:
            raise NotFoundException(
                message="Country not found",
                errors={"country_id": ["Country with this ID does not exist"]}
            )
        
        state = self.db.query(State).filter(State.id == state_id).first()
        if not state:
            raise NotFoundException(
                message="State not found",
                errors={"state_id": ["State with this ID does not exist"]}
            )
        
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise NotFoundException(
                message="City not found",
                errors={"city_id": ["City with this ID does not exist"]}
            )
        
        # If this is set as primary, unset other primary locations for this clinic
        if is_primary:
            self.db.query(ClinicLocation).filter(
                and_(
                    ClinicLocation.clinic_id == clinic_id,
                    ClinicLocation.is_primary == True,
                    ClinicLocation.deleted_at.is_(None)
                )
            ).update({"is_primary": False})
            self.db.flush()
        
        # Parse address to extract building_name and street_name if possible
        building_name = None
        street_name = None
        if address:
            # Simple parsing: first part before comma is building, rest is street
            parts = address.split(',', 1)
            if len(parts) > 0:
                building_name = parts[0].strip()
            if len(parts) > 1:
                street_name = parts[1].strip()
        
        # Create new location
        location = ClinicLocation(
            clinic_id=clinic_id,
            name=name,
            branch_type=branch_type,
            address=address,
            building_name=building_name,
            street_name=street_name,
            country_id=country_id,
            state_id=state_id,
            city_id=city_id,
            phone=phone,
            email=email,
            is_primary=is_primary
        )
        
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        
        logger.info(f"Created clinic location: {name} (id: {location.id}) for clinic {clinic_id}")
        
        return location
    
    def get_all_locations(
        self,
        clinic_id: Optional[UUID] = None
    ) -> List[ClinicLocation]:
        """
        Get all clinic locations
        
        Args:
            clinic_id: Optional filter by clinic ID
            
        Returns:
            List of ClinicLocation objects
        """
        query = self.db.query(ClinicLocation).filter(
            ClinicLocation.deleted_at.is_(None)
        )
        
        if clinic_id:
            query = query.filter(ClinicLocation.clinic_id == clinic_id)
        
        locations = query.order_by(
            ClinicLocation.is_primary.desc(),
            ClinicLocation.created_at.asc()
        ).all()
        
        return locations
    
    def get_location_by_id(self, location_id: UUID) -> ClinicLocation:
        """
        Get a clinic location by ID
        
        Args:
            location_id: Location ID
            
        Returns:
            ClinicLocation object
            
        Raises:
            NotFoundException: If location not found
        """
        location = self.db.query(ClinicLocation).filter(
            and_(
                ClinicLocation.id == location_id,
                ClinicLocation.deleted_at.is_(None)
            )
        ).first()
        
        if not location:
            raise NotFoundException(
                message="Location not found",
                errors={"id": ["Location with this ID does not exist"]}
            )
        
        return location
    
    def update_location(
        self,
        location_id: UUID,
        **kwargs
    ) -> ClinicLocation:
        """
        Update a clinic location
        
        Args:
            location_id: Location ID
            **kwargs: Fields to update
            
        Returns:
            Updated ClinicLocation object
            
        Raises:
            NotFoundException: If location not found
        """
        location = self.get_location_by_id(location_id)
        
        # If is_primary is being set to True, unset other primary locations
        if kwargs.get("is_primary") == True and not location.is_primary:
            self.db.query(ClinicLocation).filter(
                and_(
                    ClinicLocation.clinic_id == location.clinic_id,
                    ClinicLocation.is_primary == True,
                    ClinicLocation.deleted_at.is_(None),
                    ClinicLocation.id != location_id
                )
            ).update({"is_primary": False})
            self.db.flush()
        
        # Update address parsing if address is being updated
        if "address" in kwargs and kwargs["address"]:
            address = kwargs["address"]
            parts = address.split(',', 1)
            if len(parts) > 0:
                kwargs["building_name"] = parts[0].strip()
            if len(parts) > 1:
                kwargs["street_name"] = parts[1].strip()
        
        # Update fields
        for key, value in kwargs.items():
            if value is not None and hasattr(location, key):
                setattr(location, key, value)
        
        self.db.commit()
        self.db.refresh(location)
        
        logger.info(f"Updated clinic location: {location.name} (id: {location_id})")
        
        return location
    
    def delete_location(self, location_id: UUID) -> bool:
        """
        Soft delete a clinic location
        
        Args:
            location_id: Location ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If location not found
        """
        location = self.get_location_by_id(location_id)
        
        # Soft delete
        from datetime import datetime, timezone
        location.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Deleted clinic location: {location.name} (id: {location_id})")
        
        return True
    
    def format_location_response(self, location: ClinicLocation) -> dict:
        """
        Format a clinic location for API response
        
        Args:
            location: ClinicLocation object
            
        Returns:
            Formatted location dictionary
        """
        return {
            "id": str(location.id),
            "name": location.name,
            "branch_type": location.branch_type,
            "address": location.address,
            "building_name": location.building_name,
            "street_name": location.street_name,
            "pincode": location.pincode,
            "phone": location.phone,
            "email": location.email,
            "country": location.country.name if location.country else None,
            "state": location.state.name if location.state else None,
            "city": location.city.name if location.city else None,
            "country_id": str(location.country_id) if location.country_id else None,
            "state_id": str(location.state_id) if location.state_id else None,
            "city_id": str(location.city_id) if location.city_id else None,
            "latitude": float(location.latitude) if location.latitude else None,
            "longitude": float(location.longitude) if location.longitude else None,
            "is_primary": location.is_primary,
            "created_at": location.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": location.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
