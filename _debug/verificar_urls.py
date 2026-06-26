import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

urls = [
    ("FINLAND - VEIKKAUSLIIGA", "https://www.transfermarkt.es/veikkausliiga/tabelle/wettbewerb/FI1?saison_id=2024"),
    ("ARGENTINA - PRIMERA B METROPOLITANA", "https://www.transfermarkt.es/primera-b-metropolitana/tabelle/wettbewerb/URL3"),
    ("SWEDEN - SUPERETTAN", "https://www.transfermarkt.es/superettan/tabelle/wettbewerb/SE2?saison_id=2024"),
    ("ICELAND - BESTA DEILDIN", "https://www.transfermarkt.es/besta-deild/tabelle/wettbewerb/IS1?saison_id=2024"),
    ("ARGENTINA - PRIMERA NACIONAL", "https://www.transfermarkt.es/primera-nacional/tabelle/wettbewerb/ARG2"),
]

for nombre, url in urls:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="items")
        if table:
            rows = table.find_all("tr")
            n_teams = sum(1 for r in rows if r.find_all("td") and r.find_all("td")[0].get_text(strip=True).isdigit())
            title = soup.title.get_text(strip=True)[:80] if soup.title else ""
            print(f"  OK | {nombre:<40} | {n_teams} equipos | {url[:70]}")
            print(f"      | {title}")
        else:
            print(f"FAIL | {nombre:<40} | sin tabla    | {url[:70]}")
    except Exception as e:
        print(f"ERROR | {nombre:<40} | {str(e)[:40]} | {url[:70]}")
