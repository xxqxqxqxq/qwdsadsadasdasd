import aiohttp
from utils.logger import logger


class UserAPI:
    def __init__(self):
        self.session = None
        self.token = None
        self.ready = False
        self._guild_cache: dict[int, dict] = {}

    async def start(self, token: str):
        self.token = token
        self.session = aiohttp.ClientSession()
        self.ready = True
        # Preload selfbot's guilds
        headers = {"Authorization": self.token}
        try:
            async with self.session.get(
                "https://discord.com/api/v10/users/@me/guilds",
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    guilds = await resp.json()
                    for g in guilds:
                        gid = int(g.get("id", 0))
                        if gid:
                            self._guild_cache[gid] = g
                    logger.success(f"User API: cached {len(guilds)} guilds")
        except Exception:
            pass
        logger.success("User API session ready")

    async def get_user_profile(self, user_id: int):
        if not self.ready:
            return None
        headers = {"Authorization": self.token}
        try:
            async with self.session.get(
                f"https://discord.com/api/v10/users/{user_id}/profile?with_mutual_guilds=true",
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Profile fetch error: {e}")
        return None

    async def get_user(self, user_id: int):
        if not self.ready:
            return None
        headers = {"Authorization": self.token}
        try:
            async with self.session.get(
                f"https://discord.com/api/v10/users/{user_id}",
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None

    async def get_mutual_guilds(self, user_id: int):
        profile = await self.get_user_profile(user_id)
        if not profile or "mutual_guilds" not in profile:
            return []
        return [int(g.get("id")) for g in profile.get("mutual_guilds", []) if g.get("id")]

    async def get_guild_members(self, guild_id: int):
        headers = {"Authorization": self.token}
        try:
            async with self.session.get(
                f"https://discord.com/api/v10/guilds/{guild_id}/members",
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return []

    async def get_guild(self, guild_id: int):
        if not self.ready:
            return None
        try:
            guild_id = int(guild_id)
        except (TypeError, ValueError):
            return None
        return self._guild_cache.get(guild_id)

    async def get_mutual_members_all(self, user_id: int):
        mutual_guilds = await self.get_mutual_guilds(user_id)
        all_members = []
        for guild_id in mutual_guilds:
            members = await self.get_guild_members(guild_id)
            for m in members:
                all_members.append(m["user"])
        return all_members


user_api = UserAPI()