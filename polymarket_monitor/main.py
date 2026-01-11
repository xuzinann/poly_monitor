import time
import signal
import logging
import schedule
from .config import Config
from .database import init_database
from .market_discovery import refresh_markets
from .trade_monitor import check_for_large_trades
from .alerting import send_alerts

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('polymarket_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

running = True

def signal_handler(signum, frame):
    global running
    logger.info("Shutdown signal received, stopping...")
    running = False

def monitor_cycle():
    try:
        large_trades = check_for_large_trades()
        if large_trades:
            logger.info(f"Found {len(large_trades)} new large trades")
            sent = send_alerts(large_trades)
            logger.info(f"Sent {sent} Discord alerts")
    except Exception as e:
        logger.error(f"Error in monitor cycle: {e}")

def market_refresh_cycle():
    try:
        markets = refresh_markets()
        logger.info(f"Monitoring {len(markets)} low-probability markets")
    except Exception as e:
        logger.error(f"Error in market refresh: {e}")

def main():
    global running
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Polymarket Large Buy-In Monitor")
    
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    init_database()
    
    logger.info("Initial market discovery...")
    market_refresh_cycle()
    
    schedule.every(Config.POLL_INTERVAL_SECONDS).seconds.do(monitor_cycle)
    schedule.every(Config.MARKET_REFRESH_SECONDS).seconds.do(market_refresh_cycle)
    
    logger.info(f"Polling every {Config.POLL_INTERVAL_SECONDS}s, market refresh every {Config.MARKET_REFRESH_SECONDS}s")
    logger.info(f"Thresholds: probability < {Config.PROBABILITY_THRESHOLD*100}%, trade size >= ${Config.TRADE_SIZE_THRESHOLD:,.0f}")
    
    monitor_cycle()
    
    while running:
        schedule.run_pending()
        time.sleep(1)
    
    logger.info("Monitor stopped")
    return 0

if __name__ == "__main__":
    exit(main())
