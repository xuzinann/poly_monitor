import requests
import logging
import urllib3
from .config import Config
from .database import upsert_market
from .utils import classify_market_category, is_monitored_category

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def fetch_low_probability_markets():
    markets = []
    
    try:
        url = f"{Config.GAMMA_API_BASE}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": Config.MARKETS_API_LIMIT
        }
        
        response = requests.get(url, params=params, timeout=30, verify=False)
        response.raise_for_status()

        all_markets = response.json()
        logger.info(f"API returned {len(all_markets)} total active markets (limit: {Config.MARKETS_API_LIMIT})")

        sports_politics_count = sum(1 for m in all_markets if is_monitored_category(m))
        logger.info(f"Found {sports_politics_count} sports/politics markets before probability filtering")

        if len(all_markets) >= Config.MARKETS_API_LIMIT:
            logger.warning(f"API returned exactly {len(all_markets)} markets (at limit). You may be missing some markets. Consider increasing MARKETS_API_LIMIT.")

        for market in all_markets:
            # Check if market belongs to monitored categories
            if not is_monitored_category(market):
                continue

            outcomes = market.get("outcomes", [])
            outcome_prices = market.get("outcomePrices", [])

            if not outcome_prices:
                continue

            category = classify_market_category(market)

            for i, price_str in enumerate(outcome_prices):
                try:
                    price = float(price_str)
                except (ValueError, TypeError):
                    continue

                if price < Config.PROBABILITY_THRESHOLD:
                    outcome_name = outcomes[i] if i < len(outcomes) else f"Outcome {i}"

                    market_data = {
                        "condition_id": market.get("conditionId", ""),
                        "title": market.get("question", market.get("title", "Unknown")),
                        "slug": market.get("slug", ""),
                        "current_probability": price,
                        "outcome": outcome_name,
                        "category": category
                    }

                    if market_data["condition_id"]:
                        markets.append(market_data)
                        upsert_market(market_data)
        
        categories_str = ", ".join(Config.MARKET_CATEGORIES)
        logger.info(f"Found {len(markets)} low-probability markets (<{Config.PROBABILITY_THRESHOLD*100}%) in categories: {categories_str}")
        
    except requests.RequestException as e:
        logger.error(f"Error fetching markets: {e}")
    
    return markets

def refresh_markets():
    logger.info("Refreshing market data...")
    return fetch_low_probability_markets()
