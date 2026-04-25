"""
Pydantic schemas for service commission (admin).
Rate 1-100 (decimal), status ACTIVE/INACTIVE.
"""

from decimal import Decimal
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


CommissionStatus = Literal["ACTIVE", "INACTIVE"]


class ServiceCommissionCreateUpdate(BaseModel):
    """Request body for create/update commission (admin)."""

    rate: Decimal = Field(
        ...,
        ge=1,
        le=100,
        description="Commission rate 1-100 (percentage), decimal allowed",
    )
    status: CommissionStatus = Field(
        "ACTIVE",
        description="ACTIVE or INACTIVE",
    )


class ServiceCommissionResponse(BaseModel):
    """Single commission response."""

    id: UUID
    service_id: UUID
    rate: float
    status: str

    class Config:
        from_attributes = True


class ServiceCommissionWithServiceResponse(BaseModel):
    """Commission with minimal service info (for list)."""

    id: UUID
    service_id: UUID
    service_name: Optional[str] = None
    rate: float
    status: str

    class Config:
        from_attributes = True
