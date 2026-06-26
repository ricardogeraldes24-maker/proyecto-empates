import sqlite3

conn = sqlite3.connect("empates.db")
cursor = conn.cursor()

# 1. Equipos de K3 League con mas empates historico (de Transfermarkt)
print("=" * 70)
print("  EQUIPOS K3 LEAGUE CON MAS EMPATES (2021-2026, Transfermarkt)")
print("=" * 70)
print()
cursor.execute("""
    SELECT equipo,
           SUM(pj) as total_pj,
           SUM(e) as total_e,
           ROUND(100.0 * SUM(e) / SUM(pj), 1) as draw_pct,
           COUNT(DISTINCT temporada) as temporadas
    FROM standings
    WHERE liga = 'SOUTH KOREA - K3 LEAGUE'
    GROUP BY equipo
    HAVING total_pj >= 10
    ORDER BY draw_pct DESC
""")
rows = cursor.fetchall()
print(f"{'Equipo':<30} {'PJ':<6} {'E':<5} {'%E':<8} {'Temp':<5}")
print("-" * 54)
for r in rows[:10]:
    print(f"{r[0]:<30} {r[1]:<6} {r[2]:<5} {r[3]:<8} {r[4]:<5}")

# 2. Partidos de K3 League con alta prediccion de empate segun Statarea
print()
print("=" * 70)
print("  PARTIDOS K3 LEAGUE CON ALTA PROB. DE EMPATE (Statarea)")
print("=" * 70)
print()
cursor.execute("""
    SELECT fecha, local, visitante, pct_empate, resultado
    FROM partidos
    WHERE (liga LIKE '%K3%' OR liga LIKE '%K3 LEAGUE%')
      AND pct_empate >= 25
    ORDER BY pct_empate DESC
""")
rows = cursor.fetchall()
print(f"{'Fecha':<12} {'Local':<25} {'Visitante':<25} {'%X':<6} {'Resultado':<10}")
print("-" * 78)
for r in rows:
    print(f"{r[0]:<12} {r[1]:<25} {r[2]:<25} {r[3]:<6} {r[4]:<10}")

# 3. Cruce: equipos que mas empatan (standings) vs partidos con alta prediccion (statarea)
print()
print("=" * 70)
print("  CRUCE: equipos con historial de empates + alta prediccion")
print("=" * 70)
print()

# Obtener lista de equipos con mas empates en K3 League
cursor.execute("""
    SELECT DISTINCT equipo
    FROM standings
    WHERE liga = 'SOUTH KOREA - K3 LEAGUE'
      AND 100.0 * e / pj >= 28.0
      AND pj >= 10
""")
equipos_empardadores = set(r[0] for r in cursor.fetchall())

# Partidos de Statarea donde algun equipo esta en la lista
cursor.execute("""
    SELECT fecha, liga, local, visitante, pct_empate, resultado
    FROM partidos
    WHERE liga LIKE '%K3%' OR liga LIKE '%K3 LEAGUE%'
    ORDER BY fecha DESC
""")
partidos = cursor.fetchall()
conn.close()

print(f"Equipos identificados como 'empardadores' (>=28% empates historico):")
for eq in sorted(equipos_empardadores):
    print(f"  - {eq}")
print()
print("Partidos donde juega un equipo empardador:")
print(f"{'Fecha':<12} {'Local':<25} {'Visitante':<25} {'%X':<6} {'Resultado':<10}")
print("-" * 78)
for p in partidos:
    es_empardador = p[1] in equipos_empardadores or p[2] in equipos_empardadores
    if es_empardador:
        print(f"{p[0]:<12} {p[1]:<25} {p[2]:<25} {p[3]:<6} {p[4]:<10}")
