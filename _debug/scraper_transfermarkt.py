import requests
from bs4 import BeautifulSoup
import time
import sqlite3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

LIGAS = {
    "SOUTH KOREA - K3 LEAGUE": {
        "slug": "k3-league",
        "id": "K3L",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "WALES - CYMRU PREMIER": {
        "slug": "cymru-premier",
        "id": "WAL1",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "EGYPT - PREMIER LEAGUE": {
        "slug": "egyptian-premier-league",
        "id": "EGY1",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "KAZAKHSTAN - PREMIER LIGA": {
        "slug": "premier-liga",
        "id": "KAS1",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "IRAN - AZADEGAN LEAGUE": {
        "slug": "azadegan-league",
        "id": "IRN2",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "BRAZIL - SERIE B": {
        "slug": "serie-b",
        "id": "BRA2",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "GEORGIA - EROVNULI LIGA": {
        "slug": "erovnuli-liga",
        "id": "GEO1",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "GEORGIA - PIRVELI LIGA": {
        "slug": "pirveli-liga",
        "id": "GEO2",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    },
    "USA - USL CHAMPIONSHIP": {
        "slug": "usl-championship",
        "id": "USL",
        "temporadas": [2021, 2022, 2023, 2024, 2025, 2026]
    }
}

def scrape_tabla(slug, competition_id, saison_id):
    url = f"https://www.transfermarkt.es/{slug}/tabelle/wettbewerb/{competition_id}?saison_id={saison_id}"
    print(f"    URL: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        print(f"    Status: {resp.status_code}, Length: {len(resp.text)}")
    except Exception as e:
        print(f"  Error HTTP {saison_id}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="items")
    if not table:
        print(f"  No se encontro tabla para saison_id={saison_id}")
        return []

    equipos = []
    rows = table.find_all("tr")

    for row in rows:
        tds = row.find_all("td")
        # Columnas: 0=pos, 1=logo(vacio), 2=equipo, 3=PJ, 4=G, 5=E, 6=P, 7=goles, 8=DG, 9=pts
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
            goles_partes = goles_text.split(":")
            gf = int(goles_partes[0].strip()) if len(goles_partes) > 0 else 0
            gc = int(goles_partes[1].strip()) if len(goles_partes) > 1 else 0

            pts = int(tds[9].get_text(strip=True))
            draw_pct = round(100 * e / pj, 1) if pj > 0 else 0

            equipos.append({
                "pos": pos, "equipo": equipo, "pj": pj, "g": g, "e": e, "p": p,
                "gf": gf, "gc": gc, "dg": gf - gc, "pts": pts, "draw_pct": draw_pct
            })
        except (ValueError, IndexError):
            continue

    return equipos

def guardar_en_bd(liga, temporada, equipos):
    conn = sqlite3.connect("empates.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS standings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liga TEXT NOT NULL,
            temporada INTEGER NOT NULL,
            equipo TEXT NOT NULL,
            pj INTEGER, g INTEGER, e INTEGER, p INTEGER,
            gf INTEGER, gc INTEGER, dg INTEGER,
            pts INTEGER, draw_pct REAL
        )
    """)

    for eq in equipos:
        cursor.execute("""
            INSERT OR REPLACE INTO standings
            (liga, temporada, equipo, pj, g, e, p, gf, gc, dg, pts, draw_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (liga, temporada, eq["equipo"], eq["pj"], eq["g"], eq["e"], eq["p"],
              eq["gf"], eq["gc"], eq["dg"], eq["pts"], eq["draw_pct"]))

    conn.commit()
    conn.close()

def scrape_todas_las_ligas():
    resultados = {}
    for liga, info in LIGAS.items():
        print(f"\n=== {liga} ===")
        liga_resultados = []
        for anno in info["temporadas"]:
            print(f"Scrapeando temporada {anno}...")
            equipos = scrape_tabla(info["slug"], info["id"], anno)
            print(f"  -> {len(equipos)} equipos encontrados")
            if equipos:
                guardar_en_bd(liga, anno, equipos)
                liga_resultados.append({"temporada": anno, "equipos": equipos})
            time.sleep(3)
        resultados[liga] = liga_resultados
    return resultados

def mostrar_analisis_draws(resultados):
    for liga, temporadas in resultados.items():
        print(f"\n{'='*60}")
        print(f"  {liga}")
        print(f"{'='*60}")

        stats_equipos = {}
        for temp in temporadas:
            for eq in temp["equipos"]:
                nom = eq["equipo"]
                if nom not in stats_equipos:
                    stats_equipos[nom] = {"pj": 0, "e": 0}
                stats_equipos[nom]["pj"] += eq["pj"]
                stats_equipos[nom]["e"] += eq["e"]

        ranking = sorted(stats_equipos.items(),
                        key=lambda x: x[1]["e"]/max(x[1]["pj"], 1), reverse=True)

        print(f"{'Equipo':<35} {'PJ':<8} {'E':<8} {'%E':<8}")
        print("-" * 59)
        for eq, data in ranking:
            pct = round(100 * data["e"] / data["pj"], 1)
            print(f"{eq:<35} {data['pj']:<8} {data['e']:<8} {pct:<8}")

if __name__ == "__main__":
    resultados = scrape_todas_las_ligas()
    mostrar_analisis_draws(resultados)
