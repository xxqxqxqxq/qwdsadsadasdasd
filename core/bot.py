import discord
from discord.ext import commands
from config import config
from core.database import connect_database
from core.whitelist import whitelist_manager
from core.user_api import user_api
from utils.logger import logger
import time as time_module


class UtilityBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!",
            intents=intents,
            owner_ids=set(config.OWNER_IDS),
        )
        self.start_time = 0
        self._cmd_cooldowns: dict[int, float] = {}
        self._COOLDOWN = 30
        self.user_api = user_api

    async def setup_hook(self):
        self.start_time = time_module.time()
        await connect_database()
        await whitelist_manager.refresh()

        cogs = [
            "cogs.events",
            "cogs.admin",
            "cogs.utility",
            "cogs.general",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.debug(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog: {cog}", e)

    async def check_access(self, interaction: discord.Interaction) -> bool:
        uid = interaction.user.id
        user_id = str(uid)

        if user_id in config.OWNER_IDS:
            return True

        if not config.WHITELIST_ENABLED:
            return True

        if user_id in self._cache.get("whitelisted", set()):
            return True

        entry = await db.whitelist.find_first(
            where={"discordId": user_id},
        )
        if entry:
            if "whitelisted" not in self._cache:
                self._cache["whitelisted"] = set()
            self._cache["whitelisted"].add(user_id)
            return True

        now = time_module.time()
        last = self._cmd_cooldowns.get(uid, 0)
        if now - last < self._COOLDOWN:
            try:
                await interaction.followup.send("fuck off", ephemeral=True)
            except discord.InteractionResponded:
                pass
            return False
        self._cmd_cooldowns[uid] = now
        try:
            await interaction.followup.send("fuck off", ephemeral=True)
        except discord.InteractionResponded:
            pass
        return False

    async def on_ready(self):
        elapsed = time_module.time() - self.start_time
        logger.success(f"Logged in as {self.user} ({self.user.id})")
        logger.info(f"Guilds: {len(self.guilds)} | Users: {len(self.users)}")

        for guild in self.guilds:
            logger.info(f"  Guild: {guild.name} ({guild.id})")

        if self.guilds:
            for guild in self.guilds:
                try:
                    self.tree.clear_commands(guild=guild)
                except Exception:
                    pass

        try:
            synced = await self.tree.sync()
            logger.success(f"Synced {len(synced)} global commands")
        except Exception as e:
            logger.error("Failed to sync global commands", e)

        logger.success(f"Boot completed in {elapsed:.0f}ms")
        await self.change_presence(status=discord.Status.online)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error: {error}")

    async def on_application_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, (discord.app_commands.CheckFailure, discord.app_commands.CommandOnCooldown)):
            return
        logger.error(f"Command error in /{interaction.command.name if interaction.command else 'unknown'}: {error}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred.", ephemeral=True)
        except Exception:
            pass
