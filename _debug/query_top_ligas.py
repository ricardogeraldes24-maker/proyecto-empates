import sqlite3

conn = sqlite3.connect("empates.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT liga, COUNT(*) as total,
           SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) as empates,
           ROUND(100.0 * SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as draw_rate
    FROM partidos
    WHERE fue_empate IS NOT NULL
    GROUP BY liga
    HAVING total >= 3
    ORDER BY draw_rate DESC
""")
rows = cursor.fetchall()
conn.close()

print("=== TOP 20 LIGAS CON MAS EMPATES (Statarea) ===")
print()
print(f"{'Liga':<50} {'Partidos':<10} {'Empates':<10} {'%E':<8}")
print("-" * 78)
for r in rows[:20]:
    print(f"{r[0]:<50} {r[1]:<10} {r[2]:<10} {r[3]:<8}")
