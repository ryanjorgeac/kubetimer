"""
Time utilities for TTL parsing and expiration checking.

Handles ISO8601 datetime parsing and expiration checks.
"""

from datetime import datetime, timezone


def parse_ttl(ttl_value: str) -> datetime:
    """
    Parse a TTL value in ISO8601 format.
    
    Supports formats like:
    - "2024-01-07T12:00:00Z"
    - "2024-01-07T12:00:00+00:00"
    - "2024-01-07T12:00:00"
    
    Args:
        ttl_value: ISO8601 formatted datetime string
    
    Returns:
        datetime: Parsed datetime object (timezone-aware, UTC)
    
    Raises:
        ValueError: If the TTL format is invalid
    """
    if not ttl_value:
        raise ValueError("TTL value is empty")
    
    ttl_value = ttl_value.strip()
    
    try:
        # Do we really need this?
        if ttl_value.endswith("Z"):
            ttl_value = ttl_value.replace("Z", "+00:00")

        expiry_time = datetime.fromisoformat(ttl_value)

        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(tzinfo=timezone.utc)
        
        return expiry_time
        
    except ValueError as e:
        raise ValueError(f"Invalid ISO8601 format: {e}") from e


def is_ttl_expired(expiry_time: datetime) -> bool:
    """
    Compares the expiry time with current (UTC) time.
    
    Args:
        expiry_time: The datetime to check
    
    Returns:
        bool: True if expired (current time >= expiry time), False otherwise
    """
    now = datetime.now(timezone.utc)
    return now >= expiry_time

# why do we need that?
def get_seconds_until_expiry(expiry_time: datetime) -> float:
    """
    Calculate seconds until expiry (negative if already expired).
    Useful for logging how long until/since expiration.
    
    Args:
        expiry_time: The datetime to check
    
    Returns:
        float: Seconds until expiry (negative if expired)
    """
    now = datetime.now(timezone.utc)
    delta = expiry_time - now
    return delta.total_seconds()
