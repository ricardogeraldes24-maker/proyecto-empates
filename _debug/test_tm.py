import sys
sys.path.insert(0, '.')
from scraper_transfermarkt import scrape_tabla, guardar_en_bd
equipos = scrape_tabla("k3-league", "K3L", 2026)
print(f"Total equipos encontrados: {len(equipos)}")
for eq in equipos[:5]:
    print(f"  #{eq['pos']} {eq['equipo']:<35} {eq['pj']} PJ {eq['e']} E {eq['draw_pct']}%")
if equipos:
    guardar_en_bd("SOUTH KOREA - K3 LEAGUE", 2026, equipos)
    print("Guardado en BD")
