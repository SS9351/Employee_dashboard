from datetime import datetime, timedelta

def get_ist_now():
    """Returns the current naive datetime natively shifted to Indian Standard Time (UTC + 5:30)"""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)
