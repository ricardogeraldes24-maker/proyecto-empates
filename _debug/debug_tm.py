import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

resp = requests.get("https://www.transfermarkt.es/k3-league/tabelle/wettbewerb/K3L?saison_id=2026", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Length: {len(resp.text)}")

soup = BeautifulSoup(resp.text, "html.parser")

table = soup.find("table", class_="items")
if table:
    rows = table.find_all("tr")
    print(f"Rows found: {len(rows)}")
    for i, row in enumerate(rows[:5]):
        classes = row.get("class", [])
        tds = row.find_all("td")
        texts = [td.get_text(strip=True) for td in tds]
        print(f"  Row {i}: cls={classes} cols={texts[:10]}")
else:
    print("No table with class='items' found")
    tables = soup.find_all("table")
    print(f"All tables: {len(tables)}")
    for i, t in enumerate(tables[:5]):
        cls = t.get("class", "")
        rows = t.find_all("tr")
        print(f"  Table {i}: class={cls} rows={len(rows)}")
        if rows:
            first_cells = rows[0].find_all(["th", "td"])
            print(f"    First row: {[c.get_text(strip=True)[:30] for c in first_cells[:8]]}")

    # Check if there's a responsive-table div
    div = soup.find("div", class_="responsive-table")
    if div:
        print(f"responsive-table div found, tables inside: {len(div.find_all('table'))}")
    else:
        print("No responsive-table div found")

    # Search for any element with "K3" or "tabella" in it
    for el in soup.find_all(["div", "h1", "h2"]):
        text = el.get_text(strip=True)
        if "K3" in text or "Tabelle" in text or "Clasificacion" in text or "standings" in text.lower():
            print(f"Found: {el.name} = {text[:80]}")
