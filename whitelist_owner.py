from prisma import Prisma
import asyncio


async def whitelist_owner():
    db = Prisma()
    await db.connect()

    owner_id = "903327749534523452"

    await db.whitelist.upsert(
        where={"discordId": owner_id},
        data={
            "create": {
                "discordId": owner_id,
                "addedBy": owner_id,
                "role": "owner",
                "reason": "Bot owner",
            },
            "update": {},
        },
    )

    try:
        await db.user.upsert(
            where={"discordId": owner_id},
            data={
                "create": {
                    "discordId": owner_id,
                    "username": "owner",
                    "isWhitelisted": True,
                    "isBotOwner": True,
                },
                "update": {
                    "isWhitelisted": True,
                    "isBotOwner": True,
                },
            },
        )
    except Exception:
        pass

    print(f"Owner {owner_id} whitelisted successfully")
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(whitelist_owner())
