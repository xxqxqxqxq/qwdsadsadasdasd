import discord
from discord.ext import commands
from core.bot import UtilityBot
from core.database import ensure_user, ensure_guild
from utils.logger import logger


class Events(commands.Cog):
    def __init__(self, bot: UtilityBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await ensure_user(
            str(member.id),
            member.name,
            member.display_name,
            str(member.display_avatar),
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await ensure_guild(
            str(guild.id),
            guild.name,
            str(guild.icon) if guild.icon else None,
            str(guild.owner_id) if guild.owner_id else None,
            guild.member_count,
        )
        logger.info(f"Joined guild: {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        await ensure_user(
            str(message.author.id),
            message.author.name,
            message.author.display_name,
            str(message.author.display_avatar),
        )


async def setup(bot: UtilityBot):
    await bot.add_cog(Events(bot))
