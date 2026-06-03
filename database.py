import aiosqlite
import logging
from datetime import datetime

DB_PATH = "casino.db"
logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0,
                total_deposited REAL DEFAULT 0.0,
                total_withdrawn REAL DEFAULT 0.0,
                total_wagered REAL DEFAULT 0.0,
                total_won REAL DEFAULT 0.0,
                games_played INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                currency TEXT DEFAULT 'USDT',
                status TEXT DEFAULT 'pending',
                invoice_id TEXT,
                check_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game TEXT,
                bet REAL,
                result TEXT,
                profit REAL,
                balance_after REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        await db.commit()
    logger.info("Database initialized")

async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def create_user(user_id: int, username: str, first_name: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()
    return await get_user(user_id)

async def get_or_create_user(user_id: int, username: str, first_name: str) -> dict:
    user = await get_user(user_id)
    if not user:
        user = await create_user(user_id, username, first_name)
    return user

async def update_balance(user_id: int, amount: float) -> float:
    """Add or subtract from balance. Returns new balance."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()
    user = await get_user(user_id)
    return user["balance"]

async def save_game(user_id: int, game: str, bet: float, result: str, profit: float, balance_after: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO game_history (user_id, game, bet, result, profit, balance_after) VALUES (?,?,?,?,?,?)",
            (user_id, game, bet, result, profit, balance_after)
        )
        await db.execute(
            """UPDATE users SET 
               games_played = games_played + 1,
               total_wagered = total_wagered + ?,
               total_won = total_won + ?
               WHERE user_id = ?""",
            (bet, max(0, profit), user_id)
        )
        await db.commit()

async def save_transaction(user_id: int, tx_type: str, amount: float, invoice_id: str = None, status: str = "pending") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO transactions (user_id, type, amount, invoice_id, status) VALUES (?,?,?,?,?)",
            (user_id, tx_type, amount, invoice_id, status)
        )
        await db.commit()
        return cursor.lastrowid

async def update_transaction(tx_id: int, status: str, check_id: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE transactions SET status = ?, check_id = ? WHERE id = ?",
            (status, check_id, tx_id)
        )
        await db.commit()

async def get_top_players(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, first_name, username, total_won, games_played FROM users ORDER BY total_won DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_user_stats(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT game, COUNT(*) as cnt, SUM(bet) as wagered, SUM(profit) as earned FROM game_history WHERE user_id = ? GROUP BY game",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return {r["game"]: dict(r) for r in rows}
