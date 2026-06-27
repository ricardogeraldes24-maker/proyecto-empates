import time
import traceback
from datetime import datetime

from db import ejecutar as db_ejecutar
from database import crear_tabla, guardar_partido, obtener_partidos_sin_resultado, obtener_partidos_futuros
from scraper import scrape_fecha, scrape_historial
from scraper_completo import LIGAS, TEMPORADAS, scrape_tabla
from db import guardar_standings
from analyzer import generar_reporte
from notifier import enviar
from config import INTERVALO_HORAS, UMBRAL_EMPATE

def actualizar_resultados_pendientes():
    from datetime import timedelta
    try:
        pendientes = obtener_partidos_sin_resultado()
        if not pendientes:
            return 0
        hoy = datetime.now().strftime("%Y-%m-%d")
        ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        fechas = set(p["fecha"] for p in pendientes if p["fecha"] in (hoy, ayer))
        total = 0
        for f in fechas:
            try:
                actualizados = scrape_fecha(f)
                for p in actualizados:
                    guardar_partido(p["id"], p["fecha"], p["hora"], p["liga"], p["local"], p["visitante"], p["pct_empate"], p["resultado"])
                total += len(actualizados)
                time.sleep(1.5)
            except Exception as e:
                print(f"  Error actualizando {f}: {e}")
        return total
    except Exception as e:
        print(f"  Error en actualizar_resultados_pendientes: {e}")
        return 0

def ejecutar_ciclo():
    from datetime import timedelta
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n--- Ciclo {timestamp} ---")

    hoy = datetime.now().strftime("%Y-%m-%d")
    ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    nuevos = []
    try:
        nuevos = scrape_fecha(hoy)
        print(f"Partidos de hoy ({hoy}): {len(nuevos)}")
        for p in nuevos:
            guardar_partido(p["id"], p["fecha"], p["hora"], p["liga"], p["local"], p["visitante"], p["pct_empate"], p["resultado"])
    except Exception as e:
        print(f"Error scraping {hoy}: {e}")

    try:
        ayer_partidos = scrape_fecha(ayer)
        for p in ayer_partidos:
            guardar_partido(p["id"], p["fecha"], p["hora"], p["liga"], p["local"], p["visitante"], p["pct_empate"], p["resultado"])
        print(f"Resultados de ayer ({ayer}): {len(ayer_partidos)}")
    except Exception as e:
        print(f"Error scraping ayer {ayer}: {e}")

    try:
        actualizados = actualizar_resultados_pendientes()
        if actualizados:
            print(f"Resultados actualizados: {actualizados}")
    except Exception as e:
        print(f"Error actualizando resultados: {e}")

    reporte = ""
    try:
        reporte = generar_reporte()
    except Exception as e:
        print(f"Error generando reporte: {e}")
        reporte = f"--- ERROR ---\nError al generar reporte: {e}"

    print(reporte)

    try:
        enviar(reporte)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def cargar_standings_si_vacio():
    try:
        rows = db_ejecutar("SELECT COUNT(*) FROM standings")
        if rows and rows[0][0] > 0:
            print(f"Standings ya cargados: {rows[0][0]} registros")
            return
    except Exception as e:
        print(f"Error verificando standings: {e}")
        return

    print("Cargando standings desde Transfermarkt (primera vez)...")
    total = 0
    for liga, info in LIGAS.items():
        for anno in TEMPORADAS:
            try:
                equipos = scrape_tabla(info["slug"], info["id"], anno)
                if equipos:
                    guardar_standings(liga, anno, equipos)
                    total += len(equipos)
                    print(f"  {liga[:35]:<35} {anno}: {len(equipos)} equipos")
                time.sleep(2.5)
            except Exception as e:
                print(f"  Error en {liga} {anno}: {e}")
                time.sleep(2.5)
    print(f"OK - {total} registros de standings cargados")

def primera_ejecucion():
    hoy = datetime.now().strftime("%Y-%m-%d")

    try:
        partidos_hoy = scrape_fecha(hoy)
        if partidos_hoy:
            print(f"Partidos de hoy ({hoy}): {len(partidos_hoy)}")
            for p in partidos_hoy:
                guardar_partido(p["id"], p["fecha"], p["hora"], p["liga"], p["local"], p["visitante"], p["pct_empate"], p["resultado"])
        else:
            print("No se encontraron partidos para hoy. Scrapeando historial...")
            partidos = scrape_historial()
            for p in partidos:
                guardar_partido(p["id"], p["fecha"], p["hora"], p["liga"], p["local"], p["visitante"], p["pct_empate"], p["resultado"])
            print(f"OK - {len(partidos)} partidos guardados")
    except Exception as e:
        print(f"Error en primera ejecucion: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Inicializando base de datos...")
    crear_tabla()

    cargar_standings_si_vacio()
    primera_ejecucion()
    ejecutar_ciclo()

    print(f"\n*** Modo 24/7 activado. Revisando cada {INTERVALO_HORAS} horas...")
    while True:
        try:
            time.sleep(INTERVALO_HORAS * 3600)
        except KeyboardInterrupt:
            print("\nDetenido por el usuario.")
            break
        except Exception as e:
            print(f"Error en espera: {e}, reintentando en 5 minutos...")
            time.sleep(300)
            continue

        ejecutar_ciclo()
