import requests
import logging
import urllib3
from .config import Config
from .database import upsert_market

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def fetch_low_probability_markets():
    markets = []
    
    try:
        url = f"{Config.GAMMA_API_BASE}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 500
        }
        
        response = requests.get(url, params=params, timeout=30, verify=False)
        response.raise_for_status()
        
        all_markets = response.json()
        
        for market in all_markets:
            outcomes = market.get("outcomes", [])
            outcome_prices = market.get("outcomePrices", [])
            
            if not outcome_prices:
                continue
            
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
                        "outcome": outcome_name
                    }
                    
                    if market_data["condition_id"]:
                        markets.append(market_data)
                        upsert_market(market_data)
        
        logger.info(f"Found {len(markets)} low-probability markets (<{Config.PROBABILITY_THRESHOLD*100}%)")
        
    except requests.RequestException as e:
        logger.error(f"Error fetching markets: {e}")
    
    return markets

def refresh_markets():
    logger.info("Refreshing market data...")
    return fetch_low_probability_markets()
