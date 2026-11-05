import asyncio
import os
from contextlib import suppress

import uvicorn
from bot import main as run_telegram_bot
from main import app


async def run_all():
    bot_task = asyncio.create_task(run_telegram_bot(), name="telegram-bot")
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            log_level="info",
        )
    )
    web_task = asyncio.create_task(server.serve(), name="mini-app-api")
    try:
        done, _ = await asyncio.wait(
            {bot_task, web_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            error = task.exception()
            if error:
                raise error
    finally:
        for task in (bot_task, web_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(bot_task, web_task, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(run_all())
