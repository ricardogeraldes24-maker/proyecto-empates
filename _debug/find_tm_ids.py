import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

# Posibles combinaciones slug/id para las ligas que nos interesan
leagues_to_check = [
    # (nombre_liga_statarea, slug_transfermarkt, id_competicion)
    ("FINLAND - VEIKKAUSLIIGA", "veikkausliiga", "FI1"),
    ("FINLAND - VEIKKAUSLIIGA", "fi1", "FI1"),
    ("FINLAND - VEIKKAUSLIIGA", "ersta-liiga", "FI1"),
    
    ("SWEDEN - SUPERETTAN", "superettan", "SE2"),
    ("SWEDEN - SUPERETTAN", "se2", "SE2"),
    
    ("ARGENTINA - PRIMERA NACIONAL", "primera-nacional", "AR2N"),
    ("ARGENTINA - PRIMERA NACIONAL", "ar2n", "AR2N"),
    
    ("NORWAY - 1. DIVISION", "1-division", "NO2"),
    ("NORWAY - 1. DIVISION", "obos-ligaen", "NO2"),
    ("NORWAY - 1. DIVISION", "no2", "NO2"),
    
    ("ICELAND - BESTA DEILDIN", "besta-deild", "ISL"),
    ("ICELAND - BESTA DEILDIN", "isl", "ISL"),
    ("ICELAND - BESTA DEILDIN", "pepsi-deild", "ISL"),
    
    ("USA - USL CHAMPIONSHIP", "usl-championship", "USL"),
    ("USA - USL CHAMPIONSHIP", "usl", "USL"),
    
    ("ARGENTINA - PRIMERA B METROPOLITANA", "primera-b-metropolitana", "ARPN"),
]

print("Buscando IDs de competicion en Transfermarkt...\n")

results = []
for name, slug, cid in leagues_to_check:
    url = f"https://www.transfermarkt.es/{slug}/tabelle/wettbewerb/{cid}?saison_id=2025"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="items")
        if table and table.find_all("tr") and len(table.find_all("tr")) > 2:
            rows = table.find_all("tr")
            n_teams = 0
            for row in rows:
                tds = row.find_all("td")
                if len(tds) >= 6 and tds[0].get_text(strip=True).isdigit():
                    n_teams += 1
            if n_teams > 0:
                title = soup.title.get_text(strip=True) if soup.title else ""
                results.append((name, slug, cid, n_teams, title, "OK"))
                print(f"✅ {name:40} slug={slug:<25} id={cid:<5} -> {n_teams} equipos | {title[:60]}")
            else:
                print(f"❌ {name:40} slug={slug:<25} id={cid:<5} -> tabla vacia")
        else:
            print(f"❌ {name:40} slug={slug:<25} id={cid:<5} -> sin tabla")
    except Exception as e:
        print(f"❌ {name:40} slug={slug:<25} id={cid:<5} -> error: {str(e)[:40]}")

print("\n\n=== COMBINACIONES QUE FUNCIONARON ===")
for r in results:
    print(f"  \"{r[0]}\": {{\"slug\": \"{r[1]}\", \"id\": \"{r[2]}\"}},")
