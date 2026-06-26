from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

UMBRAL_EMPATE = 35
HISTORIAL_DIAS = 7
INTERVALO_HORAS = 6
