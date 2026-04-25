"""
Admin Analytics / Report Service
Aggregates data for the admin Advanced Analytics dashboard: summary cards and revenue analysis.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.webinar import Webinar
from app.models.appointment import Appointment
from app.models.appointment_payment import AppointmentPayment
from app.models.webinar_payment import WebinarPayment


class AdminAnalyticsService:
    """Service for admin analytics and report aggregation."""

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary stats for admin dashboard cards: total_webinars, total_appointments, revenue, active_patients.
        """
        return {
            "total_webinars": self._count_webinars(),
            "total_appointments": self._count_appointments(),
            "revenue": round(float(self._total_revenue()), 2),
            "active_patients": self._count_active_patients(),
            "currency": "XCD",
        }

    def get_revenue_graph(
        self,
        year: int | None = None,
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Get monthly revenue data for the graph: primary (appointment) and secondary (webinar) revenue by month.
        """
        return self._monthly_revenue_analysis(year=year, months=months)

    def get_appointment_volume_graph(
        self,
        year: int | None = None,
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Get monthly appointment volume for the graph: total_appointments and amount_collected by month.
        """
        return self._monthly_appointment_volume(year=year, months=months)

    def get_webinar_volume_graph(
        self,
        year: int | None = None,
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Get monthly webinar volume for the graph: total_webinars and amount_collected by month.
        """
        return self._monthly_webinar_volume(year=year, months=months)

    def _count_webinars(self) -> int:
        """Count non-deleted webinars."""
        result = (
            self.db.query(func.count(Webinar.id))
            .filter(Webinar.deleted_at.is_(None))
            .scalar()
        )
        return result or 0

    def _count_appointments(self) -> int:
        """Count all non-deleted appointments."""
        result = (
            self.db.query(func.count(Appointment.id))
            .filter(Appointment.deleted_at.is_(None))
            .scalar()
        )
        return result or 0

    def _total_revenue(self) -> Decimal:
        """Sum of completed appointment payments + completed webinar payments."""
        appt_rev = (
            self.db.query(func.coalesce(func.sum(AppointmentPayment.amount), 0))
            .filter(AppointmentPayment.status == "COMPLETED")
            .scalar()
        )
        web_rev = (
            self.db.query(func.coalesce(func.sum(WebinarPayment.amount), 0))
            .filter(WebinarPayment.status == "COMPLETED")
            .scalar()
        )
        total = (Decimal(str(appt_rev)) if appt_rev is not None else Decimal("0")) + (
            Decimal(str(web_rev)) if web_rev is not None else Decimal("0")
        )
        return total

    def _count_active_patients(self) -> int:
        """Count distinct patients with at least one non-deleted appointment."""
        result = (
            self.db.query(func.count(func.distinct(Appointment.patient_id)))
            .filter(Appointment.deleted_at.is_(None))
            .scalar()
        )
        return result or 0

    def _monthly_revenue_analysis(
        self,
        year: int | None = None,
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """Last N months: for each month, primary_revenue (appointments) and secondary_revenue (webinars)."""
        now = datetime.now(timezone.utc)
        if year is not None:
            start = datetime(year, 1, 1, tzinfo=timezone.utc)
            end = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            # Build list of months in the year
            month_list = [(year, m) for m in range(1, 13)]
        else:
            start = now - timedelta(days=months * 31)
            end = now
            month_list = []
            for i in range(months - 1, -1, -1):
                d = now - timedelta(days=30 * i)
                month_list.append((d.year, d.month))

        start_date = start.replace(tzinfo=timezone.utc) if start.tzinfo else start
        end_date = end.replace(tzinfo=timezone.utc) if end.tzinfo else end

        # Appointment revenue per month (by payment created_at)
        appt_rev = (
            self.db.query(
                extract("year", AppointmentPayment.created_at).label("year"),
                extract("month", AppointmentPayment.created_at).label("month"),
                func.coalesce(func.sum(AppointmentPayment.amount), 0).label("revenue"),
            )
            .filter(
                AppointmentPayment.status == "COMPLETED",
                AppointmentPayment.created_at >= start_date,
                AppointmentPayment.created_at <= end_date,
            )
            .group_by(
                extract("year", AppointmentPayment.created_at),
                extract("month", AppointmentPayment.created_at),
            )
        )
        appt_map = {
            (int(r.year), int(r.month)): float(r.revenue) for r in appt_rev.all()
        }

        # Webinar revenue per month (by payment created_at)
        web_rev = (
            self.db.query(
                extract("year", WebinarPayment.created_at).label("year"),
                extract("month", WebinarPayment.created_at).label("month"),
                func.coalesce(func.sum(WebinarPayment.amount), 0).label("revenue"),
            )
            .filter(
                WebinarPayment.status == "COMPLETED",
                WebinarPayment.created_at >= start_date,
                WebinarPayment.created_at <= end_date,
            )
            .group_by(
                extract("year", WebinarPayment.created_at),
                extract("month", WebinarPayment.created_at),
            )
        )
        web_map = {
            (int(r.year), int(r.month)): float(r.revenue) for r in web_rev.all()
        }

        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        out = []
        for y, m in month_list:
            key = (y, m)
            out.append({
                "year": y,
                "month": m,
                "month_label": month_names[m - 1],
                "primary_revenue": round(appt_map.get(key, 0.0), 2),
                "secondary_revenue": round(web_map.get(key, 0.0), 2),
            })
        return out

    def _monthly_appointment_volume(
        self,
        year: int | None = None,
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """Per month: total_appointments (all non-deleted) and amount_collected (completed appointment payments), by appointment_date / payment month."""
        now = datetime.now(timezone.utc)
        if year is not None:
            start_date = now.replace(year=year, month=1, day=1).date()
            end_date = now.replace(year=year, month=12, day=31).date()
            start_dt = now.replace(year=year, month=1, day=1, tzinfo=timezone.utc)
            end_dt = now.replace(year=year, month=12, day=31, hour=23, minute=59, second=59, tzinfo=timezone.utc)
            month_list = [(year, m) for m in range(1, 13)]
        else:
            start_date = (now - timedelta(days=months * 31)).date()
            end_date = now.date()
            start_dt = (now - timedelta(days=months * 31)).replace(tzinfo=timezone.utc)
            end_dt = now.replace(tzinfo=timezone.utc)
            month_list = []
            for i in range(months - 1, -1, -1):
                d = now - timedelta(days=30 * i)
                month_list.append((d.year, d.month))

        # Total appointments per month (by appointment_date, non-deleted)
        total_q = (
            self.db.query(
                extract("year", Appointment.appointment_date).label("year"),
                extract("month", Appointment.appointment_date).label("month"),
                func.count(Appointment.id).label("total"),
            )
            .filter(
                Appointment.deleted_at.is_(None),
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
            )
            .group_by(
                extract("year", Appointment.appointment_date),
                extract("month", Appointment.appointment_date),
            )
        )
        total_map = {(int(r.year), int(r.month)): r.total for r in total_q.all()}

        # Amount collected per month (completed appointment payments, by payment created_at)
        amount_q = (
            self.db.query(
                extract("year", AppointmentPayment.created_at).label("year"),
                extract("month", AppointmentPayment.created_at).label("month"),
                func.coalesce(func.sum(AppointmentPayment.amount), 0).label("amount"),
            )
            .filter(
                AppointmentPayment.status == "COMPLETED",
                AppointmentPayment.created_at >= start_dt,
                AppointmentPayment.created_at <= end_dt,
            )
            .group_by(
                extract("year", AppointmentPayment.created_at),
                extract("month", AppointmentPayment.created_at),
            )
        )
        amount_map = {(int(r.year), int(r.month)): float(r.amount) for r in amount_q.all()}

        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        out = []
        for y, m in month_list:
            key = (y, m)
            out.append({
                "year": y,
                "month": m,
                "month_label": month_names[m - 1],
                "total_appointments": total_map.get(key, 0),
                "amount_collected": round(amount_map.get(key, 0.0), 2),
            })
        return out

    def _monthly_webinar_volume(
        self,
        year: int | None = None,
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """Per month: total_webinars (non-deleted by webinar_date) and amount_collected (completed webinar payments), by webinar_date / payment month."""
        now = datetime.now(timezone.utc)
        if year is not None:
            start_date = now.replace(year=year, month=1, day=1).date()
            end_date = now.replace(year=year, month=12, day=31).date()
            start_dt = now.replace(year=year, month=1, day=1, tzinfo=timezone.utc)
            end_dt = now.replace(year=year, month=12, day=31, hour=23, minute=59, second=59, tzinfo=timezone.utc)
            month_list = [(year, m) for m in range(1, 13)]
        else:
            start_date = (now - timedelta(days=months * 31)).date()
            end_date = now.date()
            start_dt = (now - timedelta(days=months * 31)).replace(tzinfo=timezone.utc)
            end_dt = now.replace(tzinfo=timezone.utc)
            month_list = []
            for i in range(months - 1, -1, -1):
                d = now - timedelta(days=30 * i)
                month_list.append((d.year, d.month))

        # Total webinars per month (by webinar_date, non-deleted)
        total_q = (
            self.db.query(
                extract("year", Webinar.webinar_date).label("year"),
                extract("month", Webinar.webinar_date).label("month"),
                func.count(Webinar.id).label("total"),
            )
            .filter(
                Webinar.deleted_at.is_(None),
                Webinar.webinar_date >= start_date,
                Webinar.webinar_date <= end_date,
            )
            .group_by(
                extract("year", Webinar.webinar_date),
                extract("month", Webinar.webinar_date),
            )
        )
        total_map = {(int(r.year), int(r.month)): r.total for r in total_q.all()}

        # Amount collected per month (completed webinar payments, by payment created_at)
        amount_q = (
            self.db.query(
                extract("year", WebinarPayment.created_at).label("year"),
                extract("month", WebinarPayment.created_at).label("month"),
                func.coalesce(func.sum(WebinarPayment.amount), 0).label("amount"),
            )
            .filter(
                WebinarPayment.status == "COMPLETED",
                WebinarPayment.created_at >= start_dt,
                WebinarPayment.created_at <= end_dt,
            )
            .group_by(
                extract("year", WebinarPayment.created_at),
                extract("month", WebinarPayment.created_at),
            )
        )
        amount_map = {(int(r.year), int(r.month)): float(r.amount) for r in amount_q.all()}

        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        out = []
        for y, m in month_list:
            key = (y, m)
            out.append({
                "year": y,
                "month": m,
                "month_label": month_names[m - 1],
                "total_webinars": total_map.get(key, 0),
                "amount_collected": round(amount_map.get(key, 0.0), 2),
            })
        return out
