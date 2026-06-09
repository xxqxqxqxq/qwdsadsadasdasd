import asyncio
import aiohttp

async def test():
    token = "MTUwNzAxMzYxMTM5Mjk5MTI5Mw.GMHgsk.kgTm_AVg01fctPxriDBDMKZp0OY6vw3lyIf7Pk"
    headers = {"Authorization": token}
    async with aiohttp.ClientSession() as s:
        async with s.get("https://discord.com/api/v10/users/@me", headers=headers) as r:
            data = await r.json()
            print(f"User: {data.get('username')} ({data.get('id')})")
        async with s.get("https://discord.com/api/v10/users/@me/guilds", headers=headers) as r:
            data = await r.json()
            if isinstance(data, list):
                for g in data:
                    print(f"Guild: {g.get('name')} ({g.get('id')})")
            else:
                print(f"Guilds error: {data}")

asyncio.run(test())