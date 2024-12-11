import asyncio

from config import dp, bot
import handlers


if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
