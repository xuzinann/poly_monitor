# Polymarket Large Buy-In Monitor - Requirements Document

## Project Overview

**Project Name:** Polymarket Large Buy-In Monitor  
**Purpose:** Monitor and alert on large buy-ins ($300,000+) on low-probability events (<5%) on Polymarket  
**Target User:** Crypto traders and market analysts interested in significant market movements  
**Development Tool:** Claude Code (CC CLI)

---

## Background

Polymarket is a decentralized prediction market platform where users trade on binary outcomes of real-world events. Large buy-ins on low-probability events can signal:
- Insider information
- Market manipulation attempts
- High-conviction contrarian positions
- Coordinated trading activity

This monitoring tool aims to detect these significant trades in real-time for analysis and potential trading opportunities.

---

## Core Requirements

### 1. Market Discovery & Filtering

**Requirement:** Identify all active markets with probability < 5%

**Implementation Details:**
- Use Polymarket Gamma API: `https://gamma-api.polymarket.com`
- Fetch all active/tradable markets
- Filter for markets where current probability < 0.05 (5%)
- Store market metadata: condition ID, title, current odds, end date

**API Endpoints:**
- `GET /markets` - List all markets
- `GET /events` - List events containing markets

**Data Points to Capture:**
- `conditionId` - Unique market identifier
- `title` - Market question/description
- `slug` - URL-friendly identifier
- `outcomes` - Array of possible outcomes (typically "Yes"/"No")
- `outcomePrices` - Current probability for each outcome
- `endDate` - When market closes
- `active` - Whether market is still trading

### 2. Trade Monitoring

**Requirement:** Detect trades with value ≥ $300,000 on low-probability markets

**Implementation Details:**
- Use Polymarket Data API: `https://data-api.polymarket.com`
- Monitor trades endpoint with filtering capabilities
- Calculate trade value correctly for BUY vs SELL orders
- Track both historical and real-time trades

**API Endpoints:**
- `GET /trades` - Get trade history with filters

**Query Parameters:**
- `filterType`: "CASH" or "TOKENS"
- `filterAmount`: 300000 (for $300k threshold)
- `market`: Specific condition ID (optional)
- `limit`: Number of results to return

**Trade Data Structure:**
```json
{
  "proxyWallet": "0x...",
  "side": "BUY" or "SELL",
  "asset": "token_id",
  "conditionId": "market_id",
  "size": 300000,
  "price": 0.045,
  "timestamp": 1234567890,
  "title": "Market question",
  "outcome": "Yes" or "No",
  "transactionHash": "0x..."
}
```

**Value Calculation:**
- BUY orders: Dollar amount = `size × price`
- SELL orders: Dollar amount = `size`
- For this tool: Focus on `size` with `filterType="CASH"` for $300k+ trades

### 3. Real-Time Monitoring (Optional Enhancement)

**Requirement:** Enable real-time alerts for immediate detection

**Implementation Details:**
- Use WebSocket API: `wss://ws-subscriptions-clob.polymarket.com/ws/`
- Subscribe to market channels for live updates
- Process trade events as they occur

**WebSocket Channels:**
- `market` - Public orderbook and trade updates
- Subscribe to specific token IDs from low-probability markets

### 4. Data Storage

**Requirement:** Store detected large trades for historical analysis

**Implementation Details:**
- Use SQLite database (simple, local, no external dependencies)
- Store both market data and detected large trades
- Enable querying and analysis

**Database Schema:**

**Markets Table:**
```sql
CREATE TABLE markets (
  condition_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  slug TEXT,
  current_probability REAL,
  outcome TEXT,
  last_updated TIMESTAMP,
  active BOOLEAN
);
```

**Large Trades Table:**
```sql
CREATE TABLE large_trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  condition_id TEXT NOT NULL,
  market_title TEXT,
  side TEXT,
  size REAL,
  price REAL,
  dollar_value REAL,
  outcome TEXT,
  wallet_address TEXT,
  transaction_hash TEXT UNIQUE,
  timestamp TIMESTAMP,
  detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (condition_id) REFERENCES markets(condition_id)
);
```

### 5. Alerting & Reporting

**Requirement:** Notify user when large trades are detected

**Implementation Options (user preference):**
1. **Console output** - Print to terminal (simplest)
2. **Email notifications** - Send via SMTP
3. **Slack/Discord webhook** - Post to channel
4. **Desktop notifications** - OS-level alerts

**Alert Content Should Include:**
- Market title/question
- Current probability
- Trade side (BUY/SELL)
- Trade size in USDC
- Calculated dollar value
- Wallet address (pseudonymized if available)
- Link to Polymarket market page
- Transaction hash for blockchain verification

**Example Alert:**
```
🚨 LARGE BUY-IN DETECTED 🚨

Market: "Will Bitcoin reach $200k by Dec 2025?"
Current Probability: 3.2%
Trade: BUY $450,000 worth of YES shares
Price: $0.032 per share
Trader: Mean-Record (0x6af7...ff1)
Time: 2025-01-10 14:32:00 UTC

View Market: https://polymarket.com/event/bitcoin-200k-2025
View TX: https://polygonscan.com/tx/0x...
```

---

## Technical Specifications

### Programming Language
**Python 3.9+** (recommended for Polymarket API compatibility)

**Key Libraries:**
- `py-clob-client` - Official Polymarket Python client
- `requests` - HTTP requests (if not using official client)
- `websockets` - For WebSocket connections
- `sqlite3` - Built-in database
- `schedule` or `apscheduler` - Periodic task execution
- `python-dotenv` - Environment variable management

### Configuration

**Environment Variables (.env file):**
```
# API Configuration
POLYMARKET_API_BASE=https://clob.polymarket.com
GAMMA_API_BASE=https://gamma-api.polymarket.com
DATA_API_BASE=https://data-api.polymarket.com

# Monitoring Parameters
PROBABILITY_THRESHOLD=0.05
TRADE_SIZE_THRESHOLD=300000
POLL_INTERVAL_SECONDS=60

# Alert Configuration
ALERT_METHOD=console
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# ALERT_EMAIL=recipient@example.com

# Optional: Webhook URLs
# SLACK_WEBHOOK_URL=https://hooks.slack.com/...
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Rate Limits

**Polymarket API Rate Limits:**
- Free tier: ~100 requests per minute
- Non-trading queries: Up to 1,000 calls/hour
- Trading operations: Higher limits with paid tiers

**Mitigation Strategies:**
1. Use efficient polling intervals (60-120 seconds)
2. Cache market list, only refresh periodically
3. Use WebSocket for real-time (counts as 1 connection, not repeated requests)
4. Batch API calls where possible
5. Implement exponential backoff on rate limit errors

---

## Architecture & Workflow

### High-Level Flow

```
1. Initialization
   ├── Load configuration from .env
   ├── Initialize database (create tables if not exist)
   ├── Initialize Polymarket API clients
   └── Start monitoring loop

2. Market Discovery (runs every 5 minutes)
   ├── Fetch all active markets from Gamma API
   ├── Filter markets with probability < 5%
   ├── Update markets table in database
   └── Extract token IDs for monitoring

3. Trade Monitoring (runs every 60 seconds)
   ├── For each low-probability market:
   │   ├── Query trades endpoint with filters
   │   ├── Check for new large trades (>$300k)
   │   └── Calculate dollar value based on side
   ├── Deduplicate using transaction hash
   ├── Store new large trades in database
   └── Trigger alerts for new detections

4. Alert Processing
   ├── Format alert message
   ├── Send via configured method(s)
   └── Log alert delivery status
```

### Module Structure

```
polymarket_monitor/
├── main.py                 # Entry point, orchestration
├── config.py               # Configuration management
├── database.py             # Database operations
├── market_discovery.py     # Gamma API interactions
├── trade_monitor.py        # Trade detection logic
├── alerting.py             # Alert dispatch
├── utils.py                # Helper functions
├── requirements.txt        # Python dependencies
├── .env.example           # Example configuration
└── README.md              # Setup instructions
```

---

## Features & Functionality

### MVP (Minimum Viable Product)

**Phase 1 - Core Monitoring:**
- ✅ Fetch low-probability markets (<5%)
- ✅ Poll trades API for large buy-ins ($300k+)
- ✅ Store results in SQLite database
- ✅ Console output alerts
- ✅ Basic error handling and logging

### Nice-to-Have Enhancements

**Phase 2 - Enhanced Features:**
- WebSocket integration for real-time monitoring
- Email/Slack/Discord notifications
- Web dashboard for viewing historical alerts
- Market sentiment analysis (volume trends)
- Wallet tracking (repeated large trades from same wallet)
- Price impact calculation
- Configurable thresholds per market category

**Phase 3 - Analytics:**
- Historical success rate (did the event happen?)
- Pattern recognition (time of day, market types)
- Correlation analysis between large trades and outcomes
- Export to CSV for further analysis
- Integration with trading bots (auto-execute counter-trades)

---

## Data Flow Diagrams

### Polling Mode (Default)
```
[Gamma API] --fetch markets--> [Market Discovery Module]
                                        |
                                        v
                                [Filter by probability < 5%]
                                        |
                                        v
                                [Store in DB: markets table]
                                        |
                                        v
[Data API] --query trades--> [Trade Monitor Module]
                                        |
                                        v
                            [Filter by size >= $300k]
                                        |
                                        v
                            [Calculate dollar value]
                                        |
                                        v
                            [Check for duplicates]
                                        |
                                        v
                            [Store in DB: large_trades table]
                                        |
                                        v
                                [Alert Module]
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
                    v                   v                   v
               [Console]           [Email/SMS]         [Webhook]
```

### WebSocket Mode (Optional)
```
[Gamma API] --fetch markets--> [Get token IDs for low-prob markets]
                                        |
                                        v
[WebSocket] <--subscribe to tokens-- [Connection Manager]
      |
      v
[Market events stream]
      |
      v
[Filter: large trades]
      |
      v
[Process & alert] --> [Database] --> [Alerting]
```

---

## Error Handling & Edge Cases

### Expected Errors

1. **API Rate Limiting**
   - Response: HTTP 429
   - Action: Exponential backoff, retry after delay
   - Log: Rate limit hit at [timestamp]

2. **Network Failures**
   - Response: Connection timeout, DNS errors
   - Action: Retry up to 3 times with increasing delays
   - Log: Network error, retrying...

3. **Invalid Market Data**
   - Issue: Missing fields, null values
   - Action: Skip market, log warning
   - Continue processing other markets

4. **Database Errors**
   - Issue: Write failures, lock timeouts
   - Action: Queue writes, retry mechanism
   - Alert: Critical if persistent

### Edge Cases

1. **Market probability fluctuating around 5% threshold**
   - Solution: Use hysteresis (e.g., alert if drops below 4.5%, stop when exceeds 5.5%)

2. **Multiple large trades in same market**
   - Solution: Aggregate or alert individually based on config

3. **Trade size exactly at $300k threshold**
   - Solution: Use >= comparison to include boundary

4. **Stale market data**
   - Solution: Timestamp checks, refresh if data older than X minutes

5. **Duplicate transaction hashes**
   - Solution: Use transaction hash as unique constraint in DB

---

## Testing Requirements

### Unit Tests
- Market filtering logic (probability thresholds)
- Dollar value calculation (BUY vs SELL)
- Alert formatting
- Database operations (CRUD)

### Integration Tests
- End-to-end flow with test data
- Mock API responses
- Database persistence
- Alert delivery

### Manual Testing Checklist
- [ ] Application starts successfully
- [ ] Markets are discovered and filtered correctly
- [ ] Large trades are detected
- [ ] Alerts are sent via configured method
- [ ] Database stores data correctly
- [ ] Rate limits are respected
- [ ] Graceful shutdown on Ctrl+C

---

## Deployment & Operations

### Installation
```bash
# Clone or create project directory
cd polymarket_monitor

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env  # Edit configuration

# Initialize database
python main.py --init-db

# Run monitor
python main.py
```

### Running as Service

**Option 1: Systemd (Linux)**
```ini
[Unit]
Description=Polymarket Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/polymarket_monitor
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Option 2: Docker**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**Option 3: Screen/Tmux (Simple)**
```bash
screen -S polymarket-monitor
python main.py
# Ctrl+A, D to detach
```

### Monitoring & Maintenance

**Logs:**
- Store in `logs/monitor.log` with rotation
- Include timestamps, log levels, contextual info
- Separate error log: `logs/error.log`

**Metrics to Track:**
- Number of markets monitored
- Number of large trades detected
- API calls made per minute
- Alert success rate
- Database size

**Maintenance Tasks:**
- Weekly: Review alert accuracy
- Monthly: Archive old trades (>30 days)
- Quarterly: Update dependencies
- As needed: Adjust thresholds based on market conditions

---

## Success Criteria

The project is successful when:

1. **Accuracy**: Detects all large trades (>$300k) on low-probability markets (<5%) with <1% false negatives
2. **Timeliness**: Alerts sent within 2 minutes of trade execution
3. **Reliability**: Runs continuously with <1% downtime
4. **Usability**: Clear, actionable alerts with all relevant information
5. **Performance**: Stays within API rate limits with current polling strategy
6. **Maintainability**: Code is well-documented and easily configurable

---

## Future Considerations

### Scalability
- If monitoring hundreds of markets, consider distributed architecture
- Use message queue (Redis, RabbitMQ) for alert processing
- Horizontal scaling with multiple monitor instances

### Data Science
- Build ML model to predict outcomes based on large trades
- Sentiment analysis from comments/news
- Correlation with external data sources (news, social media)

### User Interface
- Web dashboard with charts and filters
- Mobile app for push notifications
- REST API for programmatic access to alerts

### Blockchain Integration
- Direct blockchain monitoring (Polygon chain)
- Track wallet addresses across multiple trades
- On-chain analytics for deeper insights

---

## Appendix

### Polymarket API Documentation
- Main Docs: https://docs.polymarket.com
- CLOB API: https://docs.polymarket.com/developers/CLOB/introduction
- Gamma API: https://docs.polymarket.com/developers/gamma-markets-api/overview
- Data API: https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets

### Related Resources
- Polymarket Platform: https://polymarket.com
- Python CLOB Client: https://github.com/Polymarket/py-clob-client
- Polygon Blockchain Explorer: https://polygonscan.com

### Glossary
- **CLOB**: Central Limit Order Book
- **Condition ID**: Unique identifier for a market
- **Token ID**: Identifier for a specific outcome share
- **DXA**: Direct Exchange Access
- **Outcome Token**: Shares representing a position on a market outcome
- **USDC**: USD Coin, the stablecoin used for trading on Polymarket
- **Proxy Wallet**: Smart contract wallet used by Polymarket for gasless transactions

---

## Contact & Support

For questions about this requirements document or the Polymarket API:
- Polymarket Discord: https://discord.gg/polymarket
- Polymarket Support: https://support.polymarket.com

---

**Document Version:** 1.0  
**Last Updated:** January 10, 2025  
**Author:** Requirements compiled for Claude Code development
