#!/usr/bin/env python3
"""
Seed location data for Sint Maarten
Creates countries, states (districts), and cities for Sint Maarten
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.location import Country, State, City
from loguru import logger


def seed_sint_maarten_locations(db: Session) -> None:
    """
    Seed Sint Maarten country, districts (as states), and cities
    
    Args:
        db: Database session
    """
    logger.info("Starting Sint Maarten location data seeding...")
    
    # 1. Create/Get Sint Maarten Country
    logger.info("Creating Sint Maarten country...")
    country = db.query(Country).filter(
        Country.name == "Sint Maarten",
        Country.deleted_at.is_(None)
    ).first()
    
    if not country:
        country = Country(
            shortname="SX",
            name="Sint Maarten",
            phonecode=1  # NANP country code (1). Area code 721 is part of the phone number, not the country code.
        )
        db.add(country)
        db.flush()  # Flush to get the ID
        logger.info(f"Created country: {country.name} (ID: {country.id})")
    else:
        logger.info(f"Country '{country.name}' already exists (ID: {country.id})")
    
    # 2. Create Districts/Regions (as States)
    # Sint Maarten doesn't have formal states, but has main regions/districts
    # These are the primary administrative/geographical areas
    districts_data = [
        {
            "name": "Philipsburg",
            "sortcode": "PB",
            "icon": None,
            "description": "Capital and main commercial district"
        },
        {
            "name": "Lower Prince's Quarter",
            "sortcode": "LPQ",
            "icon": None,
            "description": "Lower Prince's Quarter district"
        },
        {
            "name": "Upper Prince's Quarter",
            "sortcode": "UPQ",
            "icon": None,
            "description": "Upper Prince's Quarter district"
        },
        {
            "name": "Simpson Bay",
            "sortcode": "SB",
            "icon": None,
            "description": "Simpson Bay area"
        },
        {
            "name": "Cole Bay",
            "sortcode": "CB",
            "icon": None,
            "description": "Cole Bay district"
        },
        {
            "name": "Maho",
            "sortcode": "MH",
            "icon": None,
            "description": "Maho area"
        },
        {
            "name": "Cul de Sac",
            "sortcode": "CDS",
            "icon": None,
            "description": "Cul de Sac area"
        },
        {
            "name": "Dutch Quarter",
            "sortcode": "DQ",
            "icon": None,
            "description": "Dutch Quarter district"
        },
        {
            "name": "Oyster Pond",
            "sortcode": "OP",
            "icon": None,
            "description": "Oyster Pond area"
        },
        {
            "name": "Pointe Blanche",
            "sortcode": "PB",
            "icon": None,
            "description": "Pointe Blanche area"
        },
        {
            "name": "St. Peters",
            "sortcode": "SP",
            "icon": None,
            "description": "St. Peters area"
        },
        {
            "name": "Little Bay",
            "sortcode": "LB",
            "icon": None,
            "description": "Little Bay area"
        },
        {
            "name": "Mullet Bay",
            "sortcode": "MB",
            "icon": None,
            "description": "Mullet Bay area"
        },
        {
            "name": "Belvedere",
            "sortcode": "BV",
            "icon": None,
            "description": "Belvedere area"
        },
        {
            "name": "Saunders",
            "sortcode": "SD",
            "icon": None,
            "description": "Saunders area"
        },
        {
            "name": "Zorg en Rust",
            "sortcode": "ZR",
            "icon": None,
            "description": "Zorg en Rust area"
        }
    ]
    
    states_map = {}
    for district_data in districts_data:
        district_name = district_data["name"]
        
        # Check if state already exists
        existing_state = db.query(State).filter(
            State.name == district_name,
            State.country_id == country.id,
            State.deleted_at.is_(None)
        ).first()
        
        if not existing_state:
            state = State(
                name=district_name,
                sortcode=district_data["sortcode"],
                icon=district_data["icon"],
                country_id=country.id
            )
            db.add(state)
            db.flush()
            states_map[district_name] = state
            logger.info(f"Created district/state: {district_name} (ID: {state.id})")
        else:
            states_map[district_name] = existing_state
            logger.info(f"District/state '{district_name}' already exists (ID: {existing_state.id})")
    
    # 3. Create Cities/Towns
    # Mapping all cities, towns, and neighborhoods to their districts
    cities_data = [
        # Philipsburg (Capital District)
        {"name": "Philipsburg", "district": "Philipsburg"},
        {"name": "Great Bay", "district": "Philipsburg"},
        {"name": "Front Street", "district": "Philipsburg"},
        {"name": "Back Street", "district": "Philipsburg"},
        {"name": "L.B. Scott Road", "district": "Philipsburg"},
        {"name": "A. Th. Illidge Road", "district": "Philipsburg"},
        {"name": "W.J.A. Nisbeth Road", "district": "Philipsburg"},
        {"name": "Cannegieter Street", "district": "Philipsburg"},
        {"name": "Walter Nisbeth Road", "district": "Philipsburg"},
        {"name": "Juancho Yrausquin Boulevard", "district": "Philipsburg"},
        
        # Lower Prince's Quarter
        {"name": "Lower Prince's Quarter", "district": "Lower Prince's Quarter"},
        {"name": "Union Road", "district": "Lower Prince's Quarter"},
        {"name": "Cay Hill", "district": "Lower Prince's Quarter"},
        {"name": "Welfare Road", "district": "Lower Prince's Quarter"},
        {"name": "Cay Bay", "district": "Lower Prince's Quarter"},
        
        # Upper Prince's Quarter
        {"name": "Upper Prince's Quarter", "district": "Upper Prince's Quarter"},
        {"name": "St. John's Estate", "district": "Upper Prince's Quarter"},
        {"name": "Bush Road", "district": "Upper Prince's Quarter"},
        {"name": "Middle Region", "district": "Upper Prince's Quarter"},
        
        # Simpson Bay
        {"name": "Simpson Bay", "district": "Simpson Bay"},
        {"name": "Pelican Key", "district": "Simpson Bay"},
        {"name": "Cupecoy", "district": "Simpson Bay"},
        {"name": "Dawn Beach", "district": "Simpson Bay"},
        {"name": "Airport Road", "district": "Simpson Bay"},
        {"name": "Terres Basses", "district": "Simpson Bay"},
        {"name": "Lowlands", "district": "Simpson Bay"},
        {"name": "Nettle Bay", "district": "Simpson Bay"},
        {"name": "Baie Longue", "district": "Simpson Bay"},
        {"name": "Baie Rouge", "district": "Simpson Bay"},
        
        # Cole Bay
        {"name": "Cole Bay", "district": "Cole Bay"},
        {"name": "Vineyard Road", "district": "Cole Bay"},
        {"name": "Beacon Hill", "district": "Cole Bay"},
        {"name": "Union Road", "district": "Cole Bay"},  # Union Road area in Cole Bay
        
        # Maho
        {"name": "Maho", "district": "Maho"},
        {"name": "Maho Beach", "district": "Maho"},
        {"name": "Maho Village", "district": "Maho"},
        {"name": "Airport Boulevard", "district": "Maho"},
        {"name": "Maho Bay", "district": "Maho"},
        
        # Cul de Sac
        {"name": "Cul de Sac", "district": "Cul de Sac"},
        {"name": "Orient Bay", "district": "Cul de Sac"},
        {"name": "Orient Beach", "district": "Cul de Sac"},
        {"name": "Indigo Bay", "district": "Cul de Sac"},
        {"name": "Happy Bay", "district": "Cul de Sac"},
        {"name": "Friar's Bay", "district": "Cul de Sac"},
        
        # Dutch Quarter
        {"name": "Dutch Quarter", "district": "Dutch Quarter"},
        
        # Oyster Pond
        {"name": "Oyster Pond", "district": "Oyster Pond"},
        {"name": "Oyster Bay", "district": "Oyster Pond"},
        
        # Pointe Blanche
        {"name": "Pointe Blanche", "district": "Pointe Blanche"},
        {"name": "Pointe Blanche Bay", "district": "Pointe Blanche"},
        
        # St. Peters
        {"name": "St. Peters", "district": "St. Peters"},
        
        # Little Bay
        {"name": "Little Bay", "district": "Little Bay"},
        {"name": "Fort Amsterdam", "district": "Little Bay"},
        {"name": "Little Bay Beach", "district": "Little Bay"},
        
        # Mullet Bay
        {"name": "Mullet Bay", "district": "Mullet Bay"},
        {"name": "Mullet Bay Beach", "district": "Mullet Bay"},
        
        # Belvedere
        {"name": "Belvedere", "district": "Belvedere"},
        
        # Saunders
        {"name": "Saunders", "district": "Saunders"},
        
        # Zorg en Rust
        {"name": "Zorg en Rust", "district": "Zorg en Rust"},
    ]
    
    cities_created = 0
    cities_existing = 0
    
    for city_data in cities_data:
        city_name = city_data["name"]
        district_name = city_data["district"]
        
        # Get the state (district) for this city
        state = states_map.get(district_name)
        if not state:
            logger.warning(f"District '{district_name}' not found for city '{city_name}', skipping...")
            continue
        
        # Check if city already exists
        existing_city = db.query(City).filter(
            City.name == city_name,
            City.state_id == state.id,
            City.deleted_at.is_(None)
        ).first()
        
        if not existing_city:
            city = City(
                name=city_name,
                icon="icons/state.png",  # Default icon
                state_id=state.id
            )
            db.add(city)
            cities_created += 1
            logger.debug(f"Created city: {city_name} in {district_name}")
        else:
            cities_existing += 1
            logger.debug(f"City '{city_name}' already exists in {district_name}")
    
    # Commit all changes
    try:
        db.commit()
        logger.info(f"✓ Successfully seeded Sint Maarten location data:")
        logger.info(f"  - 1 Country: Sint Maarten")
        logger.info(f"  - {len(states_map)} Districts/States")
        logger.info(f"  - {cities_created} Cities created, {cities_existing} already existed")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding location data: {e}")
        raise


def main():
    """Main function to seed location data"""
    logger.info("=" * 60)
    logger.info("Sint Maarten Location Data Seeder")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        seed_sint_maarten_locations(db)
        logger.info("=" * 60)
        logger.info("Location data seeding completed successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Failed to seed location data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

