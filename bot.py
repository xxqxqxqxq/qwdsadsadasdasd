import asyncio
import sys
import time
import discord
from config import config
from core.bot import UtilityBot
from core.user_api import user_api
from core.presence import presence_gateway
from utils.logger import logger


def print_banner():
    banner = r"""
 _   _    _    ____  _   _ _   _ ____
| | | |  / \  |  _ \| | | | \ | |  _ \
| |_| | / _ \ | |_) | | | |  \| | | | |
|  _  |/ ___ \|  __/| |_| | |\  | |_| |
|_| |_/_/   \_\_|    \___/|_| \_|____/
    """
    print(banner)
    print("=" * 100)
    print("  Discord Application v1.0 -- Python")
    print("=" * 100)


async def main():
    print_banner()

    if not config.TOKEN:
        logger.error("No Discord token found. Set DISCORD_TOKEN in .env")
        sys.exit(1)

    bot = UtilityBot()

    # Start API
    from api.server import start_api
    start_api()

    # Start user API and presence gateway if token provided
    selfbot_token = config.SELFBOT_TOKEN
    if selfbot_token:
        await user_api.start(selfbot_token)
        await presence_gateway.start(selfbot_token)
    else:
        logger.warning("No selfbot token found. Profile/bio info will be limited.")

    try:
        await bot.start(config.TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
