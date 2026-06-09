import os
import discord
from discord import app_commands
from discord.ext import commands
from core.bot import UtilityBot
from core.whitelist import whitelist_manager
from core.database import db, create_log
from utils.logger import logger

GRADIENT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "imasdadage.png")


def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        bot = interaction.client
        return interaction.user.id in [int(i) for i in bot.owner_ids]
    return app_commands.check(predicate)


class WhitelistCog(commands.GroupCog, name="whitelist", description="Manage the whitelist system"):
    def __init__(self, bot: UtilityBot):
        self.bot = bot

    @app_commands.command(name="add", description="Add a user to the whitelist")
    @app_commands.describe(
        user="User to whitelist",
        reason="Reason",
        role="Role to assign",
        silent="Don't send them a DM",
    )
    @app_commands.choices(role=[
        app_commands.Choice(name="VIP", value="vip"),
        app_commands.Choice(name="Superstar", value="superstar"),
        app_commands.Choice(name="Admin", value="admin"),
    ])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(users=True, guilds=True)
    @is_owner()
    async def add(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        role: str = "vip",
        reason: str | None = None,
        silent: bool = False,
    ):
        await interaction.response.defer(ephemeral=True)
        await whitelist_manager.add_user(str(user.id), str(interaction.user.id), reason, role)
        await create_log(str(interaction.user.id), log_type="whitelist", action="add", details={"target": str(user.id), "reason": reason, "silent": silent})

        embed = discord.Embed(
            title="Whitelisted",
            color=0x57F287,
        )
        embed.add_field(name="User", value=f"`{user}`", inline=True)
        embed.add_field(name="Role", value=f"`{role}`", inline=True)
        if reason:
            embed.add_field(name="Reason", value=f"`{reason}`", inline=True)
        embed.set_thumbnail(url=str(user.display_avatar))
        await interaction.followup.send(embed=embed)

        if not silent:
            try:
                dm = discord.Embed(
                    title=f"Access Granted",
                    description=(
                        f"{user.mention}\n\n"
                        f"You now have **{role}** access to {self.bot.user.name}."
                    ),
                    color=0x57F287,
                )
                if reason:
                    dm.add_field(name="Reason", value=f"`{reason}`", inline=False)
                dm.set_thumbnail(url=str(user.display_avatar))
                dm.set_footer(text=f"{self.bot.user.name}", icon_url="https://img.icons8.com/ios-filled/512/ffffff/discord.png")
                gradient = discord.File(GRADIENT_PATH, filename="gradient.png")
                dm.set_image(url="attachment://gradient.png")
                await user.send(embed=dm, file=gradient)
                logger.info(f"Sent whitelist DM to {user.name} ({user.id})")
            except discord.Forbidden:
                logger.warning(f"Cannot DM {user.name} ({user.id}) - DMs closed")
            except Exception as e:
                logger.error(f"Whitelist DM failed to {user.name}: {e}")

    @app_commands.command(name="remove", description="Remove a user from the whitelist")
    @app_commands.describe(
        user="User to unwhitelist",
        reason="Reason",
        silent="Don't send them a DM",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(users=True, guilds=True)
    @is_owner()
    async def remove(self, interaction: discord.Interaction, user: discord.User, reason: str | None = None, silent: bool = False):
        await interaction.response.defer(ephemeral=True)
        fetched_reason = await whitelist_manager.remove_user(str(user.id))
        final_reason = reason or fetched_reason
        await create_log(str(interaction.user.id), log_type="whitelist", action="remove", details={"target": str(user.id), "reason": final_reason, "silent": silent})

        embed = discord.Embed(
            title="Removed from Whitelist",
            color=0xED4245,
        )
        embed.add_field(name="User", value=f"`{user}`", inline=True)
        if final_reason:
            embed.add_field(name="Reason", value=f"`{final_reason}`", inline=True)
        embed.set_thumbnail(url=str(user.display_avatar))
        await interaction.followup.send(embed=embed)

        if not silent:
            try:
                dm = discord.Embed(
                    title="Access Revoked",
                    description=(
                        f"{user.mention}\n\n"
                        f"Your access to **{self.bot.user.name}** has been revoked."
                    ),
                    color=0xED4245,
                )
                if final_reason:
                    dm.add_field(name="Reason", value=f"`{final_reason}`", inline=False)
                dm.set_footer(text=f"{self.bot.user.name}", icon_url="https://img.icons8.com/ios-filled/512/ffffff/discord.png")
                await user.send(embed=dm)
                logger.info(f"Sent remove DM to {user.name} ({user.id})")
            except discord.Forbidden:
                logger.warning(f"Cannot DM {user.name} ({user.id}) - DMs closed")
            except Exception as e:
                logger.error(f"Remove DM failed to {user.name}: {e}")

    @app_commands.command(name="list", description="List all whitelisted users")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(users=True, guilds=True)
    @is_owner()
    async def list_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        entries = await whitelist_manager.get_all()

        if not entries:
            embed = discord.Embed(
                title="Whitelist",
                description="```No whitelisted users```",
                color=0x5865F2,
            )
            await interaction.followup.send(embed=embed)
            return

        lines = []
        for i, e in enumerate(entries, 1):
            lines.append(f"`{i}.` <@{e['discordId']}> — `{e['role']}`")

        embed = discord.Embed(
            title=f"Whitelisted Users — {len(entries)}",
            description="\n".join(lines[:50]),
            color=0x5865F2,
        )
        await interaction.followup.send(embed=embed)


class ReloadCog(commands.Cog):
    def __init__(self, bot: UtilityBot):
        self.bot = bot

    @app_commands.command(name="reload", description="Reload all cogs and resync commands")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(users=True, guilds=True)
    @is_owner()
    async def reload(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        cogs = ["cogs.events", "cogs.admin", "cogs.utility", "cogs.general"]
        reloaded = []
        failed = []

        for cog in cogs:
            try:
                await self.bot.reload_extension(cog)
                reloaded.append(cog)
            except Exception as e:
                failed.append(f"{cog}: {e}")

        synced = 0
        try:
            if self.bot.guilds:
                for guild in self.bot.guilds:
                    s = await self.bot.tree.sync(guild=guild)
                    synced += len(s)
            else:
                s = await self.bot.tree.sync()
                synced = len(s)
        except Exception as e:
            failed.append(f"Sync: {e}")

        try:
            await whitelist_manager.load()
        except Exception as e:
            failed.append(f"Whitelist: {e}")

        embed = discord.Embed(title="Reload", color=0x57F287)
        if reloaded:
            embed.add_field(name="Reloaded", value=", ".join(reloaded), inline=False)
        embed.add_field(name="Synced", value=f"{synced} commands", inline=False)
        if failed:
            embed.add_field(name="Failed", value="\n".join(f"`{f}`" for f in failed), inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot: UtilityBot):
    await bot.add_cog(WhitelistCog(bot))
    await bot.add_cog(ReloadCog(bot))
