import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CryptoPay:
    def __init__(self, token: str, api_url: str):
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.headers = {"Crypto-Pay-API-Token": token}

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.api_url}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, **kwargs) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    raise Exception(f"CryptoPay API error: {data}")
                return data.get("result", {})

    async def get_me(self) -> dict:
        """Проверить подключение к API"""
        return await self._request("GET", "getMe")

    async def create_invoice(
        self,
        asset: str = "USDT",
        amount: float = 1.0,
        description: str = "Casino Deposit",
        payload: str = "",
        expires_in: int = 3600,
    ) -> dict:
        """Создать счёт для оплаты (депозит)"""
        return await self._request("POST", "createInvoice", json={
            "asset": asset,
            "amount": str(amount),
            "description": description,
            "payload": payload,
            "expires_in": expires_in,
            "allow_comments": False,
            "allow_anonymous": False,
        })

    async def get_invoices(self, invoice_ids: list = None, status: str = None) -> list:
        """Получить список счетов"""
        params = {}
        if invoice_ids:
            params["invoice_ids"] = ",".join(str(i) for i in invoice_ids)
        if status:
            params["status"] = status
        result = await self._request("GET", "getInvoices", params=params)
        return result.get("items", [])

    async def check_invoice(self, invoice_id: int) -> Optional[dict]:
        """Проверить статус конкретного счёта"""
        try:
            invoices = await self.get_invoices(invoice_ids=[invoice_id])
            if invoices:
                return invoices[0]
        except Exception as e:
            logger.error(f"Error checking invoice {invoice_id}: {e}")
        return None

    async def create_check(
        self,
        asset: str = "USDT",
        amount: float = 1.0,
        pin_to_user_id: int = None,
    ) -> dict:
        """Создать чек для вывода средств пользователю"""
        payload = {
            "asset": asset,
            "amount": str(amount),
        }
        if pin_to_user_id:
            payload["pin_to_user_id"] = pin_to_user_id
        return await self._request("POST", "createCheck", json=payload)

    async def get_checks(self, check_ids: list = None, status: str = None) -> list:
        """Получить список чеков"""
        params = {}
        if check_ids:
            params["check_ids"] = ",".join(str(i) for i in check_ids)
        if status:
            params["status"] = status
        result = await self._request("GET", "getChecks", params=params)
        return result.get("items", [])

    async def transfer(
        self,
        user_id: int,
        asset: str = "USDT",
        amount: float = 1.0,
        spend_id: str = "",
        comment: str = "Casino withdrawal",
    ) -> dict:
        """
        Прямой перевод пользователю (требует разрешение в настройках CryptoBot).
        spend_id — уникальный ID для идемпотентности (например str(tx_id)).
        """
        return await self._request("POST", "transfer", json={
            "user_id": user_id,
            "asset": asset,
            "amount": str(amount),
            "spend_id": spend_id,
            "comment": comment,
            "disable_send_notification": False,
        })

    async def get_balance(self) -> list:
        """Баланс приложения CryptoPay"""
        return await self._request("GET", "getBalance")

    async def get_exchange_rates(self) -> list:
        return await self._request("GET", "getExchangeRates")
