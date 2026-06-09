import discord
from utils.embeds import COLORS


class PaginationView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author_id: int, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.embeds) - 1
        self.page_button.label = f"{self.current_page + 1} / {len(self.embeds)}"

    @property
    def current_embed(self) -> discord.Embed:
        return self.embeds[self.current_page]

    async def _update(self, interaction: discord.Interaction):
        self._update_buttons()
        await interaction.response.edit_message(embed=self.current_embed, view=self)

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.secondary)
    async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        await self._update(interaction)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        await self._update(interaction)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.embeds) - 1, self.current_page + 1)
        await self._update(interaction)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.secondary)
    async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.embeds) - 1
        await self._update(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This is not your menu.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            pass


async def paginate(interaction: discord.Interaction, embeds: list[discord.Embed], ephemeral: bool = False):
    if not embeds:
        await interaction.response.send_message("No data to display.", ephemeral=True)
        return

    if len(embeds) == 1:
        await interaction.response.send_message(embed=embeds[0], ephemeral=ephemeral)
        return

    view = PaginationView(embeds, interaction.user.id)
    await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=ephemeral)
    view.message = await interaction.original_response()
