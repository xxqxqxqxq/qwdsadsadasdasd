from prisma import Prisma
from utils.logger import logger
import json

db = Prisma()


async def connect_database():
    try:
        await db.connect()
        logger.success("Database connected successfully")
    except Exception as e:
        logger.error("Failed to connect to database", e)
        raise SystemExit(1)


async def disconnect_database():
    try:
        await db.disconnect()
        logger.info("Database disconnected")
    except Exception as e:
        logger.error("Error disconnecting database", e)


async def ensure_user(discord_id: str, username: str, display_name: str | None = None, avatar: str | None = None):
    try:
        await db.user.upsert(
            where={"discordId": discord_id},
            data={
                "create": {
                    "discordId": discord_id,
                    "username": username,
                    "displayName": display_name or username,
                    "avatar": avatar,
                },
                "update": {
                    "username": username,
                    "displayName": display_name or username,
                    "avatar": avatar,
                },
            },
        )
    except Exception as e:
        logger.error(f"Failed to ensure user {discord_id}", e)


async def ensure_guild(discord_id: str, name: str, icon: str | None = None, owner_id: str | None = None, member_count: int = 0):
    try:
        await db.guild.upsert(
            where={"discordId": discord_id},
            data={
                "create": {
                    "discordId": discord_id,
                    "name": name,
                    "icon": icon,
                    "ownerId": owner_id,
                    "memberCount": member_count,
                },
                "update": {
                    "name": name,
                    "icon": icon,
                    "ownerId": owner_id,
                    "memberCount": member_count,
                },
            },
        )
    except Exception as e:
        logger.error(f"Failed to ensure guild {discord_id}", e)


async def create_log(
    user_id: str | None = None,
    guild_id: str | None = None,
    log_type: str = "general",
    action: str = "unknown",
    details: dict | None = None,
    severity: str = "info",
):
    try:
        data = {
            "type": log_type,
            "action": action,
            "severity": severity,
        }

        if details:
            data["details"] = json.dumps(details)

        await db.log.create(data=data)
    except Exception as e:
        logger.error("Failed to create log entry", e)
