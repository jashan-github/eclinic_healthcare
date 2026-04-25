"""
Webinar Service
Business logic for webinar management
"""

from typing import Optional, List
from uuid import UUID
from datetime import date, time, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from decimal import Decimal

from app.models.webinar import Webinar
from app.models.user import User
from app.core.exceptions import NotFoundException, ValidationException
from loguru import logger


class WebinarService:
    """Service for managing webinars"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_webinar(
        self,
        title: str,
        webinar_date: date,
        start_time: time,
        end_time: time,
        host_id: UUID,
        created_by: UUID,
        description: Optional[str] = None,
        pricing_type: str = "free",
        price: Decimal = Decimal("0.00"),
        participant_limit: Optional[int] = None,
        status: str = "draft",
        visibility: str = "public",
        agenda: Optional[str] = None
    ) -> Webinar:
        """
        Create a new webinar
        
        Args:
            title: Webinar title
            webinar_date: Date of the webinar
            start_time: Start time
            end_time: End time
            host_id: Host user ID
            created_by: Creator user ID
            description: Webinar description
            pricing_type: Pricing type (free or paid)
            price: Price for paid webinars
            participant_limit: Maximum number of participants
            status: Webinar status
            visibility: Visibility (public or private)
            agenda: Webinar agenda
            
        Returns:
            Created Webinar object
            
        Raises:
            NotFoundException: If host user not found
            ValidationException: If validation fails
        """
        # Verify host exists and is either admin or doctor
        host = self.db.query(User).filter(
            and_(
                User.id == host_id,
                User.deleted_at.is_(None)
            )
        ).first()
        
        if not host:
            raise NotFoundException(
                message="Host not found",
                errors={"host_id": ["Host with this ID does not exist"]}
            )
        
        # Validate host role: must be admin (super_admin or clinic_admin) or doctor
        valid_host_roles = ["super_admin", "clinic_admin", "doctor"]
        if host.role not in valid_host_roles:
            raise ValidationException(
                message="Invalid host role",
                errors={"host_id": [f"Host must be an admin or doctor. Current role: {host.role}"]}
            )
        
        # Validate time range
        if end_time <= start_time:
            raise ValidationException(
                message="Invalid time range",
                errors={"end_time": ["End time must be after start time"]}
            )
        
        # Validate pricing
        if pricing_type == "paid" and price <= 0:
            raise ValidationException(
                message="Invalid price",
                errors={"price": ["Price must be greater than 0 for paid webinars"]}
            )
        
        # Create new webinar
        webinar = Webinar(
            title=title,
            description=description,
            webinar_date=webinar_date,
            start_time=start_time,
            end_time=end_time,
            pricing_type=pricing_type,
            price=price,
            participant_limit=participant_limit,
            host_id=host_id,
            created_by=created_by,
            status=status,
            visibility=visibility,
            agenda=agenda,
            registered_count=0,
            attended_count=0
        )
        
        self.db.add(webinar)
        self.db.commit()
        self.db.refresh(webinar)
        
        logger.info(f"Created webinar: {title} (id: {webinar.id}) for date {webinar_date}")
        
        return webinar
    
    def get_all_webinars(
        self,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        pricing_type: Optional[str] = None,
        host_id: Optional[UUID] = None
    ) -> List[Webinar]:
        """
        Get all webinars
        
        Args:
            status: Optional filter by status
            visibility: Optional filter by visibility
            pricing_type: Optional filter by pricing type
            host_id: Optional filter by host ID
            
        Returns:
            List of Webinar objects
        """
        query = self.db.query(Webinar).filter(
            Webinar.deleted_at.is_(None)
        )
        
        if status:
            query = query.filter(Webinar.status == status)
        
        if visibility:
            query = query.filter(Webinar.visibility == visibility)
        
        if pricing_type:
            query = query.filter(Webinar.pricing_type == pricing_type)
        
        if host_id:
            query = query.filter(Webinar.host_id == host_id)
        
        webinars = query.order_by(
            Webinar.webinar_date.desc(),
            Webinar.start_time.desc()
        ).all()
        
        return webinars
    
    def get_upcoming_webinars(
        self,
        from_date: date,
        visibility: Optional[str] = None
    ) -> List[Webinar]:
        """
        Get upcoming webinars (scheduled or live)
        
        Args:
            from_date: Start date to filter from (inclusive)
            visibility: Optional filter by visibility (public/private). None = all
            
        Returns:
            List of Webinar objects ordered by date (soonest first)
        """
        query = self.db.query(Webinar).filter(
            and_(
                Webinar.deleted_at.is_(None),
                Webinar.webinar_date >= from_date,
                or_(
                    Webinar.status == 'scheduled',
                    Webinar.status == 'live'
                )
            )
        )
        
        if visibility:
            query = query.filter(Webinar.visibility == visibility)
        
        webinars = query.order_by(
            Webinar.webinar_date.asc(),
            Webinar.start_time.asc()
        ).all()
        
        return webinars
    
    def get_webinar_by_id(self, webinar_id: UUID) -> Webinar:
        """
        Get a webinar by ID
        
        Args:
            webinar_id: Webinar ID
            
        Returns:
            Webinar object
            
        Raises:
            NotFoundException: If webinar not found
        """
        webinar = self.db.query(Webinar).filter(
            and_(
                Webinar.id == webinar_id,
                Webinar.deleted_at.is_(None)
            )
        ).first()
        
        if not webinar:
            raise NotFoundException(
                message="Webinar not found",
                errors={"id": ["Webinar with this ID does not exist"]}
            )
        
        return webinar
    
    def update_webinar(
        self,
        webinar_id: UUID,
        **kwargs
    ) -> Webinar:
        """
        Update a webinar
        
        Args:
            webinar_id: Webinar ID
            **kwargs: Fields to update
            
        Returns:
            Updated Webinar object
            
        Raises:
            NotFoundException: If webinar not found
            ValidationException: If validation fails
        """
        webinar = self.get_webinar_by_id(webinar_id)
        
        # Validate time range if both times are being updated
        start_time = kwargs.get('start_time', webinar.start_time)
        end_time = kwargs.get('end_time', webinar.end_time)
        
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M').time()
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%H:%M').time()
        
        if end_time <= start_time:
            raise ValidationException(
                message="Invalid time range",
                errors={"end_time": ["End time must be after start time"]}
            )
        
        # Validate pricing if being updated
        pricing_type = kwargs.get('pricing_type', webinar.pricing_type)
        price = kwargs.get('price', webinar.price)
        
        if pricing_type == "paid" and price <= 0:
            raise ValidationException(
                message="Invalid price",
                errors={"price": ["Price must be greater than 0 for paid webinars"]}
            )
        
        # Update fields
        for key, value in kwargs.items():
            if value is not None and hasattr(webinar, key):
                # Convert string time to time object if needed
                if key in ['start_time', 'end_time'] and isinstance(value, str):
                    value = datetime.strptime(value, '%H:%M').time()
                setattr(webinar, key, value)
        
        self.db.commit()
        self.db.refresh(webinar)
        
        logger.info(f"Updated webinar: {webinar.title} (id: {webinar_id})")
        
        return webinar
    
    def delete_webinar(self, webinar_id: UUID) -> bool:
        """
        Soft delete a webinar
        
        Args:
            webinar_id: Webinar ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If webinar not found
        """
        webinar = self.get_webinar_by_id(webinar_id)
        
        # Soft delete
        from datetime import timezone
        webinar.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(f"Deleted webinar: {webinar.title} (id: {webinar_id})")
        
        return True
    
    def format_webinar_response(self, webinar: Webinar) -> dict:
        """
        Format a webinar for API response
        
        Args:
            webinar: Webinar object
            
        Returns:
            Formatted webinar dictionary with host details
        """
        # Get host details if host_id exists
        host_details = None
        if webinar.host_id:
            # Load host relationship if not already loaded
            if not webinar.host:
                host = self.db.query(User).filter(
                    and_(
                        User.id == webinar.host_id,
                        User.deleted_at.is_(None)
                    )
                ).first()
            else:
                host = webinar.host
            
            if host:
                # Build host profile image URL if available
                host_image = None
                if hasattr(host, 'profile_image') and host.profile_image:
                    from app.core.config import settings
                    base_url = settings.BASE_URL.rstrip('/')
                    # Remove leading slash from profile_image if present
                    image_path = host.profile_image.lstrip('/') if host.profile_image.startswith('/') else host.profile_image
                    host_image = f"{base_url}{image_path}" if not image_path.startswith('http') else host.profile_image
                
                host_details = {
                    "id": str(host.id),
                    "name": host.name,
                    "email": host.email,
                    "profile_image": host_image,
                    "role": host.role
                }
        
        response = {
            "id": str(webinar.id),
            "title": webinar.title,
            "description": webinar.description,
            "webinar_date": webinar.webinar_date.strftime("%Y-%m-%d"),
            "start_time": webinar.start_time.strftime("%H:%M:%S"),
            "end_time": webinar.end_time.strftime("%H:%M:%S"),
            "pricing_type": webinar.pricing_type,
            "price": str(webinar.price),
            "participant_limit": webinar.participant_limit,
            "host_id": str(webinar.host_id) if webinar.host_id else None,
            "host": host_details,  # Add host details
            "created_by": str(webinar.created_by) if webinar.created_by else None,
            "status": webinar.status,
            "visibility": webinar.visibility,
            "agora_channel_name": webinar.agora_channel_name,
            "agora_token": webinar.agora_token,
            "registered_count": webinar.registered_count,
            "attended_count": webinar.attended_count,
            "agenda": webinar.agenda,
            "created_at": webinar.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": webinar.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "deleted_at": webinar.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if webinar.deleted_at else None
        }
        
        return response