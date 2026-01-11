import requests
import logging
import smtplib
import urllib3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import Config
from .utils import truncate_address, format_currency, format_percentage, format_timestamp

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def send_email_alert(trade_data):
    if not Config.EMAIL_ENABLED or not Config.SMTP_PASSWORD:
        return False
    
    market_url = f"https://polymarket.com/event/{trade_data.get('slug', '')}"
    tx_hash = trade_data.get('transaction_hash', '')
    polygonscan_url = f"https://polygonscan.com/tx/{tx_hash}" if tx_hash else ""
    
    subject = f"Polymarket Alert: {format_currency(trade_data.get('dollar_value', 0))} trade detected"
    
    body = f"""
Large Buy-In Detected on Polymarket

Market: {trade_data.get('market_title', 'Unknown')}
Current Probability: {format_percentage(trade_data.get('current_probability', 0))}
Trade Side: {trade_data.get('side', 'UNKNOWN')}
Outcome: {trade_data.get('outcome', 'Unknown')}
Trade Size: {format_currency(trade_data.get('dollar_value', 0))}
Price: 
Trader: {truncate_address(trade_data.get('wallet_address', ''))}
Time: {format_timestamp(trade_data.get('timestamp', ''))}

View Market: {market_url}
View Transaction: {polygonscan_url}
"""
    
    msg = MIMEMultipart()
    msg['From'] = Config.SMTP_USER
    msg['To'] = Config.ALERT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.sendmail(Config.SMTP_USER, Config.ALERT_EMAIL, msg.as_string())
        server.quit()
        logger.info(f"Email alert sent to {Config.ALERT_EMAIL}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False

def send_discord_alert(trade_data):
    if not Config.DISCORD_WEBHOOK_URL:
        return False
    
    market_url = f"https://polymarket.com/event/{trade_data.get('slug', '')}"
    tx_hash = trade_data.get('transaction_hash', '')
    polygonscan_url = f"https://polygonscan.com/tx/{tx_hash}" if tx_hash else None
    
    embed = {
        "title": "Large Buy-In Detected",
        "color": 15158332,
        "fields": [
            {"name": "Market", "value": trade_data.get("market_title", "Unknown")[:256], "inline": False},
            {"name": "Current Probability", "value": format_percentage(trade_data.get("current_probability", 0)), "inline": True},
            {"name": "Trade Side", "value": trade_data.get("side", "UNKNOWN"), "inline": True},
            {"name": "Outcome", "value": trade_data.get("outcome", "Unknown"), "inline": True},
            {"name": "Trade Size", "value": format_currency(trade_data.get("dollar_value", 0)), "inline": True},
            {"name": "Price", "value": f"", "inline": True},
            {"name": "Trader", "value": truncate_address(trade_data.get("wallet_address", "")), "inline": True}
        ],
        "footer": {"text": f"Detected at {format_timestamp(trade_data.get('timestamp', ''))}"}
    }
    
    if trade_data.get("slug"):
        embed["url"] = market_url
    
    links = []
    if trade_data.get("slug"):
        links.append(f"[View Market]({market_url})")
    if polygonscan_url:
        links.append(f"[View TX]({polygonscan_url})")
    if links:
        embed["fields"].append({"name": "Links", "value": " | ".join(links), "inline": False})
    
    try:
        response = requests.post(Config.DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=10, verify=False)
        response.raise_for_status()
        logger.info(f"Discord alert sent for trade: {tx_hash[:16]}...")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Discord alert: {e}")
        return False

def send_alerts(trades):
    success_count = 0
    for trade in trades:
        discord_ok = send_discord_alert(trade)
        email_ok = send_email_alert(trade)
        if discord_ok or email_ok:
            success_count += 1
    return success_count
