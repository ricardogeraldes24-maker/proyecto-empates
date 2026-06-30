import urllib.parse
from datetime import datetime, timedelta

from db import conectar, ejecutar
from config import UMBRAL_EMPATE, BETSSON_LIGAS, BETSSON_BASE, BETSSON_VERIFIED

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
    "BRAZIL - SERIE C": "BRA3",
    "REP. OF IRELAND - PREMIER DIVISION": "IRL1",
    "FINLAND - YKKOSLIIGA": "FI2",
}

LIGA_ALIAS = {
    "ARGENTINA - PRIMERA B METROPOLITANA": "ARGENTINA - PRIMERA B",
    "KAZAKHSTAN - PREMIER LEAGUE": "KAZAKHSTAN - PREMIER LIGA",
    "BRAZIL - BRASILEIRO SERIE C": "BRAZIL - SERIE C",
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
        SELECT resultado FROM partidos
        WHERE liga LIKE ? AND resultado IS NOT NULL
          AND resultado != '-' AND resultado LIKE '%-%'
    """, (f"%{liga_nombre[:30]}%",))
    if rows:
        goles = []
        for r in rows:
            try:
                partes = r[0].split("-")
                goles.append(int(partes[0]) + int(partes[1]))
            except (ValueError, IndexError):
                pass
        if goles:
            return round(sum(goles) / len(goles), 2)
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
MIN_PARTIDOS_POR_LIGA = 3

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

def obtener_umbral_dinamico(fecha=None, minimo=MAX_PARTIDOS):
    umbral = UMBRAL_EMPATE
    while umbral >= 15:
        if fecha:
            rows = ejecutar("""
                SELECT COUNT(*) FROM partidos
                WHERE fecha = ? AND pct_empate >= ?
                  AND (resultado IS NULL OR resultado = '-' OR resultado = '')
            """, (fecha, umbral))
        else:
            rows = ejecutar("""
                SELECT COUNT(*) FROM partidos
                WHERE pct_empate >= ?
                  AND (resultado IS NULL OR resultado = '-' OR resultado = '')
            """, (umbral,))
        if rows and rows[0][0] >= minimo:
            return umbral
        umbral -= 5
    return 15

def top_ligas_ponderado(max_ligas=MAX_LIGAS, betsson_only=True):
    hoy = datetime.now().strftime("%Y-%m-%d")
    manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    hist_rows = ejecutar("""
        SELECT liga, SUM(pj) as total_pj, SUM(e) as total_e,
               ROUND(100.0 * SUM(e) / NULLIF(SUM(pj), 0), 1) as draw_pct,
               ROUND(2.0 * SUM(gf) / NULLIF(SUM(pj), 0), 2) as avg_goals
        FROM standings
        GROUP BY liga
        HAVING SUM(pj) >= 50
    """)

    upcoming = ejecutar("""
        SELECT liga, COUNT(*) as cnt, ROUND(AVG(pct_empate), 1) as avg_x
        FROM partidos
        WHERE fecha IN (?, ?)
          AND (resultado IS NULL OR resultado = '-' OR resultado = '')
          AND pct_empate >= 20
        GROUP BY liga
    """, (hoy, manana))

    upcoming_dict = {}
    for r in upcoming:
        norm = _normalizar_liga(r[0])
        upcoming_dict[norm] = {"cnt": r[1], "avg_x": r[2]}

    scores = []
    for r in hist_rows:
        name = r[0]
        norm = _normalizar_liga(name)
        if betsson_only and norm not in BETSSON_VERIFIED:
            continue
        draw_pct = r[3]
        avg_goals = r[4] if r[4] else 3.0

        up = upcoming_dict.get(norm, {"cnt": 0, "avg_x": 0})
        avail = up["cnt"]
        avg_x = up["avg_x"]

        draw_score = draw_pct * 2
        goals_score = max(0, (2.5 - avg_goals) * 10)
        statarea_score = avg_x * 0.8
        avail_score = min(avail, 10) * 2

        score = draw_score + goals_score + statarea_score + avail_score

        scores.append({
            "liga": name, "draw_pct": draw_pct, "avg_goals": avg_goals,
            "avg_statarea_x": avg_x, "available": avail, "score": round(score, 1)
        })

    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:max_ligas]

def top_ligas_con_stats(ponderado=True, betsson_only=True):
    if ponderado:
        return top_ligas_ponderado(betsson_only=betsson_only)
    return draw_rate_por_liga_tm()

def generar_stats_aciertos(dias=7, umbral=25):
    desde = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    rows = ejecutar("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) as aciertos,
               ROUND(100.0 * SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) as pct
        FROM partidos
        WHERE fue_empate IS NOT NULL AND fecha >= ? AND pct_empate >= ?
    """, (desde, umbral))

    rows_liga = ejecutar("""
        SELECT liga, COUNT(*) as total,
               SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) as aciertos,
               ROUND(100.0 * SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) as pct
        FROM partidos
        WHERE fue_empate IS NOT NULL AND fecha >= ? AND pct_empate >= ?
        GROUP BY liga HAVING COUNT(*) >= 3
        ORDER BY pct DESC
    """, (desde, umbral))

    lineas = []
    hoy = datetime.now()
    fecha_str = hoy.strftime("%d/%m/%Y")
    lineas.append(f"<b>ESTADISTICAS {dias} DIAS ({fecha_str})</b>")
    lineas.append("")

    r = rows[0] if rows else (0, 0, 0)
    lineas.append(f"Total: <b>{r[1]}/{r[0]}</b>  <b>{r[2]}%</b> aciertos (umbral >= {umbral}%)")
    lineas.append("")

    if rows_liga:
        lineas.append("<b>Por liga:</b>")
        for l in rows_liga[:MAX_LIGAS]:
            lineas.append(f"  <b>{l[3]}%</b>  {l[1]}/{l[0]}  {l[2]}")
    else:
        lineas.append("(sin datos suficientes aun)")

    return "\n".join(lineas)

def generar_reporte(ponderado=True, betsson_only=True):
    lineas = []
    hoy = datetime.now()
    fecha_str = hoy.strftime("%d/%m/%Y")
    lineas.append(f"<b>PARTIDOS DEL DIA {fecha_str}</b>")
    lineas.append("")

    today = hoy.strftime("%Y-%m-%d")
    top = top_ligas_con_stats(ponderado, betsson_only=betsson_only)
    top_nombres = set(_normalizar_liga(l["liga"]) for l in top[:MAX_LIGAS])

    umbral = obtener_umbral_dinamico(today)

    rows = ejecutar("""
        SELECT fecha, hora, liga, local, visitante, pct_empate
        FROM partidos
        WHERE fecha = ? AND pct_empate >= ?
          AND (resultado IS NULL OR resultado = '-' OR resultado = '')
        ORDER BY pct_empate DESC
    """, (today, umbral))

    if not rows:
        rows = ejecutar("""
            SELECT fecha, hora, liga, local, visitante, pct_empate
            FROM partidos
            WHERE pct_empate >= ?
              AND (resultado IS NULL OR resultado = '-' OR resultado = '')
            ORDER BY pct_empate DESC
        """, (umbral,))

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
            url = BETSSON_LIGAS.get(liga_norm)
            if url:
                lineas.append(f"  <a href='{url}'>Betsson</a>")
            else:
                q = urllib.parse.quote(f"{local} {visitante}")
                lineas.append(f"  <a href='{BETSSON_BASE}/search?query={q}'>Buscar Betsson</a>")
    else:
        lineas.append("  (sin partidos proximamente)")

    lineas.append("")
    lineas.append(f"<i>Umbral usado: {umbral}%</i>")
    lineas.append("")
    lineas.append("<b>TOP LIGAS EMPARDORAS</b>")
    for l in top[:MAX_LIGAS]:
        avg = _liga_avg_goals(l["liga"])
        g_str = f"g{avg}" if avg else "g?"
        lineas.append(f"  <b>{l['score']}</b>  {l['liga'][:35]:<35}  <i>{l['draw_pct']}% {g_str}</i>")

    lineas.append("")
    lineas.append(f"Reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    return "\n".join(lineas)

def generar_reporte_manana(ponderado=True, betsson_only=True):
    lineas = []
    manana = datetime.now() + timedelta(days=1)
    fecha_str = manana.strftime("%d/%m/%Y")
    manana_str = manana.strftime("%Y-%m-%d")
    lineas.append(f"<b>PARTIDOS DE MAÑANA {fecha_str}</b>")
    lineas.append("")

    top = top_ligas_con_stats(ponderado, betsson_only=betsson_only)
    top_nombres = set(_normalizar_liga(l["liga"]) for l in top[:MAX_LIGAS])

    umbral = obtener_umbral_dinamico(manana_str)

    rows = ejecutar("""
        SELECT fecha, hora, liga, local, visitante, pct_empate
        FROM partidos
        WHERE fecha = ? AND pct_empate >= ?
          AND (resultado IS NULL OR resultado = '-' OR resultado = '')
        ORDER BY pct_empate DESC
    """, (manana_str, umbral))

    filtrados = [p for p in rows if _normalizar_liga(p[2]) in top_nombres]
    if filtrados:
        partidos = sorted(filtrados, key=lambda p: (_hora_min(p[1]), -p[5]))[:MAX_PARTIDOS]
    else:
        partidos = sorted(rows, key=lambda p: (_hora_min(p[1]), -p[5]))[:MAX_PARTIDOS]

    if partidos:
        grupo_act = -1
        for p in partidos:
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
            url = BETSSON_LIGAS.get(liga_norm)
            if url:
                lineas.append(f"  <a href='{url}'>Betsson</a>")
            else:
                q = urllib.parse.quote(f"{local} {visitante}")
                lineas.append(f"  <a href='{BETSSON_BASE}/search?query={q}'>Buscar Betsson</a>")

        total_filt = len(filtrados)
        if total_filt:
            lineas.append("")
            lineas.append(f"Total: {total_filt} partidos en top ligas")
    else:
        lineas.append("  (sin partidos manana)")

    lineas.append("")
    lineas.append(f"<i>Umbral usado: {umbral}%</i>")
    lineas.append("")
    lineas.append("<b>TOP LIGAS PONDERADAS</b>")
    for l in top[:MAX_LIGAS]:
        avg = _liga_avg_goals(l["liga"])
        g_str = f"g{avg}" if avg else "g?"
        lineas.append(f"  <b>{l['score']}</b>  {l['liga'][:35]:<35}  <i>{l['draw_pct']}% {g_str}</i>")

    lineas.append("")
    lineas.append(f"Preview: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    return "\n".join(lineas) if partidos else None

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
    print(generar_reporte(betsson_only=False))
    print()
    print(generar_stats_aciertos())
