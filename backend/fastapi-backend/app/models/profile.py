"""
User profile models
Profile and contact information (no auth data)
"""

from sqlalchemy import Column, String, Date, Text, ForeignKey, Index, Boolean, Integer, Table, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import func

from app.models.base import BaseModel, Base
from app.models.location import Country, State, City


# Association table for many-to-many relationship between users and languages
user_languages = Table(
    'user_languages',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('language_id', UUID(as_uuid=True), ForeignKey('languages.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=True),
    Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True),
    UniqueConstraint('user_id', 'language_id', name='user_languages_user_id_language_id_unique'),
    Index('user_languages_user_id_index', 'user_id'),
    Index('user_languages_language_id_index', 'language_id'),
)


# Association table for many-to-many relationship between users and medical services
user_medical_services = Table(
    'user_medical_services',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('medical_service_id', UUID(as_uuid=True), ForeignKey('medical_services.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=True),
    Column('updated_at', DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True),
    UniqueConstraint('user_id', 'medical_service_id', name='user_medical_services_user_id_medical_service_id_unique'),
    Index('user_medical_services_user_id_index', 'user_id'),
    Index('user_medical_services_medical_service_id_index', 'medical_service_id'),
)


class UserProfile(BaseModel):
    """
    User profile model
    Stores extended profile information (no auth data)
    Matches Laravel user_profiles table structure
    """
    
    __tablename__ = "user_profiles"
    
    # Foreign key to users
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Foreign key to users table"
    )
    
    # Title (as per Figma design - Dr, Mr, Mrs, Ms, etc.)
    # Positioned right after user_id for better organization
    title = Column(String(10), nullable=True, comment="Title prefix (Dr, Mr, Mrs, Ms, etc.)")
    
    # Personal information
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    middle_name = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, other
    bio = Column(Text, nullable=True)
    
    # Profile picture
    avatar = Column(String(255), nullable=True)
    
    # Note: Address fields (address_line_1, address_line_2, city, state, postal_code, country)
    # are stored in contact_details table, not here. This follows best practices:
    # - user_profiles: Personal/demographic information (WHO the person is)
    # - contact_details: Contact information (HOW to reach the person)
    
    # Additional profile fields
    occupation = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Medical/Demographic fields (for patient profile)
    blood_type = Column(String(10), nullable=True, comment="Blood type (O+, A+, B+, AB+, O-, A-, B-, AB-)")
    marital_status = Column(String(50), nullable=True, comment="Marital status (Single, Married, Divorced, Widowed)")
    preferred_language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="SET NULL"), nullable=True, index=True, comment="Foreign key to languages table")
    medical_info = Column(JSONB, nullable=True, comment="Medical information (conditions, allergies, medications) as JSON")
    
    # Doctor-specific fields
    education = Column(String(255), nullable=True, comment="Education details (e.g., MBBS, MD)")
    years_of_experience = Column(Integer, nullable=True, comment="Years of professional experience")
    
    # Patient-specific fields
    hipaa_form_filled = Column(Boolean, nullable=False, default=False, index=True, comment="HIPAA release form filled (required before first appointment)")
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="profile")
    preferred_language = relationship("Language", foreign_keys=[preferred_language_id], lazy="select")
    
    # Indexes
    __table_args__ = (
        Index('user_profiles_user_id_index', 'user_id'),
    )
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"


class ContactDetail(BaseModel):
    """
    Contact details model
    Stores contact information (phone, address, emergency contacts)
    Matches Laravel contact_details table structure
    """
    
    __tablename__ = "contact_details"
    
    # Foreign key to users
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to users table"
    )
    
    # Contact type (primary, secondary, emergency, work, etc.)
    contact_type = Column(
        String(50),
        nullable=False,
        default="primary",
        index=True,
        comment="Type: primary, secondary, emergency, work, home"
    )
    
    # Phone numbers
    phone = Column(String(20), nullable=True)
    phone_secondary = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)
    
    # Email (can be different from users.email)
    email = Column(String(255), nullable=True, index=True)
    
    # Address details
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Location foreign keys (UUIDs)
    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to countries table"
    )
    state_id = Column(
        UUID(as_uuid=True),
        ForeignKey("states.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to states table"
    )
    city_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to cities table"
    )
    
    # Relationships
    country = relationship("Country", foreign_keys=[country_id], lazy="select")
    state = relationship("State", foreign_keys=[state_id], lazy="select")
    city = relationship("City", foreign_keys=[city_id], lazy="select")
    
    # Emergency contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True, comment="Emergency contact number")
    emergency_contact_relationship = Column(String(100), nullable=True)
    
    # Family contact (for patient profile)
    family_contact_phone = Column(String(20), nullable=True, comment="Family contact number")
    
    # Additional contact info
    notes = Column(Text, nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False, index=True, comment="Is this the primary contact?")
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="contact_details")
    
    # Indexes
    __table_args__ = (
        Index('contact_details_user_id_index', 'user_id'),
        Index('contact_details_contact_type_index', 'contact_type'),
        Index('contact_details_is_primary_index', 'is_primary'),
        Index('contact_details_country_id_index', 'country_id'),
        Index('contact_details_state_id_index', 'state_id'),
        Index('contact_details_city_id_index', 'city_id'),
    )
    
    def __repr__(self):
        return f"<ContactDetail(id={self.id}, user_id={self.user_id}, contact_type='{self.contact_type}')>"

