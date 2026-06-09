import asyncio
import aiohttp

async def test():
    token = "MTUwNzAxMzYxMTM5Mjk5MTI5Mw.GMHgsk.kgTm_AVg01fctPxriDBDMKZp0OY6vw3lyIf7Pk"
    headers = {"Authorization": token}
    async with aiohttp.ClientSession() as s:
        async with s.get("https://discord.com/api/v10/users/903327749534523452/profile", headers=headers) as r:
            print(f"Status: {r.status}")
            data = await r.json()
            print(f"Keys: {list(data.keys())}")
            user_data = data.get("user", {})
            print(f"Bio: {user_data.get('bio')}")
            print(f"Pronouns: {user_data.get('pronouns')}")

asyncio.run(test())