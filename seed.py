import json
from prisma import Prisma
import asyncio


async def seed():
    db = Prisma()
    await db.connect()

    print("Seeding database...")

    await db.globalsetting.upsert(
        where={"key": "app_name"},
        data={
            "create": {"key": "app_name", "value": json.dumps("Utility Platform")},
            "update": {},
        },
    )

    await db.globalsetting.upsert(
        where={"key": "app_version"},
        data={
            "create": {"key": "app_version", "value": json.dumps("1.0.0")},
            "update": {},
        },
    )

    await db.globalsetting.upsert(
        where={"key": "whitelist_enabled"},
        data={
            "create": {"key": "whitelist_enabled", "value": json.dumps(True)},
            "update": {},
        },
    )

    print("Seed complete.")
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(seed())
