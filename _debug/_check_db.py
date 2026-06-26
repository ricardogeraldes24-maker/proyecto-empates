import sqlite3
import os, pathlib
os.chdir(pathlib.Path(__file__).parent)
conn = sqlite3.connect("empates.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
for t in tables:
    print(f"=== Table: {t[0]} ===")
    c.execute(f"PRAGMA table_info({t[0]})")
    cols = c.fetchall()
    for col in cols:
        print(f"  {col}")
    c.execute(f"SELECT COUNT(*) FROM {t[0]}")
    cnt = c.fetchone()[0]
    print(f"  Rows: {cnt}")
    if cnt > 0:
        c.execute(f"SELECT * FROM {t[0]} LIMIT 3")
        rows = c.fetchall()
        for row in rows:
            print(f"  Sample: {row}")
conn.close()
