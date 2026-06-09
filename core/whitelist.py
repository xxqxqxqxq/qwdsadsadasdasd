import discord
from config import config
from core.database import db
from utils.logger import logger


class WhitelistManager:
    _instance = None
    _cache: dict[str, dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def is_whitelisted(self, discord_id: str) -> bool:
        if not config.WHITELIST_ENABLED:
            return True

        if discord_id in self._cache:
            return True

        entry = await db.whitelist.find_first(
            where={"discordId": discord_id},
        )
        if entry:
            self._cache[discord_id] = {
                "discordId": entry.discordId,
                "role": entry.role,
            }
            return True

        return False

    async def add_user(self, discord_id: str, added_by: str, reason: str | None = None, role: str = "vip", permissions: list[str] | None = None):
        entry = await db.whitelist.upsert(
            where={"discordId": discord_id},
            data={
                "create": {
                    "discordId": discord_id,
                    "addedBy": added_by,
                    "reason": reason,
                    "role": role,
                    "permissions": permissions or [],
                },
                "update": {
                    "addedBy": added_by,
                    "reason": reason,
                    "role": role,
                    "permissions": permissions or [],
                },
            },
            select={"id": True, "discordId": True, "addedBy": True, "role": True, "permissions": True},
        )

        self._cache[discord_id] = {
            "id": entry.id,
            "discordId": entry.discordId,
            "addedBy": entry.addedBy,
            "role": entry.role,
            "permissions": entry.permissions,
        }

        try:
            await db.user.update(
                where={"discordId": discord_id},
                data={"isWhitelisted": True, "whitelistedBy": added_by},
            )
        except Exception:
            pass

        logger.info(f"Whitelisted user {discord_id}")

    async def get_role(self, discord_id: str) -> str:
        if discord_id in self._cache:
            return self._cache[discord_id].get("role", "vip")

        entry = await db.whitelist.find_first(
            where={"discordId": discord_id},
        )
        return entry.role if entry else "vip"

    async def remove_user(self, discord_id: str) -> str | None:
        entry = await db.whitelist.find_first(
            where={"discordId": discord_id},
        )
        reason = entry.reason if entry else None
        await db.whitelist.delete_many(where={"discordId": discord_id})
        self._cache.pop(discord_id, None)
        try:
            await db.user.update_many(
                where={"discordId": discord_id},
                data={"isWhitelisted": False},
            )
        except Exception:
            pass
        logger.info(f"Unwhitelisted user {discord_id}")
        return reason

    async def load(self):
        try:
            entries = await db.whitelist.find_many()
            self._cache.clear()
            for e in entries:
                self._cache[e.discordId] = {
                    "id": e.id,
                    "discordId": e.discordId,
                    "addedBy": e.addedBy,
                    "reason": e.reason,
                    "role": e.role,
                    "permissions": e.permissions,
                }
            logger.info(f"Loaded {len(entries)} whitelist entries")
        except Exception as e:
            logger.error("Failed to load whitelist", e)

    async def refresh(self):
        await self.load()


whitelist_manager = WhitelistManager()
