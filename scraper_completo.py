import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

from db import conectar, guardar_standings, ejecutar

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

LIGAS = {
    "SOUTH KOREA - K3 LEAGUE":           {"slug": "k3-league",                "id": "K3L"},
    "FINLAND - VEIKKAUSLIIGA":           {"slug": "veikkausliiga",           "id": "FI1"},
    "ARGENTINA - PRIMERA B METROPOLITANA": {"slug": "primera-b-metropolitana", "id": "URL3"},
    "SWEDEN - SUPERETTAN":               {"slug": "superettan",              "id": "SE2"},
    "ICELAND - BESTA DEILDIN":           {"slug": "besta-deild",             "id": "IS1"},
    "ARGENTINA - PRIMERA NACIONAL":      {"slug": "primera-nacional",        "id": "ARG2"},
    "NORWAY - 1. DIVISION":              {"slug": "1-division",              "id": "NO2"},
    "WALES - CYMRU PREMIER":             {"slug": "cymru-premier",           "id": "WAL1"},
    "EGYPT - PREMIER LEAGUE":            {"slug": "egyptian-premier-league", "id": "EGY1"},
    "KAZAKHSTAN - PREMIER LIGA":         {"slug": "premier-liga",            "id": "KAS1"},
    "IRAN - AZADEGAN LEAGUE":            {"slug": "azadegan-league",          "id": "IRN2"},
    "BRAZIL - SERIE B":                  {"slug": "serie-b",                 "id": "BRA2"},
    "GEORGIA - EROVNULI LIGA":           {"slug": "erovnuli-liga",           "id": "GEO1"},
    "GEORGIA - PIRVELI LIGA":            {"slug": "pirveli-liga",            "id": "GEO2"},
    "USA - USL CHAMPIONSHIP":            {"slug": "usl-championship",        "id": "USL"},
    "MOROCCO - BOTOLA PRO":              {"slug": "botola-pro-inwi",         "id": "MAR1"},
    "LATVIA - VIRSLIGA":                 {"slug": "virsliga",                "id": "LET1"},
}

TEMPORADAS = [2021, 2022, 2023, 2024, 2025, 2026]

def scrape_tabla(slug, competition_id, saison_id):
    url = f"https://www.transfermarkt.es/{slug}/tabelle/wettbewerb/{competition_id}?saison_id={saison_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="items")
    if not table:
        return []

    equipos = []
    rows = table.find_all("tr")
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 10:
            continue

        pos_text = tds[0].get_text(strip=True)
        if not pos_text.isdigit():
            continue

        equipo = tds[2].get_text(strip=True)
        if not equipo:
            continue

        try:
            pos = int(pos_text)
            pj = int(tds[3].get_text(strip=True))
            g = int(tds[4].get_text(strip=True))
            e = int(tds[5].get_text(strip=True))
            p = int(tds[6].get_text(strip=True))

            goles_text = tds[7].get_text(strip=True)
            partes = goles_text.split(":")
            gf = int(partes[0].strip()) if len(partes) > 0 else 0
            gc = int(partes[1].strip()) if len(partes) > 1 else 0
            pts = int(tds[9].get_text(strip=True))
            draw_pct = round(100 * e / pj, 1) if pj > 0 else 0

            equipos.append({
                "pos": pos, "equipo": equipo, "pj": pj, "g": g, "e": e, "p": p,
                "gf": gf, "gc": gc, "dg": gf - gc, "pts": pts, "draw_pct": draw_pct
            })
        except (ValueError, IndexError):
            continue

    return equipos

def scrapear_todo():
    for liga, info in LIGAS.items():
        print(f"\n--- {liga} ---")
        for anno in TEMPORADAS:
            equipos = scrape_tabla(info["slug"], info["id"], anno)
            if equipos:
                print(f"  {anno}: {len(equipos)} equipos")
                guardar_standings(liga, anno, equipos)
            else:
                print(f"  {anno}: sin datos")
            time.sleep(2.5)

def generar_reporte_ligas():
    rows = ejecutar("""
        SELECT liga,
               SUM(pj) as total_pj,
               SUM(e) as total_e,
               ROUND(100.0 * SUM(e) / SUM(pj), 1) as draw_pct,
               COUNT(DISTINCT equipo) as n_equipos,
               COUNT(DISTINCT temporada) as n_temporadas
        FROM standings
        GROUP BY liga
        ORDER BY draw_pct DESC
    """)

    print("\n" + "=" * 80)
    print("  REPORTE GLOBAL - LIGAS CON MAS EMPATES")
    print("=" * 80)
    print(f"\n{'Liga':<40} {'PJ':<8} {'E':<8} {'%E':<8} {'Equipos':<8} {'Temp':<6}")
    print("-" * 78)
    for l in rows:
        print(f"{l[0]:<40} {l[1]:<8} {l[2]:<8} {l[3]:<8} {l[4]:<8} {l[5]:<6}")

    print("\n" + "=" * 80)
    print("  TOP 5 EQUIPOS EMPARDADORES POR LIGA")
    print("=" * 80)

    for liga_name in LIGAS:
        equipos = ejecutar("""
            SELECT equipo,
                   SUM(pj) as total_pj,
                   SUM(e) as total_e,
                   CASE WHEN SUM(pj) > 0 THEN ROUND(100.0 * SUM(e) / SUM(pj), 1) ELSE 0 END as draw_pct,
                   COUNT(DISTINCT temporada) as temps
            FROM standings
            WHERE liga = ?
            GROUP BY equipo
            HAVING SUM(pj) >= 10
            ORDER BY draw_pct DESC
            LIMIT 5
        """, (liga_name,))
        if equipos:
            print(f"\n{liga_name}:")
            for eq in equipos:
                print(f"  {eq[0]:<35} {eq[3]}% ({eq[2]}/{eq[1]}) en {eq[4]} temporadas")

def reporte_partidos_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")

    partidos = ejecutar("""
        SELECT fecha, liga, local, visitante, pct_empate
        FROM partidos
        WHERE fecha = ? AND pct_empate >= 25
          AND (resultado IS NULL OR resultado = '-' OR resultado = '')
        ORDER BY pct_empate DESC
    """, (hoy,))

    if not partidos:
        partidos = ejecutar("""
            SELECT fecha, liga, local, visitante, pct_empate
            FROM partidos
            WHERE pct_empate >= 25
              AND (resultado IS NULL OR resultado = '-' OR resultado = '')
            ORDER BY pct_empate DESC
            LIMIT 10
        """)

    print(f"\n{'='*80}")
    print(f"  PARTIDOS CON ALTA PROBABILIDAD DE EMPATE")
    print(f"{'='*80}")
    print(f"\n{'Fecha':<12} {'Liga':<30} {'Local':<25} {'Visitante':<25} {'%X':<6}")
    print("-" * 98)
    for p in partidos:
        print(f"{p[0]:<12} {p[1][:30]:<30} {p[2][:25]:<25} {p[3][:25]:<25} {p[4]:<6}")

if __name__ == "__main__":
    scrapear_todo()
    generar_reporte_ligas()
    reporte_partidos_hoy()
