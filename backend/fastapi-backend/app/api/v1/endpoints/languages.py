"""
Language endpoints
API endpoints for languages
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.exceptions import laravel_response
from app.models.language import Language
from app.schemas.language import LanguagesListResponse

router = APIRouter()


@router.get("/languages", response_model=LanguagesListResponse, status_code=200)
async def list_languages(
    db: Session = Depends(get_db)
):
    """
    Get list of all languages
    
    **Laravel-compatible endpoint**
    
    Returns all languages sorted by language name.
    No authentication required (public endpoint).
    """
    languages = db.query(Language).order_by(Language.language_name).all()
    
    languages_data = [
        {
            "id": str(language.id),
            "language_name": language.language_name,
            "language_code": language.language_code,
            "created_at": language.created_at.isoformat() if language.created_at else None,
            "updated_at": language.updated_at.isoformat() if language.updated_at else None
        }
        for language in languages
    ]
    
    return laravel_response(
        success=True,
        message="Languages retrieved successfully",
        data={"languages": languages_data}
    )

