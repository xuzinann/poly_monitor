import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    # Email settings
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
    
    PROBABILITY_THRESHOLD = float(os.getenv("PROBABILITY_THRESHOLD", "0.05"))
    TRADE_SIZE_MIN = float(os.getenv("TRADE_SIZE_MIN", "50000"))
    TRADE_SIZE_MAX = float(os.getenv("TRADE_SIZE_MAX", "10000000"))
    TRADE_SIZE_THRESHOLD = float(os.getenv("TRADE_SIZE_THRESHOLD", "50000"))
    POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "4"))
    MARKET_REFRESH_SECONDS = int(os.getenv("MARKET_REFRESH_SECONDS", "360"))

    DATABASE_PATH = os.getenv("DATABASE_PATH", "polymarket_monitor.db")
    MARKET_CATEGORIES = os.getenv("MARKET_CATEGORIES", "sports,politics").split(",")
    TRADES_API_LIMIT = int(os.getenv("TRADES_API_LIMIT", "1000"))
    MARKETS_API_LIMIT = int(os.getenv("MARKETS_API_LIMIT", "2000"))
    
    GAMMA_API_BASE = "https://gamma-api.polymarket.com"
    DATA_API_BASE = "https://data-api.polymarket.com"
    
    @classmethod
    def validate(cls):
        if not cls.DISCORD_WEBHOOK_URL and not cls.EMAIL_ENABLED:
            print("WARNING: No alerting configured - alerts will only print to console")
        if cls.EMAIL_ENABLED and not cls.SMTP_PASSWORD:
            print("WARNING: EMAIL_ENABLED but SMTP_PASSWORD not set")
        if cls.TRADE_SIZE_MIN > cls.TRADE_SIZE_MAX:
            print("WARNING: TRADE_SIZE_MIN is greater than TRADE_SIZE_MAX")
        return True
