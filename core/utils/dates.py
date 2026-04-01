# core/utils/dates.py
from datetime import datetime

def to_ymd(date: datetime):
    """
    datetime → YYYY-MM-DD
    """
    return date.strftime("%Y-%m-%d")
