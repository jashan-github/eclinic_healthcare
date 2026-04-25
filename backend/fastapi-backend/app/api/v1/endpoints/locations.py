"""
Location endpoints
API endpoints for countries, states, and cities
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, select

from app.core.dependencies import get_db
from app.core.exceptions import laravel_response, NotFoundException
from app.models.location import Country, State, City
from app.schemas.location import (
    CountriesListResponse,
    StatesListResponse,
    CitiesListResponse
)

router = APIRouter()


@router.get("/countries", response_model=CountriesListResponse, status_code=200)
async def list_countries(
    db: Session = Depends(get_db)
):
    """
    Get list of all countries
    
    **Laravel-compatible endpoint**
    
    Returns all countries sorted by name.
    No authentication required (public endpoint).
    """
    countries = db.query(Country).filter(
        Country.deleted_at.is_(None)
    ).order_by(Country.name).all()
    
    countries_data = [
        {
            "id": str(country.id),
            "shortname": country.shortname,
            "name": country.name,
            "phonecode": country.phonecode,
            "created_at": country.created_at.isoformat() if country.created_at else None,
            "updated_at": country.updated_at.isoformat() if country.updated_at else None
        }
        for country in countries
    ]
    
    return laravel_response(
        success=True,
        message="Countries retrieved successfully",
        data={"countries": countries_data}
    )


@router.get("/countries/{country_id}/states", response_model=StatesListResponse, status_code=200)
async def list_states_by_country(
    country_id: UUID = Path(..., description="Country ID (UUID)"),
    db: Session = Depends(get_db)
):
    """
    Get list of states by country
    
    **Laravel-compatible endpoint**
    
    Path parameters:
    - **country_id**: Country ID (UUID)
    
    Returns all states for the specified country, sorted by name.
    No authentication required (public endpoint).
    """
    # Verify country exists
    country = db.query(Country).filter(
        Country.id == country_id,
        Country.deleted_at.is_(None)
    ).first()
    
    if not country:
        raise NotFoundException(
            message="Country not found",
            errors={"country_id": ["Country does not exist"]}
        )
    
    states = db.query(State).filter(
        State.country_id == country_id,
        State.deleted_at.is_(None)
    ).order_by(State.name).all()
    
    states_data = [
        {
            "id": str(state.id),
            "name": state.name,
            "icon": state.icon,
            "sortcode": state.sortcode,
            "country_id": str(state.country_id),
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None
        }
        for state in states
    ]
    
    return laravel_response(
        success=True,
        message="States retrieved successfully",
        data={"states": states_data}
    )


@router.get("/states/{state_id}/cities", response_model=CitiesListResponse, status_code=200)
async def list_cities_by_state(
    state_id: UUID = Path(..., description="State ID (UUID)"),
    db: Session = Depends(get_db)
):
    """
    Get list of cities by state
    
    **Laravel-compatible endpoint**
    
    Path parameters:
    - **state_id**: State ID (UUID)
    
    Returns all cities for the specified state, sorted by name.
    No authentication required (public endpoint).
    """
    # Verify state exists
    state = db.query(State).filter(
        State.id == state_id,
        State.deleted_at.is_(None)
    ).first()
    
    if not state:
        raise NotFoundException(
            message="State not found",
            errors={"state_id": ["State does not exist"]}
        )
    
    cities = db.query(City).filter(
        City.state_id == state_id,
        City.deleted_at.is_(None)
    ).order_by(City.name).all()
    
    cities_data = [
        {
            "id": str(city.id),
            "name": city.name,
            "icon": city.icon,
            "state_id": str(city.state_id),
            "created_at": city.created_at.isoformat() if city.created_at else None,
            "updated_at": city.updated_at.isoformat() if city.updated_at else None
        }
        for city in cities
    ]
    
    return laravel_response(
        success=True,
        message="Cities retrieved successfully",
        data={"cities": cities_data}
    )


@router.get("/states", response_model=StatesListResponse, status_code=200)
async def list_all_states(
    country_id: Optional[UUID] = Query(None, description="Filter by country ID (UUID)"),
    db: Session = Depends(get_db)
):
    """
    Get list of all states (optionally filtered by country)
    
    **Laravel-compatible endpoint**
    
    Query parameters:
    - **country_id**: (Optional) Filter by country ID (UUID)
    
    Returns all states, optionally filtered by country, sorted by name.
    No authentication required (public endpoint).
    """
    query = db.query(State).filter(State.deleted_at.is_(None))
    
    if country_id:
        # Verify country exists if filtering
        country = db.query(Country).filter(
            Country.id == country_id,
            Country.deleted_at.is_(None)
        ).first()
        
        if not country:
            raise NotFoundException(
                message="Country not found",
                errors={"country_id": ["Country does not exist"]}
            )
        
        query = query.filter(State.country_id == country_id)
    
    states = query.order_by(State.name).all()
    
    states_data = [
        {
            "id": str(state.id),
            "name": state.name,
            "icon": state.icon,
            "sortcode": state.sortcode,
            "country_id": str(state.country_id),
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None
        }
        for state in states
    ]
    
    return laravel_response(
        success=True,
        message="States retrieved successfully",
        data={"states": states_data}
    )


@router.get("/cities", response_model=CitiesListResponse, status_code=200)
async def list_all_cities(
    state_id: Optional[UUID] = Query(None, description="Filter by state ID (UUID)"),
    country_id: Optional[UUID] = Query(None, description="Filter by country ID (UUID)"),
    db: Session = Depends(get_db)
):
    """
    Get list of all cities (optionally filtered by state or country)
    
    **Laravel-compatible endpoint**
    
    Query parameters:
    - **state_id**: (Optional) Filter by state ID (UUID)
    - **country_id**: (Optional) Filter by country ID (UUID)
    
    Returns all cities, optionally filtered by state or country, sorted by name.
    No authentication required (public endpoint).
    """
    query = db.query(City).filter(City.deleted_at.is_(None))
    
    if state_id:
        # Verify state exists if filtering
        state = db.query(State).filter(
            State.id == state_id,
            State.deleted_at.is_(None)
        ).first()
        
        if not state:
            raise NotFoundException(
                message="State not found",
                errors={"state_id": ["State does not exist"]}
            )
        
        query = query.filter(City.state_id == state_id)
    elif country_id:
        # Filter by country (cities through states)
        # Verify country exists if filtering
        country = db.query(Country).filter(
            Country.id == country_id,
            Country.deleted_at.is_(None)
        ).first()
        
        if not country:
            raise NotFoundException(
                message="Country not found",
                errors={"country_id": ["Country does not exist"]}
            )
        
        # Get all state IDs for this country using subquery
        state_subquery = select(State.id).where(
            and_(State.country_id == country_id, State.deleted_at.is_(None))
        ).scalar_subquery()
        
        query = query.filter(City.state_id.in_(state_subquery))
    
    cities = query.order_by(City.name).all()
    
    cities_data = [
        {
            "id": str(city.id),
            "name": city.name,
            "icon": city.icon,
            "state_id": str(city.state_id),
            "created_at": city.created_at.isoformat() if city.created_at else None,
            "updated_at": city.updated_at.isoformat() if city.updated_at else None
        }
        for city in cities
    ]
    
    return laravel_response(
        success=True,
        message="Cities retrieved successfully",
        data={"cities": cities_data}
    )

