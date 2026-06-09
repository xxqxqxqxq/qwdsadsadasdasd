import discord
from discord import app_commands
from discord.ext import commands
from core.bot import UtilityBot
from utils.embeds import help_embed, COLORS


class GeneralCog(commands.Cog):
    def __init__(self, bot: UtilityBot):
        self.bot = bot

    @app_commands.command(name="help", description="Display the help menu")
    @app_commands.describe(category="Filter by category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Utility", value="utility"),
        app_commands.Choice(name="Administration", value="whitelist"),
        app_commands.Choice(name="General", value="general"),
    ])
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(users=True, guilds=True)
    async def help_cmd(self, interaction: discord.Interaction, category: str | None = None):
        await interaction.response.defer()
        if not await self.bot.check_access(interaction):
            try:
                await interaction.followup.send("fuck off", ephemeral=True)
            except Exception:
                pass
            return
        commands_list = []
        for cmd in self.bot.tree.get_commands():
            if isinstance(cmd, app_commands.Group):
                for sub in cmd.commands:
                    cat = "whitelist" if cmd.name == "whitelist" else cmd.name
                    commands_list.append({
                        "name": f"{cmd.name} {sub.name}",
                        "description": sub.description,
                        "category": cat,
                    })
            else:
                commands_list.append({
                    "name": cmd.name,
                    "description": cmd.description,
                    "category": "general",
                })

        embed = help_embed(commands_list, category)
        await interaction.followup.send(embed=embed)


async def setup(bot: UtilityBot):
    await bot.add_cog(GeneralCog(bot))
