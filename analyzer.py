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
    "KAZAKHSTAN - PREMIER LEAGUE": "KAZAKHSTAN - PREMIER LIGA",
}

def _normalizar_liga(name):
    return LIGA_ALIAS.get(name, name)

def _tm_liga(name):
    return _normalizar_liga(name)

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

def _liga_avg_goals(liga_nombre):
    rows = ejecutar("""
        SELECT ROUND(2.0 * SUM(gf) / NULLIF(SUM(pj), 0), 2)
        FROM standings
        WHERE liga = ?
    """, (liga_nombre,))
    if rows and rows[0][0] is not None and rows[0][0] > 0:
        return rows[0][0]
    rows = ejecutar("""
        SELECT AVG(goles) FROM (
            SELECT CAST(SUBSTR(resultado, 1, INSTR(resultado, '-')-1) AS INTEGER) +
                   CAST(SUBSTR(resultado, INSTR(resultado, '-')+1) AS INTEGER) as goles
            FROM partidos
            WHERE liga LIKE ? AND resultado IS NOT NULL AND resultado != '-' AND resultado LIKE '%-%'
        )
    """, (f"%{liga_nombre[:30]}%",))
    if rows and rows[0][0] is not None:
        return round(rows[0][0], 2)
    return None

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

MAX_PARTIDOS = 20
MAX_LIGAS = 5

def _hora_min(hora):
    if not hora or hora == "??:??":
        return (99, 99)
    try:
        parts = hora.split(":")
        return (int(parts[0]), int(parts[1]))
    except:
        return (99, 99)

def _grupo_hora(hora):
    h, _ = _hora_min(hora)
    if h == 99:
        return 3
    if h < 6:
        return 0
    if h < 12:
        return 1
    if h < 18:
        return 2
    return 3

_NOMBRES_GRUPO = ["Madrugada", "Mañana", "Tarde", "Noche"]

def generar_reporte():
    lineas = []
    hoy = datetime.now()
    fecha_str = hoy.strftime("%d/%m/%Y")
    lineas.append(f"<b>PARTIDOS DEL DIA {fecha_str}</b>")
    lineas.append("")

    today = hoy.strftime("%Y-%m-%d")
    top_ligas = draw_rate_por_liga_tm()
    top_nombres = set(l["liga"] for l in top_ligas[:MAX_LIGAS])

    rows = ejecutar("""
        SELECT fecha, hora, liga, local, visitante, pct_empate
        FROM partidos
        WHERE fecha = ? AND pct_empate >= ?
          AND (resultado IS NULL OR resultado = '-' OR resultado = '')
        ORDER BY pct_empate DESC
    """, (today, UMBRAL_EMPATE - 10))

    if not rows:
        rows = ejecutar("""
            SELECT fecha, hora, liga, local, visitante, pct_empate
            FROM partidos
            WHERE pct_empate >= ?
              AND (resultado IS NULL OR resultado = '-' OR resultado = '')
            ORDER BY pct_empate DESC
        """, (UMBRAL_EMPATE - 10,))

    filtrados = [p for p in rows if _normalizar_liga(p[2]) in top_nombres]
    if filtrados:
        partidos = sorted(filtrados, key=lambda p: (_hora_min(p[1]), -p[5]))[:MAX_PARTIDOS]
    else:
        partidos = sorted(rows, key=lambda p: (_hora_min(p[1]), -p[5]))[:MAX_PARTIDOS]

    if partidos:
        grupo_act = -1
        for p in partidos:
            fecha = p[0]
            hora = p[1] if p[1] else "??:??"
            liga = p[2][:25]
            local = p[3]
            visitante = p[4]
            pct = p[5]

            liga_norm = _normalizar_liga(p[2])
            avg_liga = _liga_avg_goals(liga_norm)

            g = _grupo_hora(hora)
            if g != grupo_act:
                grupo_act = g
                lineas.append(f"-- {_NOMBRES_GRUPO[g]} --")

            extra = ""
            if avg_liga:
                ok = "OK" if avg_liga < 2.5 else "ALTO"
                extra = f" <i>[{avg_liga}g {ok}]</i>"

            lineas.append(f"<b>{pct}%</b> {hora}  {liga}{extra}")
            lineas.append(f"  {local} vs {visitante}")
    else:
        lineas.append("  (sin partidos proximamente)")

    lineas.append("")
    lineas.append("<b>TOP LIGAS EMPARDORAS</b>")
    top_ligas = draw_rate_por_liga_tm()
    for l in top_ligas[:MAX_LIGAS]:
        avg = _liga_avg_goals(l["liga"])
        g_str = f"g{avg}" if avg else "g?"
        lineas.append(f"  <b>{l['draw_pct']}%</b>  {l['liga'][:35]:<35} <i>{g_str}</i>")

    lineas.append("")
    lineas.append(f"Reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

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
