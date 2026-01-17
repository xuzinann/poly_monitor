from datetime import datetime
from .config import Config

# Keywords for categorizing markets
SPORTS_KEYWORDS = [
    'nba', 'nfl', 'mlb', 'nhl', 'mls', 'soccer', 'football', 'basketball',
    'baseball', 'hockey', 'tennis', 'golf', 'mma', 'ufc', 'boxing',
    'f1', 'formula', 'premier league', 'champions league', 'world cup',
    'olympics', 'super bowl', 'playoffs', 'championship', 'game', 'match',
    'spread', 'points', 'score', 'win', 'mvp', 'draft', 'roster'
]

POLITICS_KEYWORDS = [
    'trump', 'biden', 'election', 'president', 'presidential', 'congress',
    'senate', 'house', 'governor', 'senator', 'representative', 'democrat',
    'republican', 'political', 'vote', 'ballot', 'campaign', 'primary',
    'nomination', 'cabinet', 'supreme court', 'legislation', 'bill',
    'impeach', 'policy', 'whitehouse', 'gop', 'dnc', 'rnc'
]

def classify_market_category(market):
    """
    Classify a market into a category based on keywords in title/slug.
    Returns 'sports', 'politics', or 'other'.
    """
    title = market.get('question', market.get('title', '')).lower()
    slug = market.get('slug', '').lower()
    combined = f"{title} {slug}"

    # Check for sports keywords
    sports_matches = sum(1 for keyword in SPORTS_KEYWORDS if keyword in combined)

    # Check for politics keywords
    politics_matches = sum(1 for keyword in POLITICS_KEYWORDS if keyword in combined)

    # Return category with highest matches
    if sports_matches > politics_matches and sports_matches > 0:
        return 'sports'
    elif politics_matches > 0:
        return 'politics'
    else:
        return 'other'

def is_monitored_category(market):
    """
    Check if a market belongs to one of the monitored categories.
    """
    category = classify_market_category(market)
    return category in Config.MARKET_CATEGORIES

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
