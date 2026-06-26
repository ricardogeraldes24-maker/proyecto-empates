import os
import sqlite3

_DB_DIR = os.path.dirname(os.path.abspath(__file__))
_SQLITE_PATH = os.path.join(_DB_DIR, "empates.db")

DATABASE_URL = os.environ.get("DATABASE_URL", "")

USING_POSTGRES = DATABASE_URL.startswith("postgres")

if USING_POSTGRES:
    import psycopg2
    import psycopg2.extras

    def conectar():
        return psycopg2.connect(DATABASE_URL, sslmode="require")
else:
    def conectar():
        return sqlite3.connect(_SQLITE_PATH)

def crear_tablas():
    conn = conectar()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS partidos (
                id          TEXT PRIMARY KEY,
                fecha       TEXT NOT NULL,
                hora        TEXT DEFAULT '',
                liga        TEXT NOT NULL,
                local       TEXT NOT NULL,
                visitante   TEXT NOT NULL,
                pct_empate  INTEGER NOT NULL,
                resultado   TEXT,
                fue_empate  INTEGER,
                created_at  TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS standings (
                id          SERIAL PRIMARY KEY,
                liga        TEXT NOT NULL,
                temporada   INTEGER NOT NULL,
                equipo      TEXT NOT NULL,
                pj          INTEGER,
                g           INTEGER,
                e           INTEGER,
                p           INTEGER,
                gf          INTEGER,
                gc          INTEGER,
                dg          INTEGER,
                pts         INTEGER,
                draw_pct    REAL
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS partidos (
                id          TEXT PRIMARY KEY,
                fecha       TEXT NOT NULL,
                hora        TEXT DEFAULT '',
                liga        TEXT NOT NULL,
                local       TEXT NOT NULL,
                visitante   TEXT NOT NULL,
                pct_empate  INTEGER NOT NULL,
                resultado   TEXT,
                fue_empate  INTEGER,
                created_at  TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS standings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                liga        TEXT NOT NULL,
                temporada   INTEGER NOT NULL,
                equipo      TEXT NOT NULL,
                pj          INTEGER,
                g           INTEGER,
                e           INTEGER,
                p           INTEGER,
                gf          INTEGER,
                gc          INTEGER,
                dg          INTEGER,
                pts         INTEGER,
                draw_pct    REAL
            )
        """)

    conn.commit()
    conn.close()

def guardar_partido(id_partido, fecha, hora, liga, local, visitante, pct_empate, resultado):
    conn = conectar()
    cur = conn.cursor()

    fue_empate = None
    if resultado and resultado != "-":
        partes = resultado.split("-")
        if len(partes) == 2:
            fue_empate = 1 if partes[0].strip() == partes[1].strip() else 0

    import datetime
    now = datetime.datetime.now().isoformat()

    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO partidos (id, fecha, hora, liga, local, visitante, pct_empate, resultado, fue_empate, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                resultado = EXCLUDED.resultado,
                fue_empate = EXCLUDED.fue_empate
        """, (id_partido, fecha, hora, liga, local, visitante, pct_empate, resultado, fue_empate, now))
    else:
        cur.execute("""
            INSERT OR REPLACE INTO partidos
            (id, fecha, hora, liga, local, visitante, pct_empate, resultado, fue_empate, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_partido, fecha, hora, liga, local, visitante, pct_empate, resultado, fue_empate, now))

    conn.commit()
    conn.close()

def guardar_standings(liga, temporada, equipos):
    conn = conectar()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("DELETE FROM standings WHERE liga = %s AND temporada = %s", (liga, temporada))
    else:
        cur.execute("DELETE FROM standings WHERE liga = ? AND temporada = ?", (liga, temporada))

    for eq in equipos:
        if USING_POSTGRES:
            cur.execute("""
                INSERT INTO standings (liga, temporada, equipo, pj, g, e, p, gf, gc, dg, pts, draw_pct)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (liga, temporada, eq["equipo"], eq["pj"], eq["g"], eq["e"], eq["p"],
                  eq["gf"], eq["gc"], eq["dg"], eq["pts"], eq["draw_pct"]))
        else:
            cur.execute("""
                INSERT INTO standings (liga, temporada, equipo, pj, g, e, p, gf, gc, dg, pts, draw_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (liga, temporada, eq["equipo"], eq["pj"], eq["g"], eq["e"], eq["p"],
                  eq["gf"], eq["gc"], eq["dg"], eq["pts"], eq["draw_pct"]))

    conn.commit()
    conn.close()

def ejecutar(sql, params=None):
    conn = conectar()
    cur = conn.cursor()
    if USING_POSTGRES:
        sql = sql.replace("?", "%s")
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    try:
        rows = cur.fetchall()
    except:
        rows = []
    conn.commit()
    conn.close()
    return rows

def ejecutar_many(sql, params_list):
    if not params_list:
        return
    conn = conectar()
    cur = conn.cursor()
    if USING_POSTGRES:
        sql = sql.replace("?", "%s")
    cur.executemany(sql, params_list)
    conn.commit()
    conn.close()
