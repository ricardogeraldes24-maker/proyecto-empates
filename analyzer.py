from datetime import datetime

from db import conectar, ejecutar
from config import UMBRAL_EMPATE

LIGAS_TM = {
    "SOUTH KOREA - K3 LEAGUE": "K3L",
    "FINLAND - VEIKKAUSLIIGA": "FI1",
    "ARGENTINA - PRIMERA B METROPOLITANA": "URL3",
    "SWEDEN - SUPERETTAN": "SE2",
    "ICELAND - BESTA DEILDIN": "IS1",
    "ARGENTINA - PRIMERA NACIONAL": "ARG2",
    "NORWAY - 1. DIVISION": "NO2",
    "WALES - CYMRU PREMIER": "WAL1",
    "EGYPT - PREMIER LEAGUE": "EGY1",
    "KAZAKHSTAN - PREMIER LIGA": "KAS1",
    "IRAN - AZADEGAN LEAGUE": "IRN2",
    "BRAZIL - SERIE B": "BRA2",
    "GEORGIA - EROVNULI LIGA": "GEO1",
    "GEORGIA - PIRVELI LIGA": "GEO2",
    "USA - USL CHAMPIONSHIP": "USL",
    "MOROCCO - BOTOLA PRO": "MAR1",
    "LATVIA - VIRSLIGA": "LET1",
}

LIGA_ALIAS = {
    "ARGENTINA - PRIMERA B METROPOLITANA": "ARGENTINA - PRIMERA B",
}

def _tm_liga(name):
    return LIGA_ALIAS.get(name, name)

def draw_rate_por_liga_tm():
    rows = ejecutar("""
        SELECT liga,
               SUM(pj) as total_pj,
               SUM(e) as total_e,
               ROUND(100.0 * SUM(e) / NULLIF(SUM(pj), 0), 1) as draw_pct
        FROM standings
        GROUP BY liga
        ORDER BY draw_pct DESC
    """)
    return [{"liga": r[0], "total": r[1], "empates": r[2], "draw_pct": r[3]} for r in rows]

def datos_equipo(equipo_nombre):
    for liga_tm in LIGAS_TM:
        rows = ejecutar("""
            SELECT liga, ROUND(100.0 * SUM(e) / NULLIF(SUM(pj), 0), 1), SUM(pj), SUM(e)
            FROM standings
            WHERE equipo LIKE ?
            HAVING SUM(pj) >= 5
        """, (f"%{equipo_nombre[:20]}%",))
        if rows and rows[0][1]:
            r = rows[0]
            return {"liga": r[0], "draw_pct": r[1], "pj": r[2], "e": r[3]}
    return None

def generar_reporte():
    lineas = []
    hoy = datetime.now()
    fecha_str = hoy.strftime("%d/%m/%Y")
    lineas.append(f"--- PARTIDOS DEL DIA {fecha_str} ---")
    lineas.append("")

    today = hoy.strftime("%Y-%m-%d")
    partidos = ejecutar("""
        SELECT fecha, hora, liga, local, visitante, pct_empate
        FROM partidos
        WHERE fecha = ? AND pct_empate >= ?
          AND (resultado IS NULL OR resultado = '-' OR resultado = '')
        ORDER BY hora ASC, pct_empate DESC
    """, (today, UMBRAL_EMPATE - 10))

    if not partidos:
        partidos = ejecutar("""
            SELECT fecha, hora, liga, local, visitante, pct_empate
            FROM partidos
            WHERE pct_empate >= ?
              AND (resultado IS NULL OR resultado = '-' OR resultado = '')
            ORDER BY fecha ASC, hora ASC
            LIMIT 15
        """, (UMBRAL_EMPATE - 10,))

    if partidos:
        for p in partidos:
            fecha = p[0]
            hora = p[1] if p[1] else "??:??"
            liga = p[2][:25]
            local = p[3]
            visitante = p[4]
            pct = p[5]

            hist_local = datos_equipo(local)
            hist_visit = datos_equipo(visitante)

            hist_str = ""
            if hist_local and hist_visit:
                hist_str = f" [L:{hist_local['draw_pct']}% V:{hist_visit['draw_pct']}%]"
            elif hist_local:
                hist_str = f" [L:{hist_local['draw_pct']}%]"
            elif hist_visit:
                hist_str = f" [V:{hist_visit['draw_pct']}%]"

            bar = _barra(pct)
            lineas.append(f"  {fecha} {hora}  {liga}  {bar} {pct}%{hist_str}")
            lineas.append(f"     {local} vs {visitante}")
            lineas.append("")
    else:
        lineas.append("  (sin partidos proximamente)")
        lineas.append("")

    lineas.append("--- LIGAS CON MAS EMPATES (Transfermarkt 2021-2026) ---")
    lineas.append("")
    top_ligas = draw_rate_por_liga_tm()
    for l in top_ligas[:10]:
        bar = _barra(l["draw_pct"])
        lineas.append(f"  {l['liga'][:40]:<40} {bar} {l['draw_pct']}% ({l['empates']}/{l['total']})")

    lineas.append("")
    lineas.append(f"Reporte generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    return "\n".join(lineas)

def _barra(pct):
    if pct >= 40:
        return "####"
    elif pct >= 30:
        return "###"
    elif pct >= 20:
        return "##"
    elif pct >= 10:
        return "#"
    else:
        return " "

if __name__ == "__main__":
    print(generar_reporte())
