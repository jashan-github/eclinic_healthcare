"""
Service commission model.
Admin-defined commission rate per service with ACTIVE/INACTIVE status.
"""

from sqlalchemy import Column, String, Numeric, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ServiceCommission(BaseModel):
    """
    Commission configuration per service.
    One commission record per service; rate 1-100 (decimal), status ACTIVE/INACTIVE.
    """

    __tablename__ = "service_commissions"

    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Service ID (one commission per service)",
    )
    rate = Column(
        Numeric(5, 2),
        nullable=False,
        comment="Commission rate 1-100 (percentage), decimal allowed",
    )
    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
        comment="ACTIVE or INACTIVE",
    )

    # Relationships
    service = relationship("Service", foreign_keys=[service_id], lazy="select")

    __table_args__ = (
        CheckConstraint(
            "rate >= 1 AND rate <= 100",
            name="service_commissions_rate_range_check",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="service_commissions_status_check",
        ),
    )

    def __repr__(self) -> str:
        return f"<ServiceCommission(service_id={self.service_id}, rate={self.rate}, status={self.status})>"

    def to_dict(self, include_deleted: bool = False) -> dict:
        data = super().to_dict(include_deleted=include_deleted)
        data.update({
            "service_id": str(self.service_id) if self.service_id else None,
            "rate": float(self.rate) if self.rate is not None else None,
            "status": self.status,
        })
        return data
