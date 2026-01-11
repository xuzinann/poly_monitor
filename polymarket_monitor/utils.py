from datetime import datetime

def truncate_address(address, chars=6):
    if not address or len(address) < chars * 2:
        return address or "Unknown"
    return f"{address[:chars]}...{address[-chars:]}"

def format_currency(amount):
    return f"${amount:,.2f}"

def format_percentage(value):
    return f"{value * 100:.2f}%"

def format_timestamp(ts):
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except:
            return ts
    if isinstance(ts, (int, float)):
        ts = datetime.utcfromtimestamp(ts)
    return ts.strftime("%Y-%m-%d %H:%M:%S UTC")
