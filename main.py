import time
import traceback
from datetime import datetime

from database import crear_tabla, guardar_partido, obtener_partidos_sin_resultado, obtener_partidos_futuros
from scraper import scrape_fecha, scrape_historial
from analyzer import generar_reporte
from notifier import enviar
from config import INTERVALO_HORAS, UMBRAL_EMPATE

def actualizar_resultados_pendientes():
    try:
        pendientes = obtener_partidos_sin_resultado()
        if not pendientes:
            return 0
        fechas = set(p["fecha"] for p in pendientes)
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
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n--- Ciclo {timestamp} ---")

    hoy = datetime.now().strftime("%Y-%m-%d")

    nuevos = []
    try:
        nuevos = scrape_fecha(hoy)
        print(f"Partidos de hoy ({hoy}): {len(nuevos)}")
        for p in nuevos:
            guardar_partido(p["id"], p["fecha"], p["hora"], p["liga"], p["local"], p["visitante"], p["pct_empate"], p["resultado"])
    except Exception as e:
        print(f"Error scraping {hoy}: {e}")

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
