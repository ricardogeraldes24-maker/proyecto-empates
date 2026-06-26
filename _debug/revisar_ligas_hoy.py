import sqlite3

conn = sqlite3.connect("empates.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT liga, COUNT(*) as n, ROUND(AVG(pct_empate), 1) as prom, MAX(pct_empate) as max_pct
    FROM partidos
    WHERE fecha = '2026-06-25'
      AND (resultado IS NULL OR resultado = '-' OR resultado = '')
    GROUP BY liga
    ORDER BY COUNT(*) DESC
""")
rows = cursor.fetchall()
conn.close()

print("Ligas con partidos HOY (2026-06-25):")
print()
print(f"{'Liga':<55} {'Partidos':<10} {'Prom %X':<10} {'Max %X':<10}")
print("-" * 85)
for r in rows:
    print(f"{r[0]:<55} {r[1]:<10} {r[2]:<10} {r[3]:<10}")

print()
print("Ligas con max %X >= 30 (buenas candidatas para notificar):")
for r in rows:
    if r[3] >= 30:
        print(f"  {r[0]:<55} max {r[3]}% | {r[1]} partidos hoy")
