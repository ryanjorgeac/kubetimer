"""
Time utilities for TTL parsing and expiration checking.

Handles ISO8601 datetime parsing and expiration checks with timezone support.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def get_timezone(timezone_str: str = "UTC") -> ZoneInfo | timezone:
    if timezone_str == "UTC":
        return timezone.utc
    
    try:
        return ZoneInfo(timezone_str)
    except KeyError:
        raise ValueError(f"Invalid timezone: {timezone_str}. Use IANA format like 'America/New_York'")


def parse_ttl(ttl_value: str) -> datetime:
    if not ttl_value:
        raise ValueError("TTL value is empty")
    
    ttl_value = ttl_value.strip()
    
    try:
        expiry_time = datetime.fromisoformat(ttl_value)
        
        if expiry_time.tzinfo is None:
            tz = get_timezone("UTC")
            expiry_time = expiry_time.replace(tzinfo=tz)
        return expiry_time
    except ValueError as e:
        raise ValueError(f"Invalid ISO8601 format: {e}") from e


def is_ttl_expired(expiry_time: datetime, timezone_str: str = "UTC") -> bool:
    """
    Check if a TTL has expired.
    
    Compares the expiry time with current time in the configured timezone.
    
    Args:
        expiry_time: The datetime to check (must be timezone-aware)
        timezone_str: Timezone for current time comparison
    
    Returns:
        bool: True if expired (current time >= expiry time), False otherwise
    
    Note:
        Both times are converted to the same timezone for accurate comparison.
    """
    tz = get_timezone(timezone_str)
    now = datetime.now(tz)
    
    # Convert expiry_time to same timezone for comparison
    # This handles cases where TTL was set in different timezone
    expiry_in_tz = expiry_time.astimezone(tz)
    
    return now >= expiry_in_tz

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


if __name__ == "__main__":
    # Example usage
    ttl_str = "2024-12-31T23:59:59"
    tz_str = "America/New_York"
    
    expiry = parse_ttl(ttl_str)
    print(f"Parsed expiry: {expiry.isoformat()}")
    
    expired = is_ttl_expired(expiry, tz_str)
    print(f"Is TTL expired? {expired}")
    
    seconds_left = get_seconds_until_expiry(expiry)
    print(f"Seconds until expiry: {seconds_left}")