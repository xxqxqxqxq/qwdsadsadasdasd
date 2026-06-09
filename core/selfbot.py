import discord
from discord.ext import commands
import asyncio
import os
from utils.logger import logger


class SelfbotManager:
    def __init__(self):
        self.presence_cache = {}
        self.self_client = None
        self.ready = False

    async def start(self, token: str):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        self.self_client = discord.Client(intents=intents)

        @self.self_client.event
        async def on_ready():
            self.ready = True
            logger.success(f"Selfbot logged in as {self.self_client.user}")

        @self.self_client.event
        async def on_presence_update(before, after):
            self.presence_cache[after.id] = after

        try:
            await self.self_client.start(token)
        except Exception as e:
            logger.error(f"Selfbot failed to start: {e}")

    def get_presence(self, user_id: int):
        return self.presence_cache.get(user_id)


selfbot_manager = SelfbotManager()