import time
import traceback
import json
import os
from datetime import datetime, timedelta

from db import ejecutar as db_ejecutar
from database import crear_tabla, guardar_partido
from scraper import scrape_fecha, scrape_historial
from scraper_completo import LIGAS, TEMPORADAS, scrape_tabla
from db import guardar_standings
from analyzer import generar_reporte, generar_reporte_manana, MAX_LIGAS, draw_rate_por_liga_tm, _normalizar_liga, _liga_avg_goals
from notifier import enviar
from config import UMBRAL_EMPATE, INTERVALO_ALERTA, TIMEZONE_OFFSET

ALERTED_FILE = "alerted.json"

def cargar_alerted():
    try:
        with open(ALERTED_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def guardar_alerted(s):
    try:
        with open(ALERTED_FILE, "w") as f:
            json.dump(list(s), f)
    except Exception as e:
        print(f"Error guardando alerted: {e}")

def limpiar_alerted(s):
    if len(s) > 500:
        nuevos = set(list(s)[-300:])
        s.clear()
        s.update(nuevos)

_TOP5_CACHE = {"ts": 0, "names": set()}

def get_top5_names():
    top = draw_rate_por_liga_tm()
    return set(_normalizar_liga(l["liga"]) for l in top[:MAX_LIGAS])

def top5_cached():
    if time.time() - _TOP5_CACHE["ts"] > 1800:
        _TOP5_CACHE["names"] = get_top5_names()
        _TOP5_CACHE["ts"] = time.time()
    return _TOP5_CACHE["names"]

def scrape_hoy_ayer():
    hoy = datetime.now().strftime("%Y-%m-%d")
    ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    total = 0
    for f in [hoy, ayer]:
        try:
            partidos = scrape_fecha(f)
            for p in partidos:
                guardar_partido(p["id"], p["fecha"], p["hora"], p["liga"], p["local"], p["visitante"], p["pct_empate"], p["resultado"])
            total += len(partidos)
            time.sleep(2)
        except Exception as e:
            print(f"Error scrapeando {f}: {e}")
    return total

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

def ejecutar_ciclo(alerted):
    now = datetime.now()
    hoy = now.strftime("%Y-%m-%d")
    top5 = top5_cached()
    ahora_min = now.hour * 60 + now.minute + TIMEZONE_OFFSET
    reports = []
    try:
        partidos = db_ejecutar("""
            SELECT id, hora, liga, local, visitante, pct_empate
            FROM partidos
            WHERE fecha = ?
              AND (resultado IS NULL OR resultado = '-' OR resultado = '')
              AND hora != '' AND hora != '??:??'
              AND pct_empate >= ?
        """, (hoy, UMBRAL_EMPATE - 10))
        for r in partidos:
            mid = r[0]
            if mid in alerted:
                continue
            hora = r[1]
            liga = r[2]
            local = r[3]
            visit = r[4]
            pct = r[5]
            liga_norm = _normalizar_liga(liga)
            if liga_norm not in top5:
                continue
            try:
                parts = hora.split(":")
                match_min = int(parts[0]) * 60 + int(parts[1])
                diff = match_min - ahora_min
                if 9 <= diff <= 11:
                    msg = (
                        f"<b>{local}</b> vs <b>{visit}</b>\n"
                        f"{liga} - {hora}\n"
                        f"Probabilidad empate: <b>{pct}%</b>"
                    )
                    avg = _liga_avg_goals(liga_norm)
                    if avg:
                        msg += f"\nPromedio goles liga: {avg}"
                    reports.append(("ALERTA 10min", msg))
                    alerted.add(mid)
                    guardar_alerted(alerted)
                    print(f"Alerta 10min: {local} vs {visit} ({hora})")
            except ValueError:
                continue
    except Exception as e:
        print(f"Error alertas: {e}")
    for label, msg in reports:
        try:
            enviar(msg)
        except Exception as e:
            print(f"Error enviando {label}: {e}")

if __name__ == "__main__":
    print("Iniciando...")
    crear_tabla()
    cargar_standings_si_vacio()
    primera_ejecucion()
    ultima_actualizacion = 0
    preview_enviado = ""
    alerted = cargar_alerted()
    print(f"Alertes cargades: {len(alerted)}")
    print(f"*** Mod 24/7 amb alertes 10-min. Revisant cada {INTERVALO_ALERTA}s...")
    while True:
        try:
            now = datetime.now()
            hoy = now.strftime("%Y-%m-%d")
            if time.time() - ultima_actualizacion > 1800:
                try:
                    n = scrape_hoy_ayer()
                    if n:
                        print(f"Dades actualitzades: {n} partits")
                    ultima_actualizacion = time.time()
                except Exception as e:
                    print(f"Error scrape: {e}")
            if now.hour == 20 and preview_enviado != hoy:
                try:
                    preview = generar_reporte_manana()
                    if preview:
                        enviar(preview)
                        print(f"Preview dem. enviat ({len(preview)} chars)")
                    preview_enviado = hoy
                except Exception as e:
                    print(f"Error preview: {e}")
            ejecutar_ciclo(alerted)
            limpiar_alerted(alerted)
            guardar_alerted(alerted)
            time.sleep(INTERVALO_ALERTA)
        except KeyboardInterrupt:
            print("Aturat per l'usuari.")
            break
        except Exception as e:
            print(f"Error en loop principal: {e}")
            traceback.print_exc()
            time.sleep(60)
