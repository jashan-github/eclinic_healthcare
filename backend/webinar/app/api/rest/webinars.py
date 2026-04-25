"""
Webinar API Endpoints
Admin, Doctor, and Patient routes for managing webinars.
Option B: Webinar microservice owns all webinar logic including go-live and join.
"""

from typing import Optional, Any
from fastapi import APIRouter, Depends, status, Path, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date, datetime, timezone
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import get_current_user_id, get_user_role, extract_token_from_header
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException, UnauthorizedException
from app.services.webinar_service import WebinarService
from app.services.video_session_service import VideoSessionService
from app.db.models_video_session import VideoSessionType
from app.schemas.webinar import (
    WebinarCreate,
    WebinarUpdate,
    WebinarListResponse,
    WebinarSingleResponse,
    WebinarDeleteResponse
)
from app.core.logging import logger

HOST_ROLES = {"doctor", "super_admin", "clinic_admin"}


def laravel_response(
    success: bool = True,
    message: str = "",
    data: Any = None,
    errors: Optional[dict] = None
) -> dict:
    """Generate Laravel-compatible response format"""
    return {
        "success": success,
        "message": message,
        "errors": errors,
        "data": data
    }


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from JWT token"""
    if not authorization:
        raise UnauthorizedException("Authorization header required")
    
    token = extract_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    role = await get_user_role(token)
    
    return {"id": UUID(user_id), "role": role}


async def get_current_admin_user(authorization: Optional[str] = Header(None)):
    """Get current admin user from JWT token"""
    user = await get_current_user(authorization)
    
    if user["role"] not in ["super_admin", "clinic_admin"]:
        raise ForbiddenException(
            message="Admin access required",
            errors={"role": ["Only admins can access this endpoint"]}
        )
    
    return user


admin_router = APIRouter(prefix="/admin/webinars", tags=["Admin - Webinars"])
doctor_router = APIRouter(prefix="/doctor/webinars", tags=["Doctor - Webinars"])
patient_router = APIRouter(prefix="/patient/webinars", tags=["Patient - Webinars"])


@admin_router.post(
    "",
    response_model=WebinarSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new webinar",
    description="""Create a new webinar/online event (Admin only)

**Use Cases:**

1. **Free webinars**:
   - Set `pricing_type: "free"` and `price: 0`
   - Open to all participants up to the limit

2. **Paid webinars**:
   - Set `pricing_type: "paid"` and specify the price
   - Participants must pay to register

3. **Public vs Private**:
   - `visibility: "public"` - Anyone can see and register
   - `visibility: "private"` - Only invited participants can see

4. **Status management**:
   - `draft` - Not yet published
   - `scheduled` - Published and accepting registrations
   - `live` - Currently happening
   - `completed` - Finished
   - `cancelled` - Cancelled

**Important Notes:**
- Host must be an admin (super_admin or clinic_admin) or a doctor
- End time must be after start time
- Price must be > 0 for paid webinars
- Agora channel and token are auto-generated for live streaming"""
)
async def create_webinar(
    request: WebinarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Create a new webinar"""
    try:
        # Convert time strings to time objects
        start_time_obj = datetime.strptime(request.start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(request.end_time, '%H:%M').time()
        
        service = WebinarService(db)
        
        # Default status to "scheduled" if not provided (so webinars are visible to patients immediately)
        # Admin can still set status="draft" explicitly if they want to create a draft first
        webinar_status = request.status if request.status is not None else "scheduled"
        
        logger.info(f"Creating webinar with status: {webinar_status} (provided: {request.status})")
        
        webinar = await service.create_webinar(
            title=request.title,
            description=request.description,
            webinar_date=request.webinar_date,
            start_time=start_time_obj,
            end_time=end_time_obj,
            pricing_type=request.pricing_type,
            price=request.price,
            participant_limit=request.participant_limit,
            host_id=request.host_id,
            created_by=current_user["id"],
            status=webinar_status,
            visibility=request.visibility,
            agenda=request.agenda
        )
        
        formatted_webinar = await service.format_webinar_response(webinar, user_id=None)
        
        return laravel_response(
            success=True,
            message="Webinar created successfully",
            data=formatted_webinar
        )
        
    except (NotFoundException, ValidationException) as e:
        logger.warning(f"Failed to create webinar: {e.message}")
        raise
    except ValueError as e:
        raise ValidationException(
            message="Invalid time format",
            errors={"time": ["Time must be in HH:MM format"]}
        )
    except Exception as e:
        logger.error(f"Unexpected error creating webinar: {str(e)}")
        raise ValidationException(
            message="Failed to create webinar",
            errors={"error": [str(e)]}
        )


@admin_router.get(
    "",
    response_model=WebinarListResponse,
    summary="Get all webinars",
    description="""Get all webinars (Admin only)

**Query Parameters:**
- `status`: Filter by status (draft, scheduled, live, completed, cancelled)
- `visibility`: Filter by visibility (public, private)
- `pricing_type`: Filter by pricing type (free, paid)
- `host_id`: Filter by host user ID

**Response Format:**
```json
{
  "status": true,
  "message": "Webinars retrieved successfully",
  "data": {
    "webinars": [...]
  }
}
```

**Notes:**
- Webinars are ordered by date (newest first), then by start time
- Only returns non-deleted webinars"""
)
async def get_webinars(
    status: Optional[str] = None,
    visibility: Optional[str] = None,
    pricing_type: Optional[str] = None,
    host_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get all webinars with optional filters"""
    try:
        service = WebinarService(db)
        webinars = await service.get_all_webinars(
            status=status,
            visibility=visibility,
            pricing_type=pricing_type,
            host_id=host_id
        )
        
        formatted_webinars = [
            await service.format_webinar_response(webinar, user_id=None)
            for webinar in webinars
        ]
        
        return laravel_response(
            success=True,
            message="Webinars retrieved successfully",
            data={"webinars": formatted_webinars}
        )
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving webinars: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve webinars",
            errors={"error": [str(e)]}
        )


@admin_router.get(
    "/{webinar_id}",
    response_model=WebinarSingleResponse,
    summary="Get a specific webinar",
    description="Get details of a specific webinar by ID (Admin only)"
)
async def get_webinar(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get a specific webinar"""
    try:
        service = WebinarService(db)
        webinar = await service.get_webinar_by_id(webinar_id)
        
        # Admin endpoints don't need user context for registration status
        formatted_webinar = await service.format_webinar_response(webinar, user_id=None)
        
        return laravel_response(
            success=True,
            message="Webinar retrieved successfully",
            data=formatted_webinar
        )
        
    except NotFoundException as e:
        logger.warning(f"Webinar not found: {webinar_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving webinar: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve webinar",
            errors={"error": [str(e)]}
        )


@admin_router.put(
    "/{webinar_id}",
    response_model=WebinarSingleResponse,
    summary="Update a webinar",
    description="""Update an existing webinar (Admin only)

**Notes:**
- Only provided fields will be updated
- Must maintain valid time range (end > start)
- Price must be > 0 for paid webinars
- All JSON fields are optional"""
)
async def update_webinar(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    request: WebinarUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Update a webinar"""
    try:
        service = WebinarService(db)
        
        # Build update data from request
        update_data = request.model_dump(exclude_unset=True) if request else {}
        
        updated_webinar = await service.update_webinar(webinar_id, **update_data)
        
        formatted_webinar = await service.format_webinar_response(updated_webinar, user_id=None)
        
        return laravel_response(
            success=True,
            message="Webinar updated successfully",
            data=formatted_webinar
        )
        
    except (NotFoundException, ValidationException) as e:
        logger.warning(f"Failed to update webinar: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating webinar: {str(e)}")
        raise ValidationException(
            message="Failed to update webinar",
            errors={"error": [str(e)]}
        )


@admin_router.delete(
    "/{webinar_id}",
    response_model=WebinarDeleteResponse,
    summary="Delete a webinar",
    description="""Delete a webinar (Admin only)

**Notes:**
- This is a soft delete (webinar is marked as deleted but not removed)
- Deleted webinars will not appear in list results
- Cannot be undone via API (requires database access)"""
)
async def delete_webinar(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """Delete a webinar"""
    try:
        service = WebinarService(db)
        await service.delete_webinar(webinar_id)
        
        return laravel_response(
            success=True,
            message="Webinar deleted successfully",
            data={}
        )
        
    except NotFoundException as e:
        logger.warning(f"Webinar not found: {webinar_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting webinar: {str(e)}")
        raise ValidationException(
            message="Failed to delete webinar",
            errors={"error": [str(e)]}
        )


class RegisteredCountUpdate(BaseModel):
    """Request body for updating registered count"""
    increment: int = 1


@admin_router.post(
    "/{webinar_id}/registered-count",
    response_model=WebinarSingleResponse,
    summary="Update registered count",
    description="Update the registered_count for a webinar (internal endpoint)"
)
async def update_registered_count(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    request: RegisteredCountUpdate = Body(RegisteredCountUpdate(increment=1)),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update registered_count for a webinar
    
    This is an internal endpoint used by the payment service to update
    registration counts when payments are completed.
    
    Request Body:
    - **increment**: Amount to increment (default: 1, use -1 to decrement)
    
    Returns:
    - Updated webinar with new registered_count
    """
    try:
        service = WebinarService(db)
        
        # Extract increment from request body (default to 1)
        increment = request.increment if request else 1
        
        updated_webinar = await service.update_registered_count(
            webinar_id=webinar_id,
            increment=increment
        )
        
        formatted_webinar = await service.format_webinar_response(updated_webinar, user_id=None)
        
        return laravel_response(
            success=True,
            message="Registered count updated successfully",
            data=formatted_webinar
        )
        
    except NotFoundException as e:
        logger.warning(f"Webinar not found: {webinar_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating registered count: {str(e)}")
        raise ValidationException(
            message="Failed to update registered count",
            errors={"error": [str(e)]}
        )


# ============================================================================
# DOCTOR ENDPOINTS
# ============================================================================

@doctor_router.get(
    "",
    response_model=WebinarListResponse,
    summary="Get upcoming webinars for doctors",
    description="""Get all upcoming webinars (Doctor access)

**Features:**
- Shows only upcoming webinars (scheduled or live)
- Includes webinars where doctor is the host
- Shows all public webinars
- Ordered by date (soonest first)

**Response includes:**
- All webinar details
- Registration and attendance counts
- Host information

**Use Cases:**
- View webinars you're hosting
- Discover webinars to attend
- Check upcoming events"""
)
async def get_upcoming_webinars_for_doctor(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming webinars for doctors"""
    try:
        service = WebinarService(db)
        
        # Get upcoming webinars (scheduled or live, date >= today)
        today = date.today()
        
        webinars = await service.get_upcoming_webinars(
            from_date=today,
            visibility=None  # Show both public and private for doctors
        )
        
        formatted_webinars = [
            await service.format_webinar_response(webinar, user_id=current_user["id"])
            for webinar in webinars
        ]
        
        return laravel_response(
            success=True,
            message="Upcoming webinars retrieved successfully",
            data={"webinars": formatted_webinars}
        )
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving upcoming webinars for doctor: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve upcoming webinars",
            errors={"error": [str(e)]}
        )


@doctor_router.get(
    "/{webinar_id}/join",
    response_model=WebinarSingleResponse,
    summary="Join live webinar",
    description="""Join a live webinar as a doctor
    
**Use Cases:**
- Join a webinar that is currently live
- Get Agora channel details for video streaming
- Access webinar information needed for joining

**Requirements:**
- Webinar must be in "live" status
- Doctor must be either:
  - The host of the webinar, OR
  - The webinar must be public
- Webinar must not be deleted

**Response includes:**
- Full webinar details
- Agora channel name and token for joining
- Host information
- Participant counts"""
)
async def join_live_webinar(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Join a live webinar as a doctor"""
    # Check if user is doctor
    if current_user["role"] != "doctor":
        raise ForbiddenException(
            message="This endpoint is only for doctors",
            errors={"role": ["Only doctors can use this endpoint"]}
        )
    
    try:
        service = WebinarService(db)
        
        # Get webinar by ID
        webinar = await service.get_webinar_by_id(webinar_id)
        
        # Verify webinar is live
        if webinar.status != "live":
            raise ValidationException(
                message="Webinar is not live",
                errors={"status": [f"Webinar is currently {webinar.status}. Only live webinars can be joined."]}
            )
        
        # Verify doctor can join: must be either the host OR the webinar must be public
        is_host = webinar.host_id == current_user["id"]
        is_public = webinar.visibility == "public"
        
        if not is_host and not is_public:
            raise ForbiddenException(
                message="Access denied",
                errors={"access": ["You can only join webinars you are hosting or public webinars"]}
            )
        
        formatted_webinar = await service.format_webinar_response(webinar, user_id=current_user["id"])
        
        return laravel_response(
            success=True,
            message="Webinar join details retrieved successfully",
            data=formatted_webinar
        )
        
    except (NotFoundException, ValidationException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error joining live webinar: {str(e)}")
        raise ValidationException(
            message="Failed to join webinar",
            errors={"error": [str(e)]}
        )


# ============================================================================
# GO-LIVE AND JOIN (host and audience) – webinar service owns full flow
# ============================================================================

async def _go_live_impl(webinar_id: UUID, db: AsyncSession, current_user: dict) -> dict:
    """Shared go-live: get/create video session, join as host, update webinar status, return token/channel."""
    role = current_user.get("role") or ""
    if role not in HOST_ROLES:
        raise ForbiddenException(
            message="Only hosts can go live",
            errors={"role": ["Only webinar hosts (admin or doctor) can use go-live"]}
        )
    service = WebinarService(db)
    webinar = await service.get_webinar_by_id(webinar_id)
    if str(webinar.host_id) != str(current_user["id"]):
        raise ForbiddenException(
            message="Only the host can go live",
            errors={"webinar_id": ["You are not the host of this webinar"]}
        )
    from datetime import datetime as dt
    scheduled_start = dt.combine(webinar.webinar_date, webinar.start_time).replace(tzinfo=timezone.utc)
    scheduled_end = dt.combine(webinar.webinar_date, webinar.end_time).replace(tzinfo=timezone.utc)
    video_svc = VideoSessionService(db)
    session = await video_svc.get_session_by_webinar_id(webinar_id)
    if not session:
        session = await video_svc.create_session(
            doctor_id=current_user["id"],
            patient_id=None,
            appointment_id=None,
            webinar_id=webinar_id,
            session_type=VideoSessionType.WEBINAR,
            scheduled_start_time=scheduled_start,
            scheduled_end_time=scheduled_end,
            recording_enabled=False,
        )
    join_result = await video_svc.request_join(
        session_id=session.session_id,
        user_id=current_user["id"],
        user_role=role,
        webinar_host_user_id=current_user["id"],
    )
    await service.update_webinar(webinar_id, status="live")
    return laravel_response(
        success=True,
        message="You are now live. Stream to your audience.",
        data={
            "session_id": str(session.session_id),
            "channel_name": join_result.get("channel_name") or session.channel_name,
            "token": join_result.get("token"),
            "app_id": join_result.get("app_id"),
            "waiting_room": join_result.get("waiting_room", False),
            "session_type": join_result.get("session_type", "webinar"),
        }
    )


@admin_router.post(
    "/{webinar_id}/go-live",
    status_code=status.HTTP_200_OK,
    summary="Go live as host (admin)",
    description="Start the webinar as host. Returns Agora session_id, channel_name, token, app_id.",
)
async def go_live_admin(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await _go_live_impl(webinar_id, db, current_user)


@doctor_router.post(
    "/{webinar_id}/go-live",
    status_code=status.HTTP_200_OK,
    summary="Go live as host (doctor)",
    description="Start the webinar as host. Returns Agora session_id, channel_name, token, app_id.",
)
async def go_live_doctor(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await _go_live_impl(webinar_id, db, current_user)


async def _join_audience_impl(webinar_id: UUID, db: AsyncSession, current_user: dict) -> dict:
    """Join webinar as audience. Paid check is done inside VideoSessionService.request_join."""
    service = WebinarService(db)
    webinar = await service.get_webinar_by_id(webinar_id)
    if webinar.status == "cancelled":
        raise ValidationException(
            message="Webinar is cancelled",
            errors={"webinar_id": ["This webinar has been cancelled"]}
        )
    video_svc = VideoSessionService(db)
    session = await video_svc.get_session_by_webinar_id(webinar_id)
    if not session:
        raise NotFoundException(
            message="No active video session for this webinar",
            errors={"webinar_id": ["The host has not started this webinar yet."]}
        )
    join_result = await video_svc.request_join(
        session_id=session.session_id,
        user_id=current_user["id"],
        user_role=current_user.get("role") or "patient",
        webinar_host_user_id=None,
    )
    return laravel_response(
        success=True,
        message="Join details retrieved",
        data={
            "session_id": str(session.session_id),
            "channel_name": join_result.get("channel_name"),
            "token": join_result.get("token"),
            "app_id": join_result.get("app_id"),
            "waiting_room": join_result.get("waiting_room", False),
            "message": join_result.get("message"),
            "session_type": join_result.get("session_type", "webinar"),
        }
    )


@doctor_router.post(
    "/{webinar_id}/join",
    status_code=status.HTTP_200_OK,
    summary="Join webinar as audience (doctor)",
    description="Join as audience when you are not the host. For host use go-live.",
)
async def join_webinar_audience_doctor(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "doctor":
        raise ForbiddenException(
            message="This endpoint is for doctors only",
            errors={"role": ["Use patient join if you are a patient"]}
        )
    service = WebinarService(db)
    webinar = await service.get_webinar_by_id(webinar_id)
    if str(webinar.host_id) == str(current_user["id"]):
        raise ValidationException(
            message="Use go-live to start the webinar",
            errors={"webinar_id": ["You are the host. Use POST go-live to start."]}
        )
    return await _join_audience_impl(webinar_id, db, current_user)


@patient_router.post(
    "/{webinar_id}/join",
    status_code=status.HTTP_200_OK,
    summary="Join webinar as audience",
    description="Join as audience. For paid webinars, registration/payment is checked.",
)
async def join_webinar_audience_patient(
    webinar_id: UUID = Path(..., description="Webinar ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await _join_audience_impl(webinar_id, db, current_user)


# ============================================================================
# PATIENT ENDPOINTS
# ============================================================================

@patient_router.get(
    "",
    response_model=WebinarListResponse,
    summary="Get upcoming webinars for patients",
    description="""Get all upcoming public webinars (Patient access)

**Features:**
- Shows only upcoming PUBLIC webinars
- Only shows scheduled or live webinars
- Excludes draft, completed, or cancelled webinars
- Ordered by date (soonest first)

**Response includes:**
- All webinar details
- Registration and attendance counts
- Host information
- Pricing information

**Use Cases:**
- Browse available webinars
- Check registration requirements
- View webinar schedule"""
)
async def get_upcoming_webinars_for_patient(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming public webinars for patients"""
    try:
        service = WebinarService(db)
        
        # Get upcoming PUBLIC webinars only
        today = date.today()
        
        webinars = await service.get_upcoming_webinars(
            from_date=today,
            visibility="public"  # Only show public webinars for patients
        )
        
        formatted_webinars = [
            await service.format_webinar_response(webinar, user_id=current_user["id"])
            for webinar in webinars
        ]
        
        return laravel_response(
            success=True,
            message="Upcoming webinars retrieved successfully",
            data={"webinars": formatted_webinars}
        )
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving upcoming webinars for patient: {str(e)}")
        raise ValidationException(
            message="Failed to retrieve upcoming webinars",
            errors={"error": [str(e)]}
        )
