from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

UMBRAL_EMPATE = 35
HISTORIAL_DIAS = 7
INTERVALO_ALERTA = 120
TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "0"))

BETSSON_BASE = "https://www.betsson.pe/es/apuestas-deportivas/futbol"

BETSSON_LIGAS = {
    "ARGENTINA - PRIMERA NACIONAL": "https://www.betsson.pe/es/apuestas-deportivas/futbol/argentina/argentina-primera-nacional",
    "ARGENTINA - PRIMERA B": "https://www.betsson.pe/es/apuestas-deportivas/futbol/argentina/argentina-primera-b-metropolitana",
    "BRAZIL - SERIE B": "https://www.betsson.pe/es/apuestas-deportivas/futbol/brasil/serie-b",
    "BRAZIL - SERIE C": "https://www.betsson.pe/es/apuestas-deportivas/futbol/brasil/serie-c",
    "MOROCCO - BOTOLA PRO": "https://www.betsson.pe/es/apuestas-deportivas/futbol/marruecos/marruecos-botala-pro-1",
    "KAZAKHSTAN - PREMIER LIGA": "https://www.betsson.pe/es/apuestas-deportivas/futbol/kazajstan/premier-league",
    "SOUTH KOREA - K3 LEAGUE": "https://www.betsson.pe/es/apuestas-deportivas/futbol/corea-del-sur/corea-del-sur-liga-k3",
    "FINLAND - VEIKKAUSLIIGA": "https://www.betsson.pe/es/apuestas-deportivas/futbol/finlandia/veikkausliiga-finlandia",
    "SWEDEN - SUPERETTAN": "https://www.betsson.pe/es/apuestas-deportivas/futbol/suecia/superettan-suecia",
    "ICELAND - BESTA DEILDIN": "https://www.betsson.pe/es/apuestas-deportivas/futbol/islandia/islandia-urvalsdeild",
    "NORWAY - 1. DIVISION": "https://www.betsson.pe/es/apuestas-deportivas/futbol/noruega/obos-ligaen",
    "USA - USL CHAMPIONSHIP": "https://www.betsson.pe/es/apuestas-deportivas/futbol/usa/eeuu-campeonato-usl",
    "LATVIA - VIRSLIGA": "https://www.betsson.pe/es/apuestas-deportivas/futbol/letonia/virsliga-letonia",
    "REP. OF IRELAND - PREMIER DIVISION": "https://www.betsson.pe/es/apuestas-deportivas/futbol/irlanda/league-of-ireland-premier",
}
