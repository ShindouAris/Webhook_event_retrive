from flask import Flask, Response, request, render_template
from disnake import Webhook, Embed
from aiohttp import ClientSession
from os import environ
from dotenv import load_dotenv
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
load_dotenv()
webhookURL = environ.get('WEBHOOK_URL')
APPLICATION_PUBLIC_KEY = environ.get('APPLICATION_PUBLIC_KEY')


BASE = "https://cdn.discordapp.com"


def from_guild_icon(guild_id: int, icon_hash: str) -> str:
    animated = icon_hash.startswith("a_")
    format = "gif" if animated else "png"
    return f"{BASE}/icons/{guild_id}/{icon_hash}.{format}?size=1024"


def verify_signature(data) -> bool:
    verifyKey = VerifyKey(bytes.fromhex(APPLICATION_PUBLIC_KEY))
    logger.debug(f"Verifying signature")
    try:
        signature = data.headers["X-Signature-Ed25519"]
        timestamp = data.headers["X-Signature-Timestamp"]
    except KeyError:
        return False
    body = data.data.decode("utf-8")
    try:
        verifyKey.verify(f'{timestamp}{body}'.encode(),
                         bytes.fromhex(signature))
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
        try:
            embed = Embed()
            try:
                embed.description = "### __Đã được thêm vào máy chủ mới !__\n" \
                                    f"```{request.json['event']['data']['guild']['name']}```" \
                                    f"ID: {request.json['event']['data']['guild']['id']}\n" \
                                    f"Người dùng phê duyệt ứng dụng này: ```{request.json['event']['data']['user']['global_name']} - {request.json['event']['data']['user']['id']}```"
                embed.set_image(url="https://i.ibb.co/7SgZSDj/miku.gif")
                embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/1119870633468235817/a_95bf7aff063e2205da18293f375e165d.gif?size=1024", text="Kamisato Ayaka")
                embed.set_thumbnail(url=from_guild_icon(request.json["event"]['data']['guild']['id'], request.json["event"]['data']['guild']['icon']))
            except KeyError:
                embed.description = "### __Đã được thêm vào máy chủ mới !__"
                embed.set_image(url="https://i.ibb.co/7SgZSDj/miku.gif")
                embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/1119870633468235817/a_95bf7aff063e2205da18293f375e165d.gif?size=1024", text="Kamisato Ayaka")
            finally:
                await send_webhook({"embed": embed})
        except Exception as e:
            logger.error(e)
        finally:
            return Response(status=204)


@app.get("/keep_alive")
def keep_alive():
    return "Hello World!"


@app.get("/")
def response():
    return "Konichiwa!"

@app.errorhandler(404)
def handle_error(e):
    app.template_folder = "htmls"
    return render_template("notfound.html"), 404

@app.errorhandler(405)
def meth_notallowed(e):
    app.template_folder = "htmls"
    return render_template("methodnotallowed.html"), 405

@app.errorhandler(500)
def servererror(e):
    app.template_folder = "htmls"
    return render_template("servererror.html"), 500

if __name__ == "__main__":
    app.run(port=80, host="0.0.0.0")
