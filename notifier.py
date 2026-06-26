import asyncio
from telegram import Bot
from telegram.error import TelegramError

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

async def enviar_mensaje(texto):
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "poner_aqui_tu_token":
        print("Token de Telegram no configurado. Edita el archivo .env")
        return False

    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=texto)
        print("OK - Mensaje enviado a Telegram")
        return True
    except TelegramError as e:
        print(f"Error al enviar mensaje: {e}")
        return False

def enviar(texto):
    asyncio.run(enviar_mensaje(texto))
