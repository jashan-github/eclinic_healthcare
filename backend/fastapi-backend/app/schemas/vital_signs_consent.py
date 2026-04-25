"""
Vital Signs Consent schemas
Request/response models for updating consent to share vital signs with doctors
"""

from typing import Optional
from pydantic import BaseModel, Field


class VitalSignsConsentUpdate(BaseModel):
    """Update consent for all patient vital signs"""
    share_with_doctor: bool = Field(
        ...,
        description="""Patient consent to share all vital signs with doctor
        
        - `true`: Patient consents to share all vital signs with doctor (doctor can see all vitals)
        - `false`: Patient does not consent (doctor cannot see any vitals)
        
        **Important**: This updates consent for ALL vital signs recorded by the patient.
        Setting this to `false` will immediately hide all vital signs from doctor's view.
        """
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "share_with_doctor": True
            }
        }


class VitalSignsConsentUpdateResponse(BaseModel):
    """Response for consent update"""
    success: bool = True
    message: str = "Consent updated successfully"
    data: dict
    errors: Optional[dict] = None

