import re
import logging
from functools import wraps
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Decorator to mark SQLAlchemy model fields as redactable
# ---------------------------------------------------------------------------

def redactable(*field_names: str):
    """Class decorator that registers fields to be considered PII.
    Usage:
        @redactable('email', 'phone_number')
        class User(Base):
            ...
    The names are stored on the class as ``__redactable_fields__``.
    """
    def wrapper(cls):
        setattr(cls, "__redactable_fields__", set(field_names))
        return cls
    return wrapper

# ---------------------------------------------------------------------------
# Masking helpers
# ---------------------------------------------------------------------------

def mask_email(email: str) -> str:
    try:
        local, domain = email.split('@', 1)
        if len(local) <= 1:
            masked_local = '*'
        else:
            masked_local = local[0] + '*' * (len(local) - 1)
        return f"{masked_local}@{domain}"
    except Exception:
        return email

def mask_phone(phone: str) -> str:
    # Keep last 2 digits, mask the rest
    digits = re.sub(r"\D", "", phone)
    if len(digits) <= 2:
        return '*' * len(digits)
    masked = '*' * (len(digits) - 2) + digits[-2:]
    return masked

def mask_ip(ip: str) -> str:
    parts = ip.split('.')
    if len(parts) == 4:
        parts[-1] = '*'
        return '.'.join(parts)
    return ip

# ---------------------------------------------------------------------------
# Core redaction logic
# ---------------------------------------------------------------------------

def redact_data(data: Any, roles: List[str]) -> Any:
    """Recursively walk a JSON‑serialisable structure and mask PII.
    If the caller has the ``pii_viewer`` role, the data is returned untouched.
    """
    if "pii_viewer" in roles:
        return data

    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            lowered = key.lower()
            if lowered in {"email", "e_mail"}:
                redacted[key] = mask_email(str(value))
            elif lowered in {"phone_number", "phone", "telephone"}:
                redacted[key] = mask_phone(str(value))
            elif lowered in {"ip_address", "ip"}:
                redacted[key] = mask_ip(str(value))
            else:
                redacted[key] = redact_data(value, roles)
        return redacted
    elif isinstance(data, list):
        return [redact_data(item, roles) for item in data]
    else:
        return data
