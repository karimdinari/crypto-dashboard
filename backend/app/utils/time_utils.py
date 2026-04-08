from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

def to_utc(dt):
    return dt.astimezone(timezone.utc)

def today_str():
    return utc_now().strftime("%Y-%m-%d")