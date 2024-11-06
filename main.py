from flask import Flask, Response, request
from disnake import Webhook, Embed, Guild
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


jsondata = {
    "version": 1,
    "application_id": "1234560123453231555",
    "type": 1,
    "event": {
        "type": "APPLICATION_AUTHORIZED",
        "timestamp": "2024-10-18T14:42:53.064834",
        "data": {
            "integration_type": 1,
            "scopes": [
                "applications.commands"
            ],
            "guild": {
                "id": "197038439483310086",
                "name": "Discord Testers",
                "icon": "f64c482b807da4f539cff778d174971c",
                "description": "The official place to report Discord Bugs!",
                "splash": None,
                "discovery_splash": None,
                "features": [
                    "ANIMATED_ICON",
                    "VERIFIED",
                    "NEWS",
                    "VANITY_URL",
                    "DISCOVERABLE",
                    "MORE_EMOJI",
                    "INVITE_SPLASH",
                    "BANNER",
                    "COMMUNITY"
                ],
                "emojis": [],
                "banner": "9b6439a7de04f1d26af92f84ac9e1e4a",
                "owner_id": "73193882359173120",
                "application_id": None,
                "region": None,
                "afk_channel_id": None,
                "afk_timeout": 300,
                "system_channel_id": None,
                "widget_enabled": True,
                "widget_channel_id": None,
                "verification_level": 3,
                "roles": [],
                "default_message_notifications": 1,
                "mfa_level": 1,
                "explicit_content_filter": 2,
                "max_presences": 40000,
                "max_members": 250000,
                "vanity_url_code": "discord-testers",
                "premium_tier": 3,
                "premium_subscription_count": 33,
                "system_channel_flags": 0,
                "preferred_locale": "en-US",
                "rules_channel_id": "441688182833020939",
                "public_updates_channel_id": "281283303326089216",
                "safety_alerts_channel_id": "281283303326089216"
            }
    }
}
}


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
    logger.debug(f"Verifying signature for {data}")
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
        data = request.json["event"]["data"]['guild']
        print(request.json)
        try:
            guildID = data['id']
            guildName = data["name"]
            guildIcon = _from_guild_icon(guildID,data['icon'])['url']
            embed = Embed(title="Đã thêm vào máy chủ mới")
            embed.set_thumbnail(url=guildIcon)
            embed.description = f"Tên máy chủ: {guildName}\n" \
                                f"ID: {guildID}\n"
            await send_webhook({"embed": embed})
        except Exception as e:
            logger.error(e)
        finally:
            return Response(status=204)

@app.get("/keep_alive")
def keep_alive():
    return "Hello World!"


app.run(port=80, host="0.0.0.0")