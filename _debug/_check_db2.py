import sqlite3, os, pathlib
os.chdir(pathlib.Path(__file__).parent)
conn = sqlite3.connect("empates.db")
c = conn.cursor()

print("=== LEAGUES IN standings ===")
c.execute("SELECT liga, COUNT(DISTINCT temporada) as temps, COUNT(DISTINCT equipo) as teams, SUM(pj) as total_matches, SUM(e) as total_draws FROM standings GROUP BY liga ORDER BY liga")
for row in c.fetchall():
    print(f"  {row[0]:<45} temps={row[1]} teams={row[2]} matches={row[3]} draws={row[4]}")

print()
print("=== LEAGUES IN partidos (Statarea) ===")
c.execute("SELECT liga, COUNT(*) as n FROM partidos GROUP BY liga ORDER BY COUNT(*) DESC LIMIT 20")
for row in c.fetchall():
    print(f"  {row[0]:<55} {row[1]} matches")

print()
print("=== DISTINCT FECHAS in partidos ===")
c.execute("SELECT fecha, COUNT(*) FROM partidos GROUP BY fecha ORDER BY fecha")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} matches")

print()
print("=== UPCOMING matches (no result) with >=25% draw prob ===")
from datetime import datetime
hoy = datetime.now().strftime("%Y-%m-%d")
c.execute("SELECT fecha, hora, liga, local, visitante, pct_empate FROM partidos WHERE (resultado IS NULL OR resultado='-' OR resultado='') AND fecha >= ? AND pct_empate >= 25 ORDER BY fecha, pct_empate DESC LIMIT 10", (hoy,))
rows = c.fetchall()
if rows:
    for r in rows:
        print(f"  {r[0]} {r[1]} | {r[2][:35]:<35} | {r[3]:<20} vs {r[4]:<20} | {r[5]}%")
else:
    print("  (none - need to scrape future dates)")

conn.close()
