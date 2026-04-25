#!/usr/bin/env python3
"""
Seed language data
Removes all existing languages and seeds major world languages
plus additional languages commonly spoken across Europe.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.language import Language
from loguru import logger


# Major languages spoken worldwide (by speakers / global use)
# + Additional languages commonly spoken across Europe
# Format: (language_name, language_code ISO 639-1)
LANGUAGES = [
    # Major world languages
    ("English", "en"),
    ("Mandarin Chinese", "zh"),
    ("Hindi", "hi"),
    ("Spanish", "es"),
    ("French", "fr"),
    ("Arabic", "ar"),
    ("Bengali", "bn"),
    ("Portuguese", "pt"),
    ("Russian", "ru"),
    ("Japanese", "ja"),
    ("Punjabi", "pa"),
    ("German", "de"),
    ("Javanese", "jv"),
    ("Korean", "ko"),
    ("Italian", "it"),
    ("Turkish", "tr"),
    ("Vietnamese", "vi"),
    ("Telugu", "te"),
    ("Marathi", "mr"),
    ("Tamil", "ta"),
    ("Urdu", "ur"),
    ("Indonesian", "id"),
    ("Thai", "th"),
    ("Persian", "fa"),
    ("Swahili", "sw"),
    ("Hausa", "ha"),
    ("Malay", "ms"),
    # European languages (additional)
    ("Dutch", "nl"),
    ("Polish", "pl"),
    ("Ukrainian", "uk"),
    ("Romanian", "ro"),
    ("Greek", "el"),
    ("Czech", "cs"),
    ("Swedish", "sv"),
    ("Hungarian", "hu"),
    ("Serbian", "sr"),
    ("Bulgarian", "bg"),
    ("Danish", "da"),
    ("Finnish", "fi"),
    ("Norwegian", "no"),
    ("Slovak", "sk"),
    ("Croatian", "hr"),
    ("Catalan", "ca"),
    ("Lithuanian", "lt"),
    ("Slovenian", "sl"),
    ("Latvian", "lv"),
    ("Estonian", "et"),
    ("Irish", "ga"),
    ("Maltese", "mt"),
    ("Icelandic", "is"),
    ("Luxembourgish", "lb"),
    ("Albanian", "sq"),
    ("Macedonian", "mk"),
    ("Bosnian", "bs"),
    ("Welsh", "cy"),
    ("Basque", "eu"),
    ("Galician", "gl"),
]


def seed_languages(db: Session) -> None:
    """
    Remove all existing languages and seed with major world + European languages.
    Clears user_languages and user_profiles.preferred_language_id to avoid FK issues.
    """
    logger.info("Starting language data seeding (replace all)...")

    now = datetime.now(timezone.utc)

    # 1. Clear user_languages (so we can delete languages without FK errors)
    db.execute(text("DELETE FROM user_languages"))
    logger.info("Cleared user_languages associations")

    # 2. Clear preferred_language_id in user_profiles (SET NULL for deleted languages)
    db.execute(text("UPDATE user_profiles SET preferred_language_id = NULL WHERE preferred_language_id IS NOT NULL"))
    logger.info("Cleared preferred_language_id in user_profiles")

    # 3. Delete all existing languages
    db.execute(text("DELETE FROM languages"))
    logger.info("Removed all existing languages")

    # 4. Insert new languages
    for language_name, language_code in LANGUAGES:
        lang = Language(
            id=uuid4(),
            language_name=language_name,
            language_code=language_code,
            created_at=now,
            updated_at=now,
        )
        db.add(lang)

    try:
        db.commit()
        logger.info(f"Successfully seeded {len(LANGUAGES)} languages (major world + European)")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding language data: {e}")
        raise


def main():
    """Main function to seed language data"""
    logger.info("=" * 60)
    logger.info("Language Data Seeder (replace all)")
    logger.info("=" * 60)

    db: Session = SessionLocal()

    try:
        seed_languages(db)
        logger.info("=" * 60)
        logger.info("Language data seeding completed successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Failed to seed language data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
