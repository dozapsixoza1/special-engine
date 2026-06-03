import os
from dataclasses import dataclass

@dataclass
class Config:
    # === ВСТАВЬ СВОИ ТОКЕНЫ СЮДА ===
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8404617981:AAFN-gvSOUxIFAB9BAwUJfMM7aoq2VWIfLk")
    CRYPTO_PAY_TOKEN: str = os.getenv("CRYPTO_PAY_TOKEN", "591413:AAuG2K1PsJVsJMTbrMWJbYuGn8Muv6jruuL")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://your-domain.com")  # URL где хостится webapp
    ADMIN_IDS: list = 8526401545
    DB_PATH: str = "casino.db"

    # Минимальные/максимальные суммы
    MIN_DEPOSIT: float = 1.0   # USDT
    MIN_BET: float = 0.1       # USDT
    MAX_BET: float = 100.0     # USDT
    MIN_WITHDRAW: float = 1.0  # USDT

    # Crypto Pay API
    CRYPTO_PAY_API_URL: str = "https://pay.crypt.bot/api"  # mainnet
    # CRYPTO_PAY_API_URL: str = "https://testnet-pay.crypt.bot/api"  # testnet (для теста)

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            admin_str = os.getenv("ADMIN_IDS", "")
            self.ADMIN_IDS = [int(x) for x in admin_str.split(",") if x.strip().isdigit()]
