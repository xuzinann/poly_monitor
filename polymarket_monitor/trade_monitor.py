import requests
import logging
import urllib3
from .config import Config
from .database import insert_large_trade, is_trade_processed, get_monitored_markets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def fetch_large_trades():
    large_trades = []
    
    try:
        url = f"{Config.DATA_API_BASE}/trades"
        params = {
            "limit": Config.TRADES_API_LIMIT,
            "filterType": "CASH",
            "filterAmount": Config.TRADE_SIZE_MIN
        }
        
        response = requests.get(url, params=params, timeout=30, verify=False)
        response.raise_for_status()
        
        trades = response.json()
        
        monitored_markets = {m["condition_id"]: m for m in get_monitored_markets()}
        
        for trade in trades:
            size = float(trade.get("size", 0))
            price = float(trade.get("price", 0))
            
            if trade.get("side") == "BUY":
                dollar_value = size * price
            else:
                dollar_value = size
            
            # Check if trade is within the configured range
            if dollar_value < Config.TRADE_SIZE_MIN or dollar_value > Config.TRADE_SIZE_MAX:
                continue
            
            condition_id = trade.get("conditionId", trade.get("market", ""))
            
            market_info = monitored_markets.get(condition_id)
            if not market_info:
                continue
            
            tx_hash = trade.get("transactionHash", trade.get("id", ""))
            
            if is_trade_processed(tx_hash):
                continue
            
            trade_data = {
                "condition_id": condition_id,
                "market_title": market_info.get("title", trade.get("title", "Unknown")),
                "side": trade.get("side", "UNKNOWN"),
                "size": size,
                "price": price,
                "dollar_value": dollar_value,
                "outcome": trade.get("outcome", market_info.get("outcome", "")),
                "wallet_address": trade.get("proxyWallet", trade.get("maker", "")),
                "transaction_hash": tx_hash,
                "timestamp": trade.get("timestamp", ""),
                "current_probability": market_info.get("current_probability", 0),
                "slug": market_info.get("slug", "")
            }
            
            if insert_large_trade(trade_data):
                large_trades.append(trade_data)
                logger.info(f"New large trade detected: ${dollar_value:,.2f} on {trade_data['market_title']}")
    
    except requests.RequestException as e:
        logger.error(f"Error fetching trades: {e}")
    
    return large_trades

def check_for_large_trades():
    logger.debug("Checking for large trades...")
    return fetch_large_trades()
