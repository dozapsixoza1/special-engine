import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import Config
from handlers import register_handlers
from database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    config = Config()
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await init_db()
    register_handlers(dp, config)

    logger.info("Casino Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
