import sqlite3

conn = sqlite3.connect('empates.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT local, visitante, pct_empate, resultado
    FROM partidos
    WHERE liga LIKE '%K3%' OR liga LIKE '%K3 LEAGUE%'
    ORDER BY fecha DESC
""")
rows = cursor.fetchall()
conn.close()

print("Partidos de K3 League en nuestra BD:")
print()
for r in rows:
    local, visitante, pct, resultado = r
    empate_real = False
    if resultado and resultado != "-" and "-" in resultado:
        partes = resultado.split("-")
        empate_real = partes[0].strip() == partes[1].strip()
    etiqueta = "EMPATE" if empate_real else ""
    print(f"  {local:<30} vs {visitante:<30} | X predicho: {pct}% | Resultado: {resultado} {etiqueta} ")

print()
print("CONCLUSION:")
print("Solo tenemos 3 partidos de K3 League en los 7 dias scrapeados.")
print("Eso no alcanza para comparar por equipo.")
print()
print("Los datos reales de la temporada completa (tabla de posiciones):")
print("  1. Mokpo City              60.0% (9/15)")
print("  2. Gyeongju Citizen Fc      46.7% (7/15)")
print("  3. Busan Transportation     40.0% (6/15)")
print("  4. Yangpyeong FC            40.0% (6/15)")
print("  5. Changwon City            33.3% (5/15)")
print()
print("De esos 5 equipos, en nuestros datos solo aparecen:")
print("  - Changwon City (vs Mokpo City) - empate 1-1")
print("  - Yangpyeong FC (vs Yeoju Sejong) - NO empate")
print("  - Mokpo City (vs Changwon City) - empate 1-1")
print()
print("Para una comparacion real necesito:")
print("1. Scrapear la tabla de posiciones de cada liga")
print("2. Cruzarla con las predicciones de Statarea")
print("3. Asi sabremos si Statarea acierta cuando dice que")
print("   ciertos equipos tienen alta probabilidad de empate")
