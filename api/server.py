from fastapi import FastAPI, HTTPException, Depends, Header
from core.database import db
from config import config
from utils.logger import logger
import uvicorn

app = FastAPI(title="Utility Platform API")


async def api_auth(x_api_key: str = Header(None)):
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/stats", dependencies=[Depends(api_auth)])
async def stats():
    users = await db.user.count()
    guilds = await db.guild.count()
    logs = await db.log.count()
    commands = await db.commandstat.count()
    return {"users": users, "guilds": guilds, "logs": logs, "commands": commands}


@app.get("/api/v1/users/{discord_id}", dependencies=[Depends(api_auth)])
async def get_user(discord_id: str):
    user = await db.user.find_unique(where={"discordId": discord_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/v1/whitelist", dependencies=[Depends(api_auth)])
async def get_whitelist():
    return await db.whitelist.find_many()


def start_api():
    if not config.API_ENABLED:
        logger.info("API server is disabled")
        return

    import threading

    def run():
        uvicorn.run(app, host="0.0.0.0", port=config.API_PORT, log_level="info")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    logger.success(f"API server running on port {config.API_PORT}")
