"""
Service commission service.
Admin create/update commission per service (rate 1-100, status ACTIVE/INACTIVE).
Commission earned: stored on payment when COMPLETED (only upcoming: rate changes do not affect past payments).
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.appointment_payment import AppointmentPayment
from app.models.appointment_request import AppointmentRequest
from app.models.service import Service
from app.models.service_commission import ServiceCommission
from app.models.user import User
from app.services.service_catalog_service import ServiceCatalogService
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.core.security import UserRole


def set_payment_commission(db: Session, payment: AppointmentPayment) -> None:
    """
    Set commission_rate and commission_earned on a payment (call when payment is marked COMPLETED).
    Uses current ACTIVE ServiceCommission for the request's service; if none, sets commission_earned=0.
    Only upcoming: changing the rate later does not affect this stored value.
    """
    request = (
        db.query(AppointmentRequest)
        .filter(AppointmentRequest.id == payment.appointment_request_id)
        .first()
    )
    if not request:
        return
    commission = (
        db.query(ServiceCommission)
        .filter(
            ServiceCommission.service_id == request.service_id,
            ServiceCommission.status == "ACTIVE",
            ServiceCommission.deleted_at.is_(None),
        )
        .first()
    )
    if commission:
        payment.commission_rate = commission.rate
        payment.commission_earned = (payment.amount or Decimal("0")) * (commission.rate / 100)
    else:
        payment.commission_rate = None
        payment.commission_earned = Decimal("0")


class ServiceCommissionService:
    """Admin-only: create/update commission per service."""

    def __init__(self, db: Session):
        self.db = db
        self._catalog = ServiceCatalogService(db)

    def _ensure_service_access(self, user: User, service_id: UUID) -> Service:
        """Ensure service exists and user has clinic access. Returns Service."""
        return self._catalog.get_service_by_id(user=user, service_id=service_id)

    def get_by_service_id(self, user: User, service_id: UUID) -> Optional[ServiceCommission]:
        """Get commission for a service (admin). Returns None if not set."""
        self._ensure_service_access(user, service_id)
        return (
            self.db.query(ServiceCommission)
            .filter(
                ServiceCommission.service_id == service_id,
                ServiceCommission.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_clinic(
        self,
        user: User,
        clinic_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> List[ServiceCommission]:
        """List commissions for services in clinics the admin can access."""
        query = (
            self.db.query(ServiceCommission)
            .join(Service, ServiceCommission.service_id == Service.id)
            .filter(
                ServiceCommission.deleted_at.is_(None),
                Service.deleted_at.is_(None),
            )
        )
        if user.role != UserRole.SUPER_ADMIN.value:
            query = query.filter(Service.clinic_id == user.clinic_id)
        elif clinic_id:
            query = query.filter(Service.clinic_id == clinic_id)
        if status:
            query = query.filter(ServiceCommission.status == status)
        return query.order_by(Service.name).all()

    def get_commission_stats(
        self,
        user: User,
        clinic_id: Optional[UUID] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Stats for Commission Management dashboard:
        - total_commissions_this_month: sum of commission_earned for COMPLETED payments in the month
        - total_commission_rates: count of configured commission rates (service_commissions in scope)
        - average_commission: average commission rate (%) in scope
        """
        from sqlalchemy import func

        now = date.today()
        _year = year if year is not None else now.year
        _month = month if month is not None else now.month
        month_start = datetime(_year, _month, 1)
        if _month == 12:
            month_end = datetime(_year + 1, 1, 1) - timedelta(microseconds=1)
        else:
            month_end = datetime(_year, _month + 1, 1) - timedelta(microseconds=1)

        # Base query for payments in month (COMPLETED, join request for clinic)
        payment_query = (
            self.db.query(
                func.coalesce(func.sum(AppointmentPayment.commission_earned), 0).label("total"),
            )
            .join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
            )
            .filter(
                AppointmentPayment.status == "COMPLETED",
                AppointmentPayment.created_at >= month_start,
                AppointmentPayment.created_at <= month_end,
                AppointmentRequest.deleted_at.is_(None),
            )
        )
        if user.role != UserRole.SUPER_ADMIN.value:
            payment_query = payment_query.filter(AppointmentRequest.clinic_id == user.clinic_id)
        elif clinic_id:
            payment_query = payment_query.filter(AppointmentRequest.clinic_id == clinic_id)
        total_commissions_row = payment_query.first()
        total_commissions_this_month = float(total_commissions_row.total) if total_commissions_row and total_commissions_row.total is not None else 0.0

        # Count of commission rates (service_commissions in scope)
        rates_query = (
            self.db.query(func.count(ServiceCommission.id).label("cnt"))
            .join(Service, ServiceCommission.service_id == Service.id)
            .filter(
                ServiceCommission.deleted_at.is_(None),
                Service.deleted_at.is_(None),
            )
        )
        if user.role != UserRole.SUPER_ADMIN.value:
            rates_query = rates_query.filter(Service.clinic_id == user.clinic_id)
        elif clinic_id:
            rates_query = rates_query.filter(Service.clinic_id == clinic_id)
        rates_row = rates_query.first()
        total_commission_rates = int(rates_row.cnt) if rates_row and rates_row.cnt is not None else 0

        # Average commission rate (%)
        avg_query = (
            self.db.query(func.avg(ServiceCommission.rate).label("avg_rate"))
            .join(Service, ServiceCommission.service_id == Service.id)
            .filter(
                ServiceCommission.deleted_at.is_(None),
                Service.deleted_at.is_(None),
            )
        )
        if user.role != UserRole.SUPER_ADMIN.value:
            avg_query = avg_query.filter(Service.clinic_id == user.clinic_id)
        elif clinic_id:
            avg_query = avg_query.filter(Service.clinic_id == clinic_id)
        avg_row = avg_query.first()
        average_commission = round(float(avg_row.avg_rate), 2) if avg_row and avg_row.avg_rate is not None else 0.0

        return {
            "total_commissions_this_month": total_commissions_this_month,
            "total_commission_rates": total_commission_rates,
            "average_commission": average_commission,
            "month": _month,
            "year": _year,
        }

    def create_or_update(
        self,
        user: User,
        service_id: UUID,
        rate: Decimal,
        status: str,
    ) -> ServiceCommission:
        """
        Create or update commission for a service (upsert).
        rate must be between 1 and 100 (decimal allowed).
        status must be ACTIVE or INACTIVE.
        """
        if not (Decimal("1") <= rate <= Decimal("100")):
            raise ValidationException(
                message="Commission rate must be between 1 and 100",
                errors={"rate": ["Rate must be between 1 and 100 (decimal allowed)"]},
            )
        if status not in ("ACTIVE", "INACTIVE"):
            raise ValidationException(
                message="Status must be ACTIVE or INACTIVE",
                errors={"status": ["Status must be ACTIVE or INACTIVE"]},
            )
        self._ensure_service_access(user, service_id)

        # Existing non-deleted commission: update
        existing = (
            self.db.query(ServiceCommission)
            .filter(
                ServiceCommission.service_id == service_id,
                ServiceCommission.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            existing.rate = rate
            existing.status = status
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Soft-deleted commission for this service: restore and update (avoids unique constraint on service_id)
        deleted = (
            self.db.query(ServiceCommission)
            .filter(
                ServiceCommission.service_id == service_id,
                ServiceCommission.deleted_at.isnot(None),
            )
            .first()
        )
        if deleted:
            deleted.restore()
            deleted.rate = rate
            deleted.status = status
            self.db.commit()
            self.db.refresh(deleted)
            return deleted

        commission = ServiceCommission(
            service_id=service_id,
            rate=rate,
            status=status,
        )
        self.db.add(commission)
        self.db.commit()
        self.db.refresh(commission)
        return commission

    def delete(self, user: User, service_id: UUID) -> None:
        """Soft-delete commission for a service. Raises NotFoundException if no commission exists."""
        self._ensure_service_access(user, service_id)
        commission = (
            self.db.query(ServiceCommission)
            .filter(
                ServiceCommission.service_id == service_id,
                ServiceCommission.deleted_at.is_(None),
            )
            .first()
        )
        if not commission:
            raise NotFoundException(
                message="Commission not found for this service",
                errors={"service_id": ["No commission configured for this service"]},
            )
        commission.soft_delete()
        self.db.commit()

    def _query_completed_payments_with_commission(
        self,
        user: User,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        clinic_id: Optional[UUID] = None,
        service_id: Optional[UUID] = None,
    ):
        """Query COMPLETED payments joined with request and service. Uses stored commission_earned (only upcoming)."""
        q = (
            self.db.query(AppointmentPayment, AppointmentRequest, Service)
            .join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
            )
            .join(Service, AppointmentRequest.service_id == Service.id)
            .filter(
                AppointmentPayment.status == "COMPLETED",
                AppointmentRequest.deleted_at.is_(None),
                Service.deleted_at.is_(None),
            )
        )
        if user.role != UserRole.SUPER_ADMIN.value:
            q = q.filter(AppointmentRequest.clinic_id == user.clinic_id)
        elif clinic_id:
            q = q.filter(AppointmentRequest.clinic_id == clinic_id)
        if date_from:
            q = q.filter(AppointmentPayment.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            q = q.filter(AppointmentPayment.created_at < datetime.combine(date_to, datetime.min.time()) + timedelta(days=1))
        if service_id:
            q = q.filter(AppointmentRequest.service_id == service_id)
        q = q.options(joinedload(AppointmentRequest.doctor))
        return q.all()

    def get_commission_earned_by_service(
        self,
        user: User,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        clinic_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Commission earned grouped by service (from COMPLETED appointment payments).
        Only payments for services with ACTIVE commission are included in commission_earned;
        total_payment_amount includes all completed payments for that service.
        """
        rows = self._query_completed_payments_with_commission(
            user=user, date_from=date_from, date_to=date_to, clinic_id=clinic_id
        )
        by_service: Dict[UUID, Dict[str, Any]] = {}
        for payment, request, service in rows:
            sid = request.service_id
            amount = float(payment.amount)
            earned = payment.commission_earned if payment.commission_earned is not None else Decimal("0")
            rate = float(payment.commission_rate) if payment.commission_rate is not None else None
            if sid not in by_service:
                by_service[sid] = {
                    "service_id": sid,
                    "service_name": service.name,
                    "total_payment_amount": Decimal("0"),
                    "commission_earned": Decimal("0"),
                    "payment_count": 0,
                }
            by_service[sid]["total_payment_amount"] += Decimal(str(amount))
            by_service[sid]["commission_earned"] += earned
            by_service[sid]["payment_count"] += 1
            if rate is not None and by_service[sid].get("commission_rate") is None:
                by_service[sid]["commission_rate"] = rate
        result = []
        for sid, data in by_service.items():
            result.append({
                "service_id": str(data["service_id"]),
                "service_name": data["service_name"],
                "total_payment_amount": float(data["total_payment_amount"]),
                "commission_rate": data.get("commission_rate"),
                "commission_earned": float(data["commission_earned"]),
                "payment_count": data["payment_count"],
            })
        return sorted(result, key=lambda x: (-x["commission_earned"], x["service_name"]))

    def get_commission_earned_by_doctor(
        self,
        user: User,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        clinic_id: Optional[UUID] = None,
        service_id: Optional[UUID] = None,
        include_service_breakdown: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Commission earned grouped by doctor (from COMPLETED appointment payments).
        Optionally include per-service breakdown for each doctor.
        """
        rows = self._query_completed_payments_with_commission(
            user=user,
            date_from=date_from,
            date_to=date_to,
            clinic_id=clinic_id,
            service_id=service_id,
        )
        by_doctor: Dict[UUID, Dict[str, Any]] = {}
        for payment, request, service in rows:
            did = request.doctor_id
            amount = float(payment.amount)
            earned = payment.commission_earned if payment.commission_earned is not None else Decimal("0")
            doctor_name = getattr(request.doctor, "name", None) if hasattr(request, "doctor") else None
            if did not in by_doctor:
                by_doctor[did] = {
                    "doctor_id": did,
                    "doctor_name": doctor_name,
                    "total_payment_amount": Decimal("0"),
                    "commission_earned": Decimal("0"),
                    "payment_count": 0,
                    "by_service": {} if include_service_breakdown else None,
                }
            by_doctor[did]["total_payment_amount"] += Decimal(str(amount))
            by_doctor[did]["commission_earned"] += earned
            by_doctor[did]["payment_count"] += 1
            if doctor_name is None and hasattr(request, "doctor"):
                by_doctor[did]["doctor_name"] = getattr(request.doctor, "name", "—")
            if include_service_breakdown:
                sid = request.service_id
                sname = service.name
                if sid not in by_doctor[did]["by_service"]:
                    by_doctor[did]["by_service"][sid] = {
                        "service_id": str(sid),
                        "service_name": sname,
                        "total_payment_amount": Decimal("0"),
                        "commission_earned": Decimal("0"),
                        "payment_count": 0,
                    }
                by_doctor[did]["by_service"][sid]["total_payment_amount"] += Decimal(str(amount))
                by_doctor[did]["by_service"][sid]["commission_earned"] += earned
                by_doctor[did]["by_service"][sid]["payment_count"] += 1
        result = []
        for did, data in by_doctor.items():
            item = {
                "doctor_id": str(data["doctor_id"]),
                "doctor_name": data["doctor_name"] or "—",
                "total_payment_amount": float(data["total_payment_amount"]),
                "commission_earned": float(data["commission_earned"]),
                "payment_count": data["payment_count"],
            }
            if include_service_breakdown and data["by_service"]:
                item["by_service"] = [
                    {
                        "service_id": v["service_id"],
                        "service_name": v["service_name"],
                        "total_payment_amount": float(v["total_payment_amount"]),
                        "commission_earned": float(v["commission_earned"]),
                        "payment_count": v["payment_count"],
                    }
                    for v in data["by_service"].values()
                ]
                item["by_service"].sort(key=lambda x: (-x["commission_earned"], x["service_name"]))
            result.append(item)
        result.sort(key=lambda x: (-x["commission_earned"], x["doctor_name"]))
        return result
