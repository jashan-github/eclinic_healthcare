"""
Webinar Service
Business logic for webinar management (async)
"""

from typing import Optional, List
from uuid import UUID
from datetime import date, time, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, text
from decimal import Decimal

from app.db.models import Webinar
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException
from app.core.logging import logger
from app.services.agora_service import agora_service


class WebinarService:
    """Service for managing webinars (async)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_webinar(
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
        status: str = "scheduled",
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
        # Note: We query the users table directly from shared database
        host_query = text("""
            SELECT id, role, deleted_at 
            FROM users 
            WHERE id = :host_id AND deleted_at IS NULL
        """)
        result = await self.db.execute(host_query, {"host_id": str(host_id)})
        host_row = result.fetchone()
        
        if not host_row:
            raise NotFoundException(
                message="Host not found",
                errors={"host_id": ["Host with this ID does not exist"]}
            )
        
        # Validate host role: must be admin (super_admin or clinic_admin) or doctor
        valid_host_roles = ["super_admin", "clinic_admin", "doctor"]
        if host_row.role not in valid_host_roles:
            raise ValidationException(
                message="Invalid host role",
                errors={"host_id": [f"Host must be an admin or doctor. Current role: {host_row.role}"]}
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
        await self.db.flush()  # Flush to get the webinar.id
        
        # Generate Agora Interactive Live Streaming channel name for webinar (1-to-many)
        # This channel supports multiple participants based on participant_limit
        # Host will join as publisher, participants can join as publisher (interactive) or subscriber (audience)
        agora_channel_name = agora_service.generate_secure_channel_name(webinar.id)
        webinar.agora_channel_name = agora_channel_name
        
        logger.info(
            f"Generated Agora channel '{agora_channel_name}' for webinar {webinar.id} "
            f"(participant_limit: {participant_limit})"
        )
        
        await self.db.commit()
        await self.db.refresh(webinar)
        
        logger.info(f"Created webinar: {title} (id: {webinar.id}) for date {webinar_date}")
        
        return webinar
    
    async def get_all_webinars(
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
        query = select(Webinar).where(Webinar.deleted_at.is_(None))
        
        if status:
            query = query.where(Webinar.status == status)
        
        if visibility:
            query = query.where(Webinar.visibility == visibility)
        
        if pricing_type:
            query = query.where(Webinar.pricing_type == pricing_type)
        
        if host_id:
            query = query.where(Webinar.host_id == host_id)
        
        query = query.order_by(Webinar.webinar_date.desc(), Webinar.start_time.desc())
        
        result = await self.db.execute(query)
        webinars = result.scalars().all()
        
        return list(webinars)
    
    async def get_upcoming_webinars(
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
        query = select(Webinar).where(
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
            query = query.where(Webinar.visibility == visibility)
        
        query = query.order_by(Webinar.webinar_date.asc(), Webinar.start_time.asc())
        
        result = await self.db.execute(query)
        webinars = result.scalars().all()
        
        return list(webinars)
    
    async def get_webinar_by_id(self, webinar_id: UUID) -> Webinar:
        """
        Get a webinar by ID
        
        Args:
            webinar_id: Webinar ID
            
        Returns:
            Webinar object
            
        Raises:
            NotFoundException: If webinar not found
        """
        query = select(Webinar).where(
            and_(
                Webinar.id == webinar_id,
                Webinar.deleted_at.is_(None)
            )
        )
        
        result = await self.db.execute(query)
        webinar = result.scalar_one_or_none()
        
        if not webinar:
            raise NotFoundException(
                message="Webinar not found",
                errors={"id": ["Webinar with this ID does not exist"]}
            )
        
        return webinar
    
    async def update_webinar(
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
        webinar = await self.get_webinar_by_id(webinar_id)
        
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
        
        await self.db.commit()
        await self.db.refresh(webinar)
        
        logger.info(f"Updated webinar: {webinar.title} (id: {webinar_id})")
        
        return webinar
    
    async def mark_past_webinars_completed(self) -> int:
        """
        Mark webinars as completed when their end time (webinar_date + end_time, UTC) has passed.
        Only updates webinars with status 'scheduled' or 'live'.

        Returns:
            Number of webinars updated to completed.
        """
        now_utc = datetime.now(timezone.utc)
        query = select(Webinar).where(
            and_(
                Webinar.deleted_at.is_(None),
                Webinar.status.in_(["scheduled", "live"]),
            )
        )
        result = await self.db.execute(query)
        webinars = result.scalars().all()
        count = 0
        for webinar in webinars:
            end_dt = datetime.combine(
                webinar.webinar_date,
                webinar.end_time,
                tzinfo=timezone.utc,
            )
            if end_dt < now_utc:
                webinar.status = "completed"
                count += 1
                logger.info(
                    f"Marked webinar as completed: id={webinar.id} title={webinar.title} "
                    f"end={end_dt.isoformat()}"
                )
        if count:
            await self.db.commit()
        return count

    async def delete_webinar(self, webinar_id: UUID) -> bool:
        """
        Soft delete a webinar

        Args:
            webinar_id: Webinar ID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundException: If webinar not found
        """
        webinar = await self.get_webinar_by_id(webinar_id)
        
        # Soft delete
        webinar.deleted_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        
        logger.info(f"Deleted webinar: {webinar.title} (id: {webinar_id})")
        
        return True
    
    async def format_webinar_response(self, webinar: Webinar, user_id: Optional[UUID] = None) -> dict:
        """
        Format a webinar for API response
        
        Args:
            webinar: Webinar object
            user_id: Optional user ID to check registration and join status
            
        Returns:
            Formatted webinar dictionary with host details, registration status, and join eligibility
        """
        # Get host details if host_id exists
        host_details = None
        if webinar.host_id:
            host_query = text("""
                SELECT id, name, email, avatar, role 
                FROM users 
                WHERE id = :host_id AND deleted_at IS NULL
            """)
            result = await self.db.execute(host_query, {"host_id": str(webinar.host_id)})
            host_row = result.fetchone()
            
            if host_row:
                # Build host profile image URL if available
                host_image = None
                if host_row.avatar:
                    from app.core.config import settings
                    base_url = settings.BASE_URL
                    # Remove leading slash from profile_image if present
                    image_path = host_row.avatar.lstrip('/') if host_row.avatar.startswith('/') else host_row.avatar
                    host_image = f"{base_url}{image_path}" if not image_path.startswith('http') else host_row.avatar
                
                host_role = host_row.role
                host_details = {
                    "id": str(host_row.id),
                    "name": host_row.name,
                    "email": host_row.email,
                    "profile_image": host_image,
                    "role": host_role
                }
                
                # When host is a doctor, add education, experience, and specialty from shared DB
                if host_role == "doctor":
                    # Initialize doctor fields
                    host_details["education"] = None
                    host_details["years_of_experience"] = None
                    host_details["specialty"] = None
                    
                    try:
                        # Get profile info (education, years_of_experience)
                        profile_query = text("""
                            SELECT education, years_of_experience
                            FROM user_profiles
                            WHERE user_id = :host_id
                            LIMIT 1
                        """)
                        profile_result = await self.db.execute(profile_query, {"host_id": str(webinar.host_id)})
                        profile_row = profile_result.fetchone()
                        if profile_row:
                            host_details["education"] = profile_row._mapping.get("education")
                            host_details["years_of_experience"] = profile_row._mapping.get("years_of_experience")
                        
                        # Get specialties from medical services
                        specialty_query = text("""
                            SELECT ms.name
                            FROM user_medical_services ums
                            JOIN medical_services ms ON ums.medical_service_id = ms.id
                            WHERE ums.user_id = :host_id AND ms.status = true
                            ORDER BY ms.name
                        """)
                        specialty_result = await self.db.execute(specialty_query, {"host_id": str(webinar.host_id)})
                        specialty_rows = specialty_result.fetchall()
                        if specialty_rows:
                            specialties = [row._mapping.get("name") for row in specialty_rows if row._mapping.get("name")]
                            host_details["specialty"] = ", ".join(specialties) if specialties else None
                    except Exception as e:
                        logger.error(f"Failed to fetch doctor profile/specialty for host {webinar.host_id}: {e}")
        
        # Check registration and join eligibility if user_id provided
        is_registered = False
        can_join = False
        
        if user_id:
            # Check if user is the host (host can always join)
            is_host = webinar.host_id and str(webinar.host_id) == str(user_id)
            
            if is_host:
                # Host can always join if webinar is live or scheduled
                is_registered = True
                can_join = webinar.status in ["scheduled", "live"]
            else:
                # Check if user has completed payment/registration
                # Query webinar_payments table from shared database
                payment_query = text("""
                    SELECT id, status
                    FROM webinar_payments
                    WHERE webinar_id = :webinar_id 
                      AND user_id = :user_id 
                      AND status = 'COMPLETED'
                    LIMIT 1
                """)
                payment_result = await self.db.execute(
                    payment_query,
                    {
                        "webinar_id": str(webinar.id),
                        "user_id": str(user_id)
                    }
                )
                payment_row = payment_result.fetchone()
                
                if payment_row:
                    is_registered = True
                    # User can join if registered AND webinar is scheduled or live
                    can_join = webinar.status in ["scheduled", "live"]
                else:
                    # Not registered - cannot join (must register/pay first)
                    is_registered = False
                    can_join = False
        
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
            "created_at": webinar.created_at.strftime("%Y-%m-%d %H:%M:%S") if webinar.created_at else None,
            "updated_at": webinar.updated_at.strftime("%Y-%m-%d %H:%M:%S") if webinar.updated_at else None,
            "deleted_at": webinar.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if webinar.deleted_at else None,
            "is_registered": is_registered,  # Whether user has registered (completed payment if paid)
            "can_join": can_join  # Whether user can join the webinar (registered + status allows)
        }
        
        return response
    
    async def update_registered_count(
        self,
        webinar_id: UUID,
        increment: int = 1
    ) -> Webinar:
        """
        Update registered_count for a webinar
        
        Args:
            webinar_id: Webinar ID
            increment: Amount to increment (default: 1, use -1 to decrement)
            
        Returns:
            Updated Webinar object
            
        Raises:
            NotFoundException: If webinar not found
        """
        webinar = await self.get_webinar_by_id(webinar_id)
        
        # Update registered_count (ensure it doesn't go below 0)
        new_count = webinar.registered_count + increment
        webinar.registered_count = max(0, new_count)
        
        await self.db.commit()
        await self.db.refresh(webinar)
        
        logger.info(
            f"Updated registered_count for webinar {webinar_id}: "
            f"{webinar.registered_count - increment} -> {webinar.registered_count}"
        )
        
        return webinar
