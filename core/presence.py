import asyncio
import aiohttp
from utils.logger import logger


class PresenceGateway:
    def __init__(self):
        self.presence_cache = {}
        self.session = None
        self.ws = None
        self.sequence = None
        self.heartbeat_task = None
        self.connected = False
        self.token = None
        self.guild_ids = set()

    async def start(self, token: str):
        self.token = token
        self.session = aiohttp.ClientSession()
        asyncio.create_task(self._connect())
        asyncio.create_task(self._poll_presences())

    async def _poll_presences(self):
        """Poll presence via REST API as fallback."""
        while True:
            try:
                if self.session and self.token:
                    headers = {"Authorization": self.token}
                    for gid in list(self.guild_ids):
                        try:
                            async with self.session.get(
                                f"https://discord.com/api/v10/guilds/{gid}/members?limit=1000",
                                headers=headers,
                            ) as resp:
                                if resp.status == 200:
                                    members = await resp.json()
                                    for m in members:
                                        uid = m.get("user", {}).get("id")
                                        if not uid:
                                            continue
                                        status = m.get("status", "offline")
                                        client_status = m.get("client_status", {})
                                        self.presence_cache[uid] = {
                                            "status": status,
                                            "desktop": client_status.get("desktop", "offline"),
                                            "mobile": client_status.get("mobile", "offline"),
                                            "web": client_status.get("web", "offline"),
                                            "activities": m.get("activities", []),
                                        }
                                elif resp.status == 429:
                                    data = await resp.json()
                                    wait = data.get("retry_after", 5)
                                    logger.warning(f"Rate limited, waiting {wait}s")
                                    await asyncio.sleep(wait)
                        except Exception as e:
                            logger.error(f"REST poll error for {gid}: {e}")
            except Exception as e:
                logger.error(f"Poll loop error: {e}")

            await asyncio.sleep(30)

    async def _connect(self):
        retry = 1
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://discord.com/api/v10/gateway") as resp:
                        data = await resp.json()
                        gateway_url = data["url"]

                    self.ws = await session.ws_connect(
                        f"{gateway_url}?v=10&encoding=json",
                    )

                    hello = await self.ws.receive_json()
                    heartbeat_interval = hello["d"]["heartbeat_interval"]
                    self.heartbeat_task = asyncio.create_task(self._heartbeat(heartbeat_interval))

                    identify = {
                        "op": 2,
                        "d": {
                            "token": self.token,
                            "intents": 0,
                            "properties": {
                                "os": "windows",
                                "browser": "Discord Client",
                                "device": "",
                            },
                            "presence": {
                                "status": "online",
                                "since": 0,
                                "activities": [],
                                "afk": False,
                            },
                        },
                    }
                    await self.ws.send_json(identify)
                    self.connected = True
                    retry = 1
                    logger.success("Presence gateway connected")

                    async for msg in self.ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await self._handle(data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break

            except Exception as e:
                logger.error(f"Presence gateway error: {e}")
            finally:
                self.connected = False
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()

            await asyncio.sleep(min(retry * 5, 60))
            retry += 1

    async def _heartbeat(self, interval):
        while True:
            await asyncio.sleep(interval / 1000)
            try:
                if self.ws and not self.ws.closed:
                    await self.ws.send_json({"op": 1, "d": self.sequence})
            except Exception:
                break

    async def _subscribe_guild(self, guild_id: str):
        if not self.ws or self.ws.closed:
            return
        subscribe = {
            "op": 14,
            "d": {
                "guild_id": guild_id,
                "typing": True,
                "activities": True,
                "status": True,
                "users": [],
            },
        }
        await self.ws.send_json(subscribe)

    async def _handle(self, data):
        import json as _json

        op = data.get("op")
        event = data.get("t")
        d = data.get("d")

        if op == 0:
            seq = data.get("s")
            if seq is not None:
                self.sequence = seq

            if event == "PRESENCE_UPDATE":
                user_id = d.get("user", {}).get("id")
                if user_id:
                    client_status = d.get("client_status", {})
                    self.presence_cache[user_id] = {
                        "status": d.get("status", "offline"),
                        "desktop": client_status.get("desktop", "offline"),
                        "mobile": client_status.get("mobile", "offline"),
                        "web": client_status.get("web", "offline"),
                        "activities": d.get("activities", []),
                    }
                    logger.info(f"WS Presence: {user_id} -> {d.get('status')}")

            elif event == "READY":
                guilds = d.get("guilds", [])
                logger.info(f"READY: {len(guilds)} guilds")
                for g in guilds:
                    gid = g.get("id")
                    self.guild_ids.add(gid)
                    await self._subscribe_guild(gid)

            elif event == "GUILD_CREATE":
                gid = d.get("id")
                if gid not in self.guild_ids:
                    self.guild_ids.add(gid)
                    await self._subscribe_guild(gid)

        elif op == 10:
            heartbeat_interval = d.get("heartbeat_interval", 41250)
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            self.heartbeat_task = asyncio.create_task(self._heartbeat(heartbeat_interval))

    def get_presence(self, user_id: int) -> dict | None:
        return self.presence_cache.get(str(user_id))


import json
presence_gateway = PresenceGateway()