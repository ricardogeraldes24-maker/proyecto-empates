import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

url = "https://www.transfermarkt.es/k3-league/tabelle/wettbewerb/K3L?saison_id=2026"
resp = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(resp.text, "html.parser")

table = soup.find("table", class_="items")
print(f"Table found: {table is not None}")

if table:
    rows = table.find_all("tr")
    print(f"Total rows: {len(rows)}")
    
    for i, row in enumerate(rows):
        tds = row.find_all("td")
        ncols = len(tds)
        first_cols = [td.get_text(strip=True)[:20] for td in tds[:5]]
        
        row_class = row.get("class", "")
        
        # Try to find team name
        if ncols >= 2:
            name_cell = tds[1]
            link = name_cell.find("a")
            team_name = link.get_text(strip=True) if link else "(no link)"
        else:
            team_name = "(no cells)"
        
        print(f"  Row {i}: cls={row_class} ncols={ncols} first={first_cols} team={team_name}")
        
        if i >= 15:
            break

# Also try to find the items table in a different way
import re
items_tables = soup.find_all("table", class_=re.compile("items|Items|ITEMS"))
print(f"\nTables matching 'items' regex: {len(items_tables)}")
for t in items_tables:
    print(f"  class: {t.get('class')}, rows: {len(t.find_all('tr'))}")

# Try with None class
tables = soup.find_all("table")
for i, t in enumerate(tables):
    cls = t.get("class", [])
    if any("item" in str(c).lower() for c in cls if c):
        print(f"  Table {i}: class={cls}")
