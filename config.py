from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

UMBRAL_EMPATE = 35
HISTORIAL_DIAS = 7
INTERVALO_ALERTA = 120
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "0"))

BETSSON_LIGAS = {
    "ARGENTINA - PRIMERA NACIONAL": "argentina/argentina-primera-nacional",
    "ARGENTINA - PRIMERA B METROPOLITANA": "argentina/argentina-primera-b-metropolitana",
    "BRAZIL - SERIE B": "brasil/serie-b",
    "BRAZIL - SERIE C": "brasil/serie-c",
    "SOUTH KOREA - K3 LEAGUE": "corea-del-sur/corea-del-sur-liga-k3",
}

BETSSON_BASE = "https://www.betsson.pe/es/apuestas-deportivas/futbol"
