"""
API v1 router
Aggregates all v1 endpoints
"""

from fastapi import APIRouter

# Import routers here as they are created
# from app.api.v1.endpoints import auth, patients, appointments, etc.

api_router = APIRouter()


# Health check endpoint (non-authenticated)
@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    """
    return {
        "status": "healthy",
        "service": "eclinic-backend",
        "version": "1.0.0"
    }


@api_router.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    """
    return {
        "message": "eClinic Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include routers
from app.api.v1.endpoints import (
    auth,
    users,
    notifications,
    notification_settings,
    push,
    profile,
    role_permissions,
    admin_analytics,
    admin_dashboard,
    service_commissions,
    availability,
    locations,
    languages,
    services,
    doctor_services,
    doctor_service_availability,
    doctor_service_pricing,
    doctor_service_availability_pricing,
    doctor_patients,
    doctor_appointments,
    doctor_payments,
    doctor_analytics,
    medical_services,
    admin_medical_services,
    patient_doctors,
    appointment_booking,
    appointment_requests,
    payments,
    clinics,
    clinic_locations,
    patient_documents,
    doctor_documents,
    patient_dashboard,
    vital_names,
    patient_vital_signs,
    vital_frequency,
    rx_templates,
    doctors,
    admin_settings,
    waiver_settings,
    soap_notes,
    staff_dashboard,
    emails,
    hipaa_release_forms,
    webinar_payments,
)

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(notifications.router, tags=["Admin - Notifications"])
api_router.include_router(push.router)
api_router.include_router(services.router, tags=["Admin - Services"])
api_router.include_router(doctor_services.router, tags=["Doctor - Services"])
api_router.include_router(doctor_service_availability.router, tags=["Doctor - Availability Services"])
api_router.include_router(doctor_service_pricing.router, tags=["Doctor - Service Pricing"])
api_router.include_router(doctor_service_availability_pricing.router, tags=["Doctor - Availability Pricing"])
api_router.include_router(doctor_patients.router, tags=["Doctor - Patients"])
api_router.include_router(doctor_appointments.router, tags=["Doctor - Appointments"])
api_router.include_router(doctor_payments.router, tags=["Doctor - Payments"])
api_router.include_router(doctor_analytics.router, tags=["Doctor - Analytics"])
api_router.include_router(profile.router, tags=["Profile"])
api_router.include_router(availability.router, tags=["Doctor Availability"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(languages.router, prefix="/languages", tags=["Languages"])
api_router.include_router(medical_services.router, prefix="/medical-services", tags=["Medical Services"])
api_router.include_router(admin_medical_services.router)
api_router.include_router(clinics.router, prefix="/clinics", tags=["Clinics"])
api_router.include_router(clinic_locations.router, tags=["Admin - Clinic Locations"])
# Webinar CRUD, go-live, join → call webinar service directly (no proxy in fastapi-backend)
api_router.include_router(webinar_payments.router, prefix="/patient/webinars", tags=["Patient - Webinar Payments"])
api_router.include_router(patient_documents.router, tags=["Patient - Documents"])
api_router.include_router(doctor_documents.router, tags=["Doctor - Documents"])
api_router.include_router(hipaa_release_forms.router)
api_router.include_router(patient_dashboard.router, tags=["Patient - Dashboard"])
api_router.include_router(patient_doctors.router, prefix="/patient/doctors", tags=["Patient - Doctor Search"])
api_router.include_router(appointment_booking.router, prefix="/patient", tags=["Patient - Appointment Booking"])
api_router.include_router(appointment_requests.router, prefix="/appointment", tags=["Appointment Requests"])
# Include notifications routers separately to ensure proper tag registration
api_router.include_router(appointment_requests.notifications_router, prefix="/appointment")
api_router.include_router(appointment_requests.patient_notifications_router, prefix="/appointment")
api_router.include_router(appointment_requests.visit_router)
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(vital_names.router)
api_router.include_router(patient_vital_signs.router)
api_router.include_router(vital_frequency.router)
api_router.include_router(rx_templates.router, tags=["Doctor - RX Templates"])
api_router.include_router(doctors.router, tags=["Admin - Doctors"])
api_router.include_router(admin_settings.router, tags=["Admin - Settings"])
api_router.include_router(waiver_settings.router)
api_router.include_router(notification_settings.router)
api_router.include_router(role_permissions.router, tags=["Role Permissions"])
api_router.include_router(admin_analytics.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(service_commissions.router)
api_router.include_router(soap_notes.router, tags=["Doctor - SOAP Notes"])
api_router.include_router(staff_dashboard.router, tags=["Staff - Dashboard"])
api_router.include_router(emails.router, tags=["Emails"])

# Include other routers as they are created
# api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
# api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
