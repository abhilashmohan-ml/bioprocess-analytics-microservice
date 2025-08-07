import re

def validate_batch_id(batch_id: str) -> bool:
    """Simple alphanumeric and dash validation for batch IDs."""
    return bool(re.match(r"^[A-Za-z0-9\-]+$", batch_id))

def safe_parse_int(val, default=0):
    """Safely parse an integer, fall back to default."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

def iso8601_now():
    """Get current UTC timestamp in ISO 8601 format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
