"""Database models (SQLAlchemy ORM)"""

from app.models.base import Base, BaseModel

# Import models to ensure they're registered
from app.models import user  # noqa: F401
from app.models import auth  # noqa: F401
from app.models import profile  # noqa: F401
from app.models import audit  # noqa: F401
from app.models import notification  # noqa: F401
from app.models import availability  # noqa: F401
from app.models import location  # noqa: F401
from app.models import language  # noqa: F401
from app.models import medical_service  # noqa: F401
from app.models import service  # noqa: F401
from app.models import doctor_service  # noqa: F401
from app.models import doctor_service_availability  # noqa: F401
from app.models import doctor_service_pricing  # noqa: F401
from app.models import doctor_service_availability_pricing  # noqa: F401
from app.models import appointment  # noqa: F401
from app.models import appointment_request  # noqa: F401
from app.models import appointment_payment  # noqa: F401
from app.models import vital_name  # noqa: F401
from app.models import patient_vital_signs  # noqa: F401
from app.models import vital_frequency  # noqa: F401
from app.models import clinic_location  # noqa: F401
from app.models import rx_template  # noqa: F401
from app.models import soap_note  # noqa: F401
from app.models import admin_settings  # noqa: F401
from app.models import webhook_log  # noqa: F401
from app.models import hipaa_release_form  # noqa: F401
from app.models import webinar_payment  # noqa: F401
from app.models import push_subscription  # noqa: F401
from app.models import fcm_token  # noqa: F401
from app.models import role_feature_permission  # noqa: F401
from app.models import service_commission  # noqa: F401

__all__ = ["Base", "BaseModel"]
