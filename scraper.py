import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import re
import time

from config import HISTORIAL_DIAS



BASE_URL = "https://www.statarea.com/predictions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _extraer_numero(texto):
    match = re.search(r'\d+', str(texto))
    return int(match.group()) if match else 0

def scrape_fecha(fecha_str):
    url = f"{BASE_URL}/date/{fecha_str}/competition"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Error al obtener {fecha_str}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    partidos = []

    competencias = soup.find_all("div", class_="competition")
    for comp in competencias:
        header = comp.find("div", class_="header")
        if not header:
            continue

        nombre_div = header.find("div", class_="name")
        if not nombre_div:
            continue
        liga = nombre_div.get_text(strip=True)
        if not liga or liga == "Advertisement":
            continue

        matches = comp.find_all("div", class_="match")
        for match in matches:
            match_id = match.get("id", "")
            if not match_id:
                continue

            teams_div = match.find("div", class_="teams")
            if not teams_div:
                continue

            host = teams_div.find("div", class_="hostteam")
            guest = teams_div.find("div", class_="guestteam")
            if not host or not guest:
                continue

            local = host.find("div", class_="name")
            visitante = guest.find("div", class_="name")
            if not local or not visitante:
                continue

            local_nombre = local.get_text(strip=True)
            visitante_nombre = visitante.get_text(strip=True)

            date_div = match.find("div", class_="date")
            hora = date_div.get_text(strip=True) if date_div else ""

            goal_host = host.find("a", class_="goals")
            goal_guest = guest.find("a", class_="goals")
            resultado = "-"
            if goal_host and goal_guest:
                gh = goal_host.get_text(strip=True)
                gg = goal_guest.get_text(strip=True)
                if gh and gg:
                    resultado = f"{gh}-{gg}"

            inforow = match.find("div", class_="inforow")
            pct_empate = 0
            if inforow:
                coefrow = inforow.find("div", class_="coefrow")
                if coefrow:
                    values = coefrow.find_all("div", class_="value")
                    if len(values) >= 2:
                        pct_empate = _extraer_numero(values[1].get_text())

            if local_nombre and visitante_nombre:
                partidos.append({
                    "id": match_id,
                    "fecha": fecha_str,
                    "hora": hora,
                    "liga": liga,
                    "local": local_nombre,
                    "visitante": visitante_nombre,
                    "pct_empate": pct_empate,
                    "resultado": resultado
                })

    return partidos

def scrape_historial():
    hoy = datetime.now()
    todos = []

    for i in range(HISTORIAL_DIAS + 1):
        fecha = hoy - timedelta(days=i)
        fecha_str = fecha.strftime("%Y-%m-%d")
        print(f"Scrapeando {fecha_str}...")
        partidos = scrape_fecha(fecha_str)
        todos.extend(partidos)
        print(f"  -> {len(partidos)} partidos encontrados")
        time.sleep(2)

    return todos

if __name__ == "__main__":
    partidos = scrape_historial()
    print(f"\nTotal: {len(partidos)} partidos")
    for p in partidos[:5]:
        print(f"  {p['fecha']} | {p['liga']} | {p['local']} vs {p['visitante']} | X:{p['pct_empate']}% | {p['resultado']}")
