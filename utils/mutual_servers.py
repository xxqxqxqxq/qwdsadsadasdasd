import discord


class MutualServersView(discord.ui.View):
    def __init__(self, user_id: int, selfbot_guild_ids: set, bot_guild_ids: set, bot: discord.Client):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.selfbot_guild_ids = selfbot_guild_ids
        self.bot_guild_ids = bot_guild_ids
        self.bot = bot

    @discord.ui.button(label="Mutual Servers", style=discord.ButtonStyle.secondary, emoji="\U0001f3e2")
    async def mutual_servers(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        selfbot_mutual = self.selfbot_guild_ids
        bot_mutual = self.bot_guild_ids

        lines = []
        if selfbot_mutual:
            lines.append(f"**Selfbot shared:** {len(selfbot_mutual)}")
            for gid in list(selfbot_mutual)[:15]:
                g = self.bot.get_guild(int(gid))
                name = g.name if g else str(gid)
                lines.append(f"\u2022 {name}")
        else:
            lines.append("**Selfbot shared:** None")

        lines.append("")
        if bot_mutual:
            lines.append(f"**Bot shared:** {len(bot_mutual)}")
            for gid in list(bot_mutual)[:15]:
                g = self.bot.get_guild(int(gid))
                name = g.name if g else str(gid)
                lines.append(f"\u2022 {name}")
        else:
            lines.append("**Bot shared:** None")

        total = len(selfbot_mutual | bot_mutual)
        embed = discord.Embed(
            title=f"Mutual Servers with {self.user_id}",
            description="\n".join(lines),
            color=0x5865F2,
        )
        embed.set_footer(text=f"Total: {total} mutual servers")
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True