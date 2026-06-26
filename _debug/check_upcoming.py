import sqlite3

conn = sqlite3.connect("empates.db")
c = conn.cursor()

c.execute("SELECT MAX(fecha) FROM partidos WHERE resultado IS NULL OR resultado = '-' OR resultado = ''")
max_fecha = c.fetchone()[0]
print(f"Ultima fecha disponible: {max_fecha}")

c.execute("""
    SELECT fecha, liga, local, visitante, pct_empate
    FROM partidos
    WHERE fecha >= '2026-06-25'
      AND (resultado IS NULL OR resultado = '-' OR resultado = '')
      AND pct_empate >= 25
    ORDER BY fecha, pct_empate DESC
    LIMIT 20
""")
rows = c.fetchall()
conn.close()

print(f"\nProximos partidos con >= 25% de empate ({len(rows)} encontrados):")
print()
if rows:
    for r in rows:
        liga_short = r[1][:35]
        print(f"  {r[0]} | {liga_short:<35} | {r[2]:<20} vs {r[3]:<20} | {r[4]}%")
else:
    print("  (no hay partidos proximos - falta scrapear fechas futuras)")
    print()
    print("Esto es normal si Statarea solo muestra partidos del dia actual.")
    print("Cuando corra 24/7, cada ciclo obtendra los partidos del dia.")
