

from aiohttp import web
import random
import string
from datetime import datetime, timedelta
import requests
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL, CHANNEL_ID, PORT

# Generate a random verification token
def generate_verification_token(length=6):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# Store verification tokens and their expiration times
verification_tokens = {}

# Function to check if a token is valid and not expired using publicearn API
def is_valid_token(token):
    url = 'https://publicearn.com/api/verify_token'
    headers = {
        'Authorization': f'85d2cf5838d6c742c6a855eb514af076ea5c3790',
        'Content-Type': 'application/json'
    }
    data = {
        'token': token
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        # Handle exception (e.g., log error, return False)
        return False

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER
        self.verification_token = None

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        if FORCE_SUB_CHANNEL:
            try:
                link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                    link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                self.LOGGER(__name__).warning(f"Please Double check the FORCE_SUB_CHANNEL value and Make sure Bot is Admin in channel with Invite Users via Link Permission, Current Force Sub Channel Value: {FORCE_SUB_CHANNEL}")
                self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/CodeXBotzSupport for support")
                sys.exit()
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id = db_channel.id, text = "Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {CHANNEL_ID}")
            self.LOGGER(__name__).info("\nBot Stopped. Join for support")
            sys.exit()
        
			
        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/CodeXBotz")
        self.username = usr_bot_me.username
        
        # Start web server
        app = web.Application()
        app.router.add_routes([web.get('/', self.handle_verification)])
        app.router.add_routes([web.post('/', self.handle_message)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()

    async def handle_verification(self, request):
        if not self.verification_token or not is_valid_token(self.verification_token):
            self.verification_token = generate_verification_token()
            verification_tokens[self.verification_token] = datetime.now() + timedelta(hours=24)
            return web.Response(text=f"Here's your verification token: {self.verification_token}\n\nThis token will expire in 24 hours.")
        return web.Response(text="You are already verified.")

    async def handle_message(self, request):
        if not await self.verify_access(request):
            return web.Response(text="Please verify your access by providing the verification token.")
        # Process the message
        # ...

    async def verify_access(self, request):
        token = request.query.get('token')
        return token and is_valid_token(token)

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

# Run the bot
if __name__ == "__main__":
    bot = Bot()
    bot.run()
