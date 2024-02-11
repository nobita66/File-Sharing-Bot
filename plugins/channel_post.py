import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
import requests

from bot import Bot  # Assuming this is your Pyrogram bot instance
from config import ADMINS, CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode

async def shorten_url(api_key, destination_link, custom_alias):
    url = "https://publicearn.com/api"
    payload = {
        "api": api_key,
        "url": destination_link,
        "alias": custom_alias
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        return response.text  # Assuming the response contains the shortened URL
    except requests.RequestException as e:
        print(f"Failed to shorten URL: {e}")
        return None

@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(['start','users','broadcast','batch','genlink','stats']))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote=True)
    try:
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return

    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    api_key = "85d2cf5838d6c742c6a855eb514af076ea5c3790"
    destination_link = link  # Assuming 'link' contains the previously generated URL
    custom_alias = "CustomAlias"

    short_link = await shorten_url(api_key, destination_link, custom_alias)
    if short_link:
        print(f"Shortened URL: {short_link}")
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={short_link}')]])
        await reply_text.edit(f"<b>Here is your link</b>\n\n{short_link}", reply_markup=reply_markup, disable_web_page_preview=True)
        if not DISABLE_CHANNEL_BUTTON:
            await post_message.edit_reply_markup(reply_markup)
    else:
        await reply_text.edit_text("Failed to shorten URL.")

    if not DISABLE_CHANNEL_BUTTON:
        await post_message.edit_reply_markup(reply_markup)

@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)
        pass

# Start the bot
Bot.run()
