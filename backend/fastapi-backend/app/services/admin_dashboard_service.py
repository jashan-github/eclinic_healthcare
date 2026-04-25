"""
Admin Dashboard Service
Clinic overview stats, revenue graph, recent activity, and active appointments.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract, or_, and_

from app.models.webinar import Webinar
from app.models.appointment import Appointment
from app.models.appointment_payment import AppointmentPayment
from app.models.appointment_request import AppointmentRequest
from app.models.audit import AuditLog
from app.models.user import User


class AdminDashboardService:
    """Service for admin dashboard: stats, revenue graph, recent activity, active appointments."""

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> Dict[str, Any]:
        """
        Clinic overview: total_revenue, total_referrals, total_commissions, total_webinars_this_month.
        Referrals: no referral model yet; returns 0.
        """
        total_revenue = self._total_revenue()
        total_referrals = self._total_referrals()  # 0 if no referral model
        total_commissions = self._total_commissions_all_time()
        total_webinars_this_month = self._count_webinars_this_month()
        return {
            "total_revenue": round(float(total_revenue), 2),
            "total_referrals": total_referrals,
            "total_commissions": round(float(total_commissions), 2),
            "total_webinars_this_month": total_webinars_this_month,
            "currency": "XCD",
        }

    def get_revenue_graph(self, months: int = 6) -> List[Dict[str, Any]]:
        """Monthly revenue for last N months (single series: total = appointment + webinar)."""
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=months * 31)).replace(tzinfo=timezone.utc)
        end = now.replace(tzinfo=timezone.utc)
        month_list = []
        for i in range(months - 1, -1, -1):
            d = now - timedelta(days=30 * i)
            month_list.append((d.year, d.month))

        # Appointment revenue per month
        appt_rev = (
            self.db.query(
                extract("year", AppointmentPayment.created_at).label("year"),
                extract("month", AppointmentPayment.created_at).label("month"),
                func.coalesce(func.sum(AppointmentPayment.amount), 0).label("revenue"),
            )
            .filter(
                AppointmentPayment.status == "COMPLETED",
                AppointmentPayment.created_at >= start,
                AppointmentPayment.created_at <= end,
            )
            .group_by(
                extract("year", AppointmentPayment.created_at),
                extract("month", AppointmentPayment.created_at),
            )
        )
        appt_map = {(int(r.year), int(r.month)): float(r.revenue) for r in appt_rev.all()}

        # Webinar revenue per month
        from app.models.webinar_payment import WebinarPayment

        web_rev = (
            self.db.query(
                extract("year", WebinarPayment.created_at).label("year"),
                extract("month", WebinarPayment.created_at).label("month"),
                func.coalesce(func.sum(WebinarPayment.amount), 0).label("revenue"),
            )
            .filter(
                WebinarPayment.status == "COMPLETED",
                WebinarPayment.created_at >= start,
                WebinarPayment.created_at <= end,
            )
            .group_by(
                extract("year", WebinarPayment.created_at),
                extract("month", WebinarPayment.created_at),
            )
        )
        web_map = {(int(r.year), int(r.month)): float(r.revenue) for r in web_rev.all()}

        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        out = []
        for y, m in month_list:
            key = (y, m)
            total = appt_map.get(key, 0.0) + web_map.get(key, 0.0)
            out.append({
                "year": y,
                "month": m,
                "month_label": month_names[m - 1],
                "revenue": round(total, 2),
            })
        return out

    def get_recent_activity(
        self,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Latest audit log entries with actor name and action.
        status: optional filter "all" | "confirmed" | "pending" | "cancelled" (filters by entity_type/action when applicable).
        """
        query = (
            self.db.query(AuditLog)
            .options(joinedload(AuditLog.actor))
            .order_by(AuditLog.created_at.desc())
            .limit(min(limit, 100))
        )
        if status and status.lower() != "all":
            # Optional: filter by entity_type or action (e.g. confirmed/pending/cancelled)
            if status.lower() in ("confirmed", "pending", "cancelled"):
                query = query.filter(
                    or_(
                        AuditLog.entity_type == "appointment_request",
                        AuditLog.action.ilike(f"%{status}%"),
                    )
                )
        rows = query.all()
        out = []
        for r in rows:
            name = (r.actor.name if r.actor else None) or "Unknown"
            initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
            action_label = r.action.replace("_", " ").title() if r.action else ""
            out.append({
                "id": str(r.id),
                "user_initials": initials[:2],
                "user_name": name,
                "action": action_label,
                "entity_type": r.entity_type,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "time_ago": _time_ago(r.created_at) if r.created_at else None,
            })
        return out

    def get_active_appointments(
        self,
        page: int = 1,
        per_page: int = 20,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Appointments that are not COMPLETED, CANCELLED, or NO_SHOW.
        Only today and future appointments (appointment_date >= today).
        Returns paginated list with total, page, per_page, total_pages.
        status_filter: optional "all" | "scheduled" | "confirmed" | "in_progress".
        """
        today = datetime.now(timezone.utc).date()
        active_statuses = ["SCHEDULED", "CONFIRMED", "IN_PROGRESS"]
        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        base_query = (
            self.db.query(Appointment)
            .options(
                joinedload(Appointment.doctor),
                joinedload(Appointment.patient),
                joinedload(Appointment.service),
            )
            .filter(
                Appointment.deleted_at.is_(None),
                Appointment.status.in_(active_statuses),
                Appointment.appointment_date >= today,
            )
        )
        if status_filter and status_filter.lower() != "all":
            status_upper = status_filter.upper().replace(" ", "_")
            if status_upper in active_statuses:
                base_query = base_query.filter(Appointment.status == status_upper)

        total = base_query.count()
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        offset = (page - 1) * per_page
        rows = (
            base_query
            .order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc())
            .offset(offset)
            .limit(per_page)
            .all()
        )
        # Map (doctor_id, patient_id, service_id, appointment_date, start_time) -> payment id (invoice id)
        payment_map = {}
        if rows:
            payment_query = (
                self.db.query(AppointmentPayment)
                .options(joinedload(AppointmentPayment.appointment_request))
                .join(AppointmentRequest, AppointmentPayment.appointment_request_id == AppointmentRequest.id)
                .filter(AppointmentPayment.status == "COMPLETED")
                .filter(
                    or_(
                        *[
                            and_(
                                AppointmentRequest.doctor_id == a.doctor_id,
                                AppointmentRequest.patient_id == a.patient_id,
                                AppointmentRequest.service_id == a.service_id,
                                AppointmentRequest.preferred_date == a.appointment_date,
                                AppointmentRequest.preferred_time == a.start_time,
                            )
                            for a in rows
                        ]
                    )
                )
            )
            for pay in payment_query.all():
                req = pay.appointment_request
                if req:
                    key = (req.doctor_id, req.patient_id, req.service_id, req.preferred_date, req.preferred_time)
                    payment_map[key] = str(pay.id)
        out = []
        for a in rows:
            doctor_name = a.doctor.name if a.doctor else ""
            patient_name = a.patient.name if a.patient else ""
            service_name = a.service.name if a.service else ""
            key = (a.doctor_id, a.patient_id, a.service_id, a.appointment_date, a.start_time)
            invoice_id = payment_map.get(key)
            out.append({
                "id": str(a.id),
                "doctor_name": doctor_name,
                "patient_name": patient_name,
                "service_name": service_name,
                "appointment_date": a.appointment_date.isoformat() if a.appointment_date else None,
                "start_time": a.start_time.isoformat()[:5] if a.start_time else None,
                "end_time": a.end_time.isoformat()[:5] if a.end_time else None,
                "status": a.status,
                "price_amount": float(a.price_amount) if a.price_amount is not None else None,
                "currency": "XCG",
                "invoice_id": invoice_id,
            })
        return {
            "data": out,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

    def _total_revenue(self) -> Decimal:
        """Sum of completed appointment + webinar payments."""
        appt_rev = (
            self.db.query(func.coalesce(func.sum(AppointmentPayment.amount), 0))
            .filter(AppointmentPayment.status == "COMPLETED")
            .scalar()
        )
        from app.models.webinar_payment import WebinarPayment

        web_rev = (
            self.db.query(func.coalesce(func.sum(WebinarPayment.amount), 0))
            .filter(WebinarPayment.status == "COMPLETED")
            .scalar()
        )
        total = (Decimal(str(appt_rev)) if appt_rev is not None else Decimal("0")) + (
            Decimal(str(web_rev)) if web_rev is not None else Decimal("0")
        )
        return total

    def _total_referrals(self) -> int:
        """Placeholder: no referral model yet."""
        return 0

    def _total_commissions_all_time(self) -> Decimal:
        """Sum of commission_earned on all COMPLETED appointment payments."""
        result = (
            self.db.query(func.coalesce(func.sum(AppointmentPayment.commission_earned), 0))
            .filter(AppointmentPayment.status == "COMPLETED")
            .scalar()
        )
        return Decimal(str(result)) if result is not None else Decimal("0")

    def _count_webinars_this_month(self) -> int:
        """Count webinars (by webinar_date) in the current month."""
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        if now.month == 12:
            end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
        end = end.date() if hasattr(end, "date") else end
        result = (
            self.db.query(func.count(Webinar.id))
            .filter(
                Webinar.deleted_at.is_(None),
                Webinar.webinar_date >= start,
                Webinar.webinar_date <= end,
            )
            .scalar()
        )
        return result or 0


def _time_ago(dt: datetime) -> str:
    """Human-readable time ago (e.g. '2 hours ago')."""
    if not dt:
        return ""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    secs = int(delta.total_seconds())
    if secs >= 3600:
        h = secs // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    if secs >= 60:
        m = secs // 60
        return f"{m} minute{'s' if m != 1 else ''} ago"
    return "Just now"
