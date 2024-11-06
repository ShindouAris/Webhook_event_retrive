from flask import Flask, Response, request
from disnake import Webhook, Embed
from aiohttp import ClientSession
from os import environ
from dotenv import load_dotenv
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from typing import TypedDict
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
load_dotenv()
webhookURL = environ.get('WEBHOOK_URL')
APPLICATION_PUBLIC_KEY = environ.get('APPLICATION_PUBLIC_KEY')

class clsFormat(TypedDict):
    url: str
    key: str
    animated: bool


BASE = "https://cdn.discordapp.com"

def _from_guild_icon(guild_id: int, icon_hash: str):
    animated = icon_hash.startswith("a_")
    format = "gif" if animated else "png"
    return clsFormat(
        url=f"{BASE}/icons/{guild_id}/{icon_hash}.{format}?size=1024",
        key=icon_hash,
        animated=animated,
    )

def verify_signature(data) -> bool:
    verifyKey = VerifyKey(bytes.fromhex(APPLICATION_PUBLIC_KEY))
    logger.debug(f"Verifying signature")
    signature = data.headers["X-Signature-Ed25519"]
    timestamp = data.headers["X-Signature-Timestamp"]
    body = data.data.decode("utf-8")
    try:
        verifyKey.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False

async def send_webhook(data: dict):
    async with ClientSession() as session:
        webhook = Webhook.from_url(webhookURL, session=session)
        await webhook.send(**data)

@app.post("/endpoint/webhook")
async def recive_ping():
    verify = verify_signature(request)
    if not verify:
        return Response('invalid request signature', status=401)
    logger.info(f"Received webhook request")

    if request.json["type"] == 0:
        logger.info(request.json)
        return Response(status=204)

    if request.json["event"]["type"] == "APPLICATION_AUTHORIZED":
        data = request.json['event']['data']['guild']
        try:
            guildID = data['id']
            guildName = data["name"]
            embed = Embed(title="Đã thêm vào máy chủ mới")
            if data["icon"] is not None:
                guildIcon = _from_guild_icon(guildID,data['icon'])['url']
                embed.set_thumbnail(url=guildIcon)
            embed.description = f"Tên máy chủ: {guildName}\n" \
                                f"ID: {guildID}\n" \
                                f"Người auth vào guild: {request.json['event'].get('user').get('global_name')}\n"
            await send_webhook({"embed": embed})
        except Exception as e:
            logger.error(e)
        finally:
            return Response(status=204)

@app.get("/keep_alive")
def keep_alive():
    return "Hello World!"