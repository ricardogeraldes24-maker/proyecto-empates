import sqlite3
from datetime import datetime

conn = sqlite3.connect("empates.db")
cursor = conn.cursor()

LIGAS_NOMBRES = [
    "SOUTH KOREA - K3 LEAGUE",
    "FINLAND - VEIKKAUSLIIGA",
    "ARGENTINA - PRIMERA B",
    "SWEDEN - SUPERETTAN",
    "ICELAND - BESTA DEILDIN",
    "ARGENTINA - PRIMERA NACIONAL",
    "NORWAY - 1. DIVISION",
]

print("=" * 80)
print("  REPORTE GLOBAL - EMPATES POR LIGA (Transfermarkt 2021-2026)")
print("=" * 80)

cursor.execute("""
    SELECT liga,
           SUM(pj) as total_pj,
           SUM(e) as total_e,
           ROUND(100.0 * SUM(e) / NULLIF(SUM(pj), 0), 1) as draw_pct,
           COUNT(DISTINCT equipo) as n_equipos,
           COUNT(DISTINCT temporada) as n_temporadas
    FROM standings
    GROUP BY liga
    ORDER BY draw_pct DESC
""")
rows = cursor.fetchall()
print(f"\n{'Liga':<40} {'PJ':<8} {'E':<8} {'%E':<8} {'Equipos':<8} {'Temp':<6}")
print("-" * 78)
for r in rows:
    print(f"{r[0]:<40} {r[1]:<8} {r[2]:<8} {r[3]:<8} {r[4]:<8} {r[5]:<6}")

print("\n" + "=" * 80)
print("  EQUIPOS CON MAS EMPATES POR LIGA")
print("=" * 80)

for liga in LIGAS_NOMBRES:
    cursor.execute("""
        SELECT equipo,
               SUM(pj) as total_pj,
               SUM(e) as total_e,
               ROUND(100.0 * SUM(e) / NULLIF(SUM(pj), 0), 1) as draw_pct,
               COUNT(DISTINCT temporada) as temps
        FROM standings
        WHERE liga = ?
        GROUP BY equipo
        HAVING SUM(pj) >= 15
        ORDER BY draw_pct DESC
        LIMIT 5
    """, (liga,))
    equipos = cursor.fetchall()
    if equipos:
        print(f"\n{liga}:")
        print(f"{'Equipo':<35} {'PJ':<6} {'E':<5} {'%E':<8} {'Temp':<5}")
        print("-" * 59)
        for eq in equipos:
            print(f"{eq[0]:<35} {eq[1]:<6} {eq[2]:<5} {eq[3]:<8} {eq[4]:<5}")

print("\n" + "=" * 80)
print("  PARTIDOS PROXIMOS CON ALTA PROBABILIDAD DE EMPATE")
print("=" * 80)

hoy = datetime.now().strftime("%Y-%m-%d")
cursor.execute("""
    SELECT fecha, liga, local, visitante, pct_empate
    FROM partidos
    WHERE fecha >= ? AND pct_empate >= 25
      AND (resultado IS NULL OR resultado = '-' OR resultado = '')
    ORDER BY pct_empate DESC
    LIMIT 20
""", (hoy,))
partidos = cursor.fetchall()

if partidos:
    print(f"\n{'Fecha':<12} {'Liga':<30} {'Local':<22} {'Visitante':<22} {'%X':<6}")
    print("-" * 92)
    for p in partidos:
        liga_short = p[1][:28] if len(p[1]) > 28 else p[1]
        print(f"{p[0]:<12} {liga_short:<30} {p[2][:22]:<22} {p[3][:22]:<22} {p[4]:<6}")
else:
    print("\nNo hay partidos proximos con >=25% de empate")

conn.close()
