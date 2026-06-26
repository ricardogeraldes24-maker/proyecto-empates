import requests
from bs4 import BeautifulSoup
import re

URL = "https://www.statarea.com/standings/competition/South+Korea+-+K3+League+2026%2F2026"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

resp = requests.get(URL, headers=HEADERS, timeout=30)
soup = BeautifulSoup(resp.text, "html.parser")

equipos = []

rows = soup.find_all("div", class_="standingrow")
for row in rows:
    name_div = row.find("div", class_="name")
    if not name_div:
        continue

    equipo = name_div.get_text(strip=True)
    if not equipo:
        continue

    overall = row.find("div", class_="overall")
    common = row.find("div", class_="common")
    common2 = row.find("div", class_="common2")

    if not overall or not common or not common2:
        continue

    pos = common.find("div", class_="pos")
    matches = common.find("div", class_="matches")
    wins = overall.find("div", class_="wins")
    draws = overall.find("div", class_="draws")
    loses = overall.find("div", class_="loses")
    gf = overall.find("div", class_="goals host")
    ga = overall.find("div", class_="goals guest")
    gd = overall.find("div", class_="goaldiff")
    pts = common2.find("div", class_="points")

    if not all([pos, matches, wins, draws, loses, gf, ga, pts]):
        continue

    p = int(pos.get_text(strip=True))
    m = int(matches.get_text(strip=True))
    w = int(wins.get_text(strip=True))
    d = int(draws.get_text(strip=True))
    l = int(loses.get_text(strip=True))
    g_f = int(gf.get_text(strip=True))
    g_a = int(ga.get_text(strip=True))
    g_d = g_f - g_a
    pts_v = int(pts.get_text(strip=True))

    draw_pct = round(100 * d / m, 1) if m > 0 else 0

    equipos.append({
        "pos": p, "equipo": equipo, "pj": m, "g": w, "e": d, "p": l,
        "gf": g_f, "gc": g_a, "dg": g_d, "pts": pts_v, "draw_pct": draw_pct
    })

print(f"\n=== SOUTH KOREA K3 LEAGUE - TABLA DE POSICIONES ===")
print(f"{'#':<3} {'Equipo':<35} {'PJ':<4} {'G':<4} {'E':<4} {'P':<4} {'GF':<4} {'GC':<4} {'DG':<4} {'Pts':<4} {'%E':<6}")
print("=" * 80)
for eq in equipos:
    print(f"{eq['pos']:<3} {eq['equipo']:<35} {eq['pj']:<4} {eq['g']:<4} {eq['e']:<4} {eq['p']:<4} {eq['gf']:<4} {eq['gc']:<4} {eq['dg']:<4} {eq['pts']:<4} {eq['draw_pct']:<6}")

total_d = sum(eq["e"] for eq in equipos)
total_m = sum(eq["pj"] for eq in equipos)
liga_draw_pct = round(100 * total_d / total_m, 1)

print(f"\n=== RESUMEN K3 LEAGUE ===")
print(f"Total de partidos: {total_m}")
print(f"Total de empates: {total_d}")
print(f"Draw rate real de la liga: {liga_draw_pct}%")

top_empates = sorted(equipos, key=lambda x: x["draw_pct"], reverse=True)
print(f"\n=== EQUIPOS CON MAS EMPATES ===")
for eq in top_empates[:5]:
    print(f"  {eq['equipo']:<35} {eq['draw_pct']}% empates ({eq['e']}/{eq['pj']})")
