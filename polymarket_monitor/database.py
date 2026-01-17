import sqlite3
from datetime import datetime
from .config import Config

def get_connection():
    return sqlite3.connect(Config.DATABASE_PATH)

def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS markets (
            condition_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            slug TEXT,
            current_probability REAL,
            outcome TEXT,
            last_updated TIMESTAMP,
            active BOOLEAN DEFAULT 1,
            category TEXT DEFAULT 'other'
        )
    ''')

    # Migration: Add category column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE markets ADD COLUMN category TEXT DEFAULT 'other'")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS large_trades (
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
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def upsert_market(market_data):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO markets
        (condition_id, title, slug, current_probability, outcome, last_updated, active, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        market_data["condition_id"],
        market_data["title"],
        market_data.get("slug", ""),
        market_data["current_probability"],
        market_data.get("outcome", ""),
        datetime.utcnow().isoformat(),
        True,
        market_data.get("category", "other")
    ))
    
    conn.commit()
    conn.close()

def get_monitored_markets():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT condition_id, title, current_probability, slug, category
        FROM markets
        WHERE active = 1 AND current_probability < ?
    ''', (Config.PROBABILITY_THRESHOLD,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {"condition_id": r[0], "title": r[1], "current_probability": r[2], "slug": r[3], "category": r[4]}
        for r in rows
    ]

def is_trade_processed(transaction_hash):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT 1 FROM large_trades WHERE transaction_hash = ?",
        (transaction_hash,)
    )
    
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def insert_large_trade(trade_data):
    if is_trade_processed(trade_data.get("transaction_hash", "")):
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO large_trades 
            (condition_id, market_title, side, size, price, dollar_value, 
             outcome, wallet_address, transaction_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data["condition_id"],
            trade_data.get("market_title", ""),
            trade_data["side"],
            trade_data["size"],
            trade_data["price"],
            trade_data["dollar_value"],
            trade_data.get("outcome", ""),
            trade_data.get("wallet_address", ""),
            trade_data["transaction_hash"],
            trade_data.get("timestamp", datetime.utcnow().isoformat())
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False
