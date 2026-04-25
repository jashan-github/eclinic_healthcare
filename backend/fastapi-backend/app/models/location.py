"""
Location models
Countries, States, and Cities for address management
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Country(BaseModel):
    """
    Country model
    Stores country information
    """
    
    __tablename__ = "countries"
    
    shortname = Column(String(10), nullable=False, comment="Country short name/code (e.g., US, IN, UK)")
    name = Column(String(50), nullable=False, comment="Country full name")
    phonecode = Column(Integer, nullable=False, comment="International phone code")
    
    # Relationships
    states = relationship("State", back_populates="country", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index('countries_shortname_index', 'shortname'),
        Index('countries_name_index', 'name'),
    )
    
    def __repr__(self):
        return f"<Country(id={self.id}, name='{self.name}', shortname='{self.shortname}')>"


class State(BaseModel):
    """
    State model
    Stores state/province information
    """
    
    __tablename__ = "states"
    
    name = Column(String(50), nullable=False, comment="State name")
    icon = Column(String(255), nullable=True, comment="State icon path")
    sortcode = Column(String(20), nullable=True, comment="State sort code")
    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to countries table"
    )
    state_id = Column(Integer, nullable=True, comment="Legacy state ID (for backward compatibility)")
    
    # Relationships
    country = relationship("Country", back_populates="states", lazy="select")
    cities = relationship("City", back_populates="state", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index('states_country_id_index', 'country_id'),
        Index('states_name_index', 'name'),
    )
    
    def __repr__(self):
        return f"<State(id={self.id}, name='{self.name}', country_id={self.country_id})>"


class City(BaseModel):
    """
    City model
    Stores city information
    """
    
    __tablename__ = "cities"
    
    name = Column(String(50), nullable=False, comment="City name")
    icon = Column(
        String(255),
        nullable=False,
        default="icons/state.png",
        server_default="icons/state.png",
        comment="City icon path"
    )
    state_id = Column(
        UUID(as_uuid=True),
        ForeignKey("states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to states table"
    )
    city_id = Column(Integer, nullable=True, comment="Legacy city ID (for backward compatibility)")
    
    # Relationships
    state = relationship("State", back_populates="cities", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index('cities_state_id_index', 'state_id'),
        Index('cities_name_index', 'name'),
    )
    
    def __repr__(self):
        return f"<City(id={self.id}, name='{self.name}', state_id={self.state_id})>"

