"""
Doctor Analytics / Report Service
Aggregates data for the doctor analytics dashboard (summary, monthly trends, payment breakdown).
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from app.models.appointment import Appointment
from app.models.appointment_request import AppointmentRequest
from app.models.appointment_payment import AppointmentPayment
from app.models.soap_note import SoapNote


class DoctorAnalyticsService:
    """Service for doctor analytics and report aggregation."""

    def __init__(self, db: Session):
        self.db = db

    def get_report(self, doctor_id: UUID) -> Dict[str, Any]:
        """
        Get full analytics report for a doctor: summary cards, monthly performance, top medical metrics, payment breakdown.
        """
        # Summary
        total_patients = self._count_distinct_patients(doctor_id)
        total_appointments = self._count_appointments(doctor_id)
        revenue = self._total_revenue(doctor_id)
        total_waiver = self._total_waiver(doctor_id)

        # Monthly performance (last 12 months): appointments count and revenue per month
        monthly_performance = self._monthly_performance(doctor_id, months=12)

        # Top medical metrics from SOAP notes (optional; returns null if no structured extraction)
        top_metrics = self._top_medical_metrics(doctor_id)

        # Payment breakdown (current system: all completed payments are online; cash = 0)
        payment_breakdown = self._payment_breakdown(doctor_id)

        return {
            "summary": {
                "total_patients": total_patients,
                "total_appointments": total_appointments,
                "revenue": round(float(revenue), 2),
                "total_waiver": total_waiver,
                "currency": "USD",
            },
            "monthly_performance": monthly_performance,
            "top_medical_metrics": top_metrics,
            "payment_breakdown": payment_breakdown,
        }

    def _count_distinct_patients(self, doctor_id: UUID) -> int:
        """Count distinct patients who have at least one appointment with this doctor."""
        result = (
            self.db.query(func.count(func.distinct(Appointment.patient_id)))
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.deleted_at.is_(None),
            )
            .scalar()
        )
        return result or 0

    def _count_appointments(self, doctor_id: UUID) -> int:
        """Count all appointments for this doctor (any non-deleted)."""
        result = (
            self.db.query(func.count(Appointment.id))
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.deleted_at.is_(None),
            )
            .scalar()
        )
        return result or 0

    def _total_revenue(self, doctor_id: UUID) -> Decimal:
        """Sum of completed payment amounts for this doctor."""
        result = (
            self.db.query(func.coalesce(func.sum(AppointmentPayment.amount), 0))
            .join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
            )
            .filter(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentPayment.status == "COMPLETED",
            )
            .scalar()
        )
        return Decimal(str(result)) if result is not None else Decimal("0")

    def _total_waiver(self, doctor_id: UUID) -> int:
        """Placeholder: waiver count (e.g. free appointments). No waiver model yet; return 0."""
        return 0

    def _monthly_performance(
        self, doctor_id: UUID, months: int = 12
    ) -> List[Dict[str, Any]]:
        """Last N months: for each month, appointment count and revenue."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=months * 31)
        start_date = start.date()

        # Appointments per month (by appointment_date)
        appt_subq = (
            self.db.query(
                extract("year", Appointment.appointment_date).label("year"),
                extract("month", Appointment.appointment_date).label("month"),
                func.count(Appointment.id).label("appointments"),
            )
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.deleted_at.is_(None),
                Appointment.appointment_date >= start_date,
            )
            .group_by(
                extract("year", Appointment.appointment_date),
                extract("month", Appointment.appointment_date),
            )
        )
        appt_rows = appt_subq.all()

        # Revenue per month (by payment created_at)
        rev_subq = (
            self.db.query(
                extract("year", AppointmentPayment.created_at).label("year"),
                extract("month", AppointmentPayment.created_at).label("month"),
                func.coalesce(func.sum(AppointmentPayment.amount), 0).label("revenue"),
            )
            .join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
            )
            .filter(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentPayment.status == "COMPLETED",
                AppointmentPayment.created_at >= start,
            )
            .group_by(
                extract("year", AppointmentPayment.created_at),
                extract("month", AppointmentPayment.created_at),
            )
        )
        rev_rows = rev_subq.all()

        # Build lookup: (year, month) -> appointments, revenue
        appt_map = {(int(r.year), int(r.month)): r.appointments for r in appt_rows}
        rev_map = {
            (int(r.year), int(r.month)): float(r.revenue) for r in rev_rows
        }

        # Last N calendar months (ordered Jan ... Dec / by date)
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        out = []
        for i in range(months - 1, -1, -1):
            d = now - timedelta(days=30 * i)
            y, m = d.year, d.month
            key = (y, m)
            out.append({
                "year": y,
                "month": m,
                "month_label": month_names[m - 1],
                "appointments": appt_map.get(key, 0),
                "revenue": round(rev_map.get(key, 0.0), 2),
            })
        return out

    def _top_medical_metrics(self, doctor_id: UUID) -> Dict[str, Optional[str]]:
        """
        Top symptom, diagnosis, lab test, drug from SOAP notes.
        Uses simple heuristics (first line or most common token) when notes exist; otherwise null.
        """
        notes = (
            self.db.query(SoapNote)
            .filter(SoapNote.doctor_id == doctor_id)
            .all()
        )
        if not notes:
            return {
                "top_symptom": None,
                "top_diagnosis": None,
                "top_lab_test": None,
                "top_drug": None,
            }

        symptoms: List[str] = []
        diagnoses: List[str] = []
        lab_tests: List[str] = []
        drugs: List[str] = []

        for n in notes:
            if n.subjective:
                first = n.subjective.strip().split("\n")[0].strip() or n.subjective.strip().split(",")[0].strip()
                if first:
                    symptoms.append(first)
            if n.assessment:
                first = n.assessment.strip().split("\n")[0].strip() or n.assessment.strip().split(",")[0].strip()
                if first:
                    diagnoses.append(first)
            if n.objective:
                first = n.objective.strip().split("\n")[0].strip() or n.objective.strip().split(",")[0].strip()
                if first:
                    lab_tests.append(first)
            if n.plan:
                first = n.plan.strip().split("\n")[0].strip() or n.plan.strip().split(",")[0].strip()
                if first:
                    drugs.append(first)

        def most_common(lst: List[str]) -> Optional[str]:
            if not lst:
                return None
            from collections import Counter
            return Counter(lst).most_common(1)[0][0]

        return {
            "top_symptom": most_common(symptoms),
            "top_diagnosis": most_common(diagnoses),
            "top_lab_test": most_common(lab_tests),
            "top_drug": most_common(drugs),
        }

    def _payment_breakdown(self, doctor_id: UUID) -> Dict[str, Any]:
        """Total payment, cash payment, online payment. Current system: all completed are online."""
        total = (
            self.db.query(func.coalesce(func.sum(AppointmentPayment.amount), 0))
            .join(
                AppointmentRequest,
                AppointmentPayment.appointment_request_id == AppointmentRequest.id,
            )
            .filter(
                AppointmentRequest.doctor_id == doctor_id,
                AppointmentPayment.status == "COMPLETED",
            )
            .scalar()
        )
        total_val = float(total) if total is not None else 0.0
        return {
            "total_payment": round(total_val, 2),
            "total_cash_payment": 0.0,
            "total_online_payment": round(total_val, 2),
            "currency": "USD",
        }
