import discord
from discord import app_commands
from discord.ext import commands
from core.bot import UtilityBot
from core.whitelist import whitelist_manager
from core.database import db, create_log
from utils.logger import logger
import traceback

STATUS_COLORS = {
    "online": 0x3BA53B,
    "idle": 0xF0C010,
    "dnd": 0xF02471,
    "invisible": 0x808080,
    "offline": 0x808080,
}

# DIRECT Imgur banner - replace if needed
DEFAULT_BANNER = "https://i.imgur.com/wDoZKcV.jpg"  # Try this; adjust extension if needed (.png/.gif)


def is_whitelisted():
    async def predicate(interaction: discord.Interaction) -> bool:
        is_wl = await whitelist_manager.is_whitelisted(str(interaction.user.id))
        if not is_wl:
            try:
                await interaction.followup.send("fuck off", ephemeral=True)
            except discord.InteractionResponded:
                pass
            return False
        return True
    return app_commands.check(predicate)


class UtilityCog(commands.Cog):
    def __init__(self, bot: UtilityBot):
        self.bot = bot

    @app_commands.command(name="ui", description="Advanced user info with status, badges & bio")
    @app_commands.describe(user="The user to view the profile of")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(users=True, guilds=True)
    @is_whitelisted()
    async def ui(self, interaction: discord.Interaction, user: discord.User = None):
        try:
            await interaction.response.defer()

            if not user:
                await self._do_ui(interaction, str(interaction.user.id))
                return

            await self._do_ui(interaction, str(user.id))
        except discord.HTTPException as e:
            logger.error(f"HTTP error in /ui: {e}")
            try:
                await interaction.followup.send("\u274c An error occurred while processing your request.", ephemeral=True)
            except discord.InteractionResponded:
                pass
        except Exception as e:
            logger.error(f"Error in /ui: {e}")
            traceback.print_exc()
            try:
                await interaction.followup.send("\u274c An error occurred.", ephemeral=True)
            except discord.InteractionResponded:
                pass

    async def _do_ui(self, interaction: discord.Interaction, userid: str):
        try:
            if userid:
                try:
                    target_user = await self.bot.fetch_user(int(userid.strip()))
                except (ValueError, discord.NotFound):
                    await interaction.followup.send(content="\u274c User not found. Make sure the ID is correct.")
                    return
            else:
                target_user = interaction.user

            member = None
            if interaction.guild:
                try:
                    member = await interaction.guild.fetch_member(target_user.id)
                except discord.NotFound:
                    pass

            user = await self.bot.fetch_user(target_user.id)

            profile = await self.bot.user_api.get_user_profile(str(user.id)) or {}
            embeds, files, has_banner = await self._create_ui_embed(
                user, member, profile, self.bot.guilds, self.bot.user_api, interaction.guild
            )
            view = discord.ui.View()
            mutual_guilds = profile.get("mutual_guilds", [])
            if mutual_guilds:
                guild_data = []
                for guild_obj in mutual_guilds:
                    guild_id = guild_obj.get("id") if isinstance(guild_obj, dict) else guild_obj
                    guild_name = guild_obj.get("name") if isinstance(guild_obj, dict) else None
                    if not guild_id:
                        continue
                    try:
                        gid = int(guild_id)
                    except (TypeError, ValueError):
                        continue
                    if not guild_name:
                        guild = await self.bot.user_api.get_guild(gid)
                        if guild:
                            guild_name = guild.get("name")
                    guild_data.append({"id": gid, "name": guild_name or f"Server {gid}"})
                if guild_data:
                    view.add_item(_ServersButton(target_user.id, guild_data, self.bot))

            await interaction.followup.send(embed=embeds, view=view, files=files)

            await create_log(str(interaction.user.id), log_type="utility", action="user_lookup", details={"target": str(target_user.id)})

        except Exception as e:
            traceback.print_exc()
            await interaction.followup.send(content=f"\u274c Error: {e}")

    async def _create_ui_embed(self, user, member, profile, guilds, user_api, current_guild):
        bio = profile.get("bio", "") or ""
        pronouns = profile.get("pronouns", "") or ""
        mutual_guilds = profile.get("mutual_guilds", [])
        badges = profile.get("badges", [])

        # Enhanced bio fetch using selfbot
        if not bio or len(bio.strip()) < 5:
            try:
                raw_profile = await self.bot.user_api.get_user_profile(str(user.id))
                if raw_profile:
                    bio = raw_profile.get("bio", "") or bio
                    pronouns = raw_profile.get("pronouns", "") or pronouns
            except Exception:
                pass

        if not bio:
            try:
                raw_user = await self.bot.http.get_user(user.id)
                bio = raw_user.get("bio", "") or ""
                pronouns = raw_user.get("pronouns", "") or ""
            except Exception:
                pass

        avatar_url = user.display_avatar.replace(size=256, format="gif" if user.display_avatar.is_animated() else "png")
        banner_url = None
        if user.banner:
            banner_url = user.banner.replace(size=4096, format="gif" if user.banner.is_animated() else "png")
        else:
            banner_url = DEFAULT_BANNER  # Custom default banner

        created_ts = int(user.created_at.timestamp())

        from config import config
        is_owner = str(user.id) in config.OWNER_IDS
        is_whitelisted = await whitelist_manager.is_whitelisted(str(user.id))

        if is_owner:
            rank = "Owner"
        elif is_whitelisted:
            rank = "Superstar"
        else:
            rank = "Standard"

        is_server_owner = current_guild and current_guild.owner_id == user.id
        is_admin = member and member.guild_permissions.administrator if member else False
        is_mod = member and member.guild_permissions.ban_members if member else False

        role_badge = ""
        if not is_owner:
            if is_server_owner:
                role_badge = " | Server Owner"
            elif is_admin:
                role_badge = " | Admin"
            elif is_mod:
                role_badge = " | Mod"

        description = ""
        badge_line = self._get_badge_emojis(badges)
        if badge_line:
            description += f"{badge_line}\n"
        description += f"`{rank}{role_badge}`\n"

        if bio:
            description += f"\n{bio[:2000]}\n"

        if pronouns:
            description += f"\n*Pronouns:* {pronouns}\n"

        description += f"\nCreated on <t:{created_ts}:F> (<t:{created_ts}:R>)"

        embed = discord.Embed(description=description, color=0x5865F2)
        embed.set_author(name=f"{user.display_name} (@{user.name})", icon_url=str(avatar_url))
        embed.set_thumbnail(url=str(avatar_url))
        embed.set_footer(text=f"{self.bot.user.name} \u00b7 {user.id}", icon_url="https://img.icons8.com/ios-filled/512/ffffff/discord.png")

        if banner_url:
            embed.set_image(url=str(banner_url))
            files = []
        else:
            files = []

        return embed, files, bool(banner_url)

    def _get_badge_emojis(self, badges):
        badge_line = ""
        for badge in badges or []:
            badge_id = badge.get("id", "") if isinstance(badge, dict) else str(badge)
            if badge_id == "premium_tenure_24_month_v2":
                badge_line += "\u2b50"
            elif badge_id == "hypesquad_house_2":
                badge_line += "\u1f1fa8"
            # ... (keeping rest of badges)
            elif badge_id in ["guild_booster", "guild_booster_lvl1", "guild_booster_lvl2", "guild_booster_lvl3", "guild_booster_lvl4", "guild_booster_lvl5", "guild_booster_lvl6", "guild_booster_lvl7", "guild_booster_lvl8"]:
                badge_line += "\ud83d\udce1"
            elif badge_id == "early_supporter":
                badge_line += "\u2b50"
            elif badge_id == "hypesquad_events":
                badge_line += "\ud83c\udfaf"
            elif "hypesquad" in badge_id.lower():
                badge_line += "\ud83c\udfaf"
            elif badge_id == "nitro" or "nitro" in badge_id.lower():
                badge_line += "\u2728"
            elif badge_id == "developer" or badge_id == "verified_developer":
                badge_line += "\ud83d\udcbb"
            elif "bughunter" in badge_id.lower():
                badge_line += "\ud83d\udc1b"
            elif badge_id == "staff":
                badge_line += "\ud83d\udc51"
            elif badge_id == "partner":
                badge_line += "\ud83d\udc6d"
            else:
                badge_line += f"[{badge_id[:10]}]"
            badge_line += " "
        return badge_line.strip()


class _ServersButton(discord.ui.Button):
    def __init__(self, user_id: int, mutual_guilds: list, bot: discord.Client):
        super().__init__(label="Servers", style=discord.ButtonStyle.secondary)
        self.user_id = user_id
        self.mutual_guilds = mutual_guilds
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        lines = []
        if self.mutual_guilds:
            for guild_data in self.mutual_guilds[:25]:
                name = guild_data.get("name", "Unknown Server")
                lines.append(f"\u2022 {name}")
        else:
            lines.append("No mutual servers found")

        total = len(self.mutual_guilds)
        embed = discord.Embed(
            title=f"Servers ({total})",
            description="\n".join(lines),
            color=0x5865F2,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: UtilityBot):
    await bot.add_cog(UtilityCog(bot))
