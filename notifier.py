import asyncio
from telegram import Bot
from telegram.error import TelegramError

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

MAX_LEN = 4096

async def enviar_mensaje(texto):
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "poner_aqui_tu_token":
        print("Token de Telegram no configurado. Edita el archivo .env")
        return False

    bot = Bot(token=TELEGRAM_TOKEN)
    partes = [texto[i:i+MAX_LEN] for i in range(0, len(texto), MAX_LEN)]
    ok = True
    for i, parte in enumerate(partes):
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=parte, parse_mode='HTML')
            print(f"OK - Mensaje {i+1}/{len(partes)} enviado a Telegram")
        except TelegramError as e:
            print(f"Error al enviar mensaje {i+1}/{len(partes)}: {e}")
            ok = False
    return ok

def enviar(texto):
    asyncio.run(enviar_mensaje(texto))
