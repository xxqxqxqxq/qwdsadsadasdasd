import discord
from config import config

COLORS = {
    "primary": 0x2B2D31,
    "secondary": 0x1E1F22,
    "accent": 0x5865F2,
    "success": 0x57F287,
    "warning": 0xFEE75C,
    "error": 0xED4245,
    "info": 0x5865F2,
}


def create_embed(
    *,
    title: str | None = None,
    description: str | None = None,
    color: int = COLORS["primary"],
    fields: list[dict] | None = None,
    footer: str | None = None,
    thumbnail: str | None = None,
    image: str | None = None,
    author: tuple | None = None,
    timestamp: bool = False,
) -> discord.Embed:
    embed = discord.Embed(color=color)
    if title:
        embed.title = title
    if description:
        embed.description = description
    if fields:
        for f in fields:
            embed.add_field(
                name=f.get("name", "\u200b"),
                value=f.get("value", "\u200b"),
                inline=f.get("inline", False),
            )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if author:
        embed.set_author(name=author[0], icon_url=author[1] if len(author) > 1 else None)
    if footer:
        embed.set_footer(text=footer)
    if timestamp:
        embed.timestamp = discord.utils.utcnow()
    return embed


def error_embed(title: str, description: str) -> discord.Embed:
    return create_embed(title=f"❌ {title}", description=description, color=COLORS["error"], timestamp=True)


def success_embed(title: str, description: str) -> discord.Embed:
    return create_embed(title=f"✅ {title}", description=description, color=COLORS["success"], timestamp=True)


def warning_embed(title: str, description: str) -> discord.Embed:
    return create_embed(title=f"⚠️ {title}", description=description, color=COLORS["warning"], timestamp=True)


def info_embed(title: str, description: str) -> discord.Embed:
    return create_embed(title=f"ℹ️ {title}", description=description, color=COLORS["info"], timestamp=True)


def loading_embed(title: str, description: str) -> discord.Embed:
    dots = ["▪ ▫ ▫", "▫ ▪ ▫", "▫ ▫ ▪"]
    return create_embed(
        title=f"🔄 {title}",
        description=f"{description}\n\n```{dots[0]}\n{dots[1]}\n{dots[2]}```",
        color=COLORS["secondary"],
    )


def help_embed(commands: list[dict], category: str | None = None) -> discord.Embed:
    filtered = [c for c in commands if c["category"] == category] if category else commands
    categories = list(dict.fromkeys(c["category"] for c in filtered))

    embed = create_embed(
        title="Command Help",
        description=(
            "```\n"
            "  ╔══════════════════════════════╗\n"
            "  ║   Utility Platform v1.0      ║\n"
            "  ╚══════════════════════════════╝\n"
            "```\n"
            f"Use `/help <category>` for specific commands\n"
            f"Total Commands: **{len(commands)}**"
        ),
        color=COLORS["accent"],
        timestamp=True,
    )

    for cat in categories:
        cat_cmds = [c for c in filtered if c["category"] == cat]
        value = "\n".join(f"`/{c['name']}` — {c['description']}" for c in cat_cmds) or "No commands"
        embed.add_field(name=f"__**{cat.title()}**__", value=value, inline=False)

    return embed
