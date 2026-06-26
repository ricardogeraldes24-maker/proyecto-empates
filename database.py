from db import conectar, ejecutar, crear_tablas, guardar_partido as gp

crear_tabla = crear_tablas
guardar_partido = gp

def obtener_partidos_sin_resultado():
    rows = ejecutar(
        "SELECT id, fecha, liga, local, visitante FROM partidos WHERE resultado IS NULL OR resultado = '-'"
    )
    return [{"id": r[0], "fecha": r[1], "liga": r[2], "local": r[3], "visitante": r[4]} for r in rows]

def obtener_estadisticas_correlacion():
    rows = ejecutar("""
        SELECT
            CASE
                WHEN pct_empate < 10 THEN '0-10%'
                WHEN pct_empate < 20 THEN '10-20%'
                WHEN pct_empate < 30 THEN '20-30%'
                WHEN pct_empate < 40 THEN '30-40%'
                WHEN pct_empate < 50 THEN '40-50%'
                ELSE '50%+'
            END as rango,
            COUNT(*) as total,
            SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) as empates,
            ROUND(100.0 * SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as precision_pct
        FROM partidos
        WHERE fue_empate IS NOT NULL
        GROUP BY rango
        ORDER BY MIN(pct_empate)
    """)
    return [{"rango": r[0], "total": r[1], "empates": r[2], "precision": r[3]} for r in rows]

def obtener_draw_rate_por_liga():
    rows = ejecutar("""
        SELECT
            liga,
            COUNT(*) as total,
            SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) as empates,
            ROUND(100.0 * SUM(CASE WHEN fue_empate = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as draw_rate,
            ROUND(AVG(pct_empate), 1) as pct_promedio
        FROM partidos
        WHERE fue_empate IS NOT NULL
        GROUP BY liga
        HAVING total >= 3
        ORDER BY draw_rate DESC
    """)
    return [{"liga": r[0], "total": r[1], "empates": r[2], "draw_rate": r[3], "pct_promedio": r[4]} for r in rows]

def obtener_partidos_futuros(umbral):
    import datetime
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    rows = ejecutar("""
        SELECT fecha, hora, liga, local, visitante, pct_empate
        FROM partidos
        WHERE (resultado IS NULL OR resultado = '-' OR resultado = '')
          AND pct_empate >= ?
          AND fecha >= ?
        ORDER BY fecha ASC, pct_empate DESC
    """, (umbral, hoy))
    return [{"fecha": r[0], "hora": r[1], "liga": r[2], "local": r[3], "visitante": r[4], "pct": r[5]} for r in rows]
