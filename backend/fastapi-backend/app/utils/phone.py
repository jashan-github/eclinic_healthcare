"""
Phone number formatting utilities
"""

from typing import Tuple


def format_phone_number(country_code: str, phone_number: str) -> str:
    """
    Format phone number as +{country_code} ({area_code}) {first_3}-{last_4}
    
    Example: format_phone_number("1", "7215556781") -> "+1 (721) 555-6781"
    
    Args:
        country_code: Country phone code (e.g., "1", "91")
        phone_number: Phone number without country code (e.g., "7215556781")
    
    Returns:
        Formatted phone number (e.g., "+1 (721) 555-6781")
    """
    # Remove any existing formatting
    phone_clean = phone_number.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "").lstrip("+")
    
    # If phone number is 10 digits, format as: +{country_code} ({area_code}) {first_3}-{last_4}
    # Example: 7215556781 -> +1 (721) 555-6781
    if len(phone_clean) == 10:
        area_code = phone_clean[:3]  # First 3 digits (area code)
        first_3 = phone_clean[3:6]  # Next 3 digits
        last_4 = phone_clean[6:10]   # Last 4 digits
        return f"+{country_code} ({area_code}) {first_3}-{last_4}"
    
    # If phone number is 7 digits, format as: +{country_code} {first_3}-{last_4}
    # Example: 5556781 -> +1 555-6781
    elif len(phone_clean) == 7:
        first_3 = phone_clean[:3]
        last_4 = phone_clean[3:7]
        return f"+{country_code} {first_3}-{last_4}"
    
    # For other lengths, just add country code with space after it
    # Example: 123456789 -> +1 123456789
    else:
        return f"+{country_code} {phone_clean}"


def parse_phone_number(formatted_phone: str) -> Tuple[str, str]:
    """
    Parse formatted phone number to extract country code and phone number
    
    Example: parse_phone_number("+1 (721) 555-6781") -> ("1", "7215556781")
    
    Args:
        formatted_phone: Formatted phone number (e.g., "+1 (721) 555-6781")
    
    Returns:
        Tuple of (country_code, phone_number)
    """
    # Remove all formatting (dashes, spaces, parentheses)
    phone_clean = formatted_phone.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "").lstrip("+")
    
    # Extract country code (first 1-3 digits, typically 1-3 digits)
    # Common country codes: 1, 44, 91, etc.
    if phone_clean.startswith("1") and len(phone_clean) >= 11:
        # US/Canada: +1 (XXX) XXX-XXXX (11 digits total)
        country_code = "1"
        phone_number = phone_clean[1:]
    elif phone_clean.startswith("44") and len(phone_clean) >= 12:
        # UK: +44 XXXX XXXXXX
        country_code = "44"
        phone_number = phone_clean[2:]
    elif phone_clean.startswith("91") and len(phone_clean) >= 12:
        # India: +91 XXXXX XXXXX
        country_code = "91"
        phone_number = phone_clean[2:]
    else:
        # Default: assume 1-digit country code (US/Canada)
        country_code = phone_clean[0] if phone_clean else "1"
        phone_number = phone_clean[1:] if len(phone_clean) > 1 else phone_clean
    
    return (country_code, phone_number)

