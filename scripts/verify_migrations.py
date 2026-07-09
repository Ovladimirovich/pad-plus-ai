import os, sys

os.chdir(r'C:\пад ал датабаз а  чистый\PAD+ AI чистый')

with open('.env', encoding='utf-8') as f:
    env_lines = f.readlines()

db_url = None
for line in env_lines:
    if line.startswith('DATABASE_URL='):
        db_url = line.strip().split('=', 1)[1]
        break

db_url = db_url.strip("'").strip('"')

import psycopg2
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema='public' AND table_name IN ('experiences', 'user_personas')
    ORDER BY table_name
""")
tables = [r[0] for r in cur.fetchall()]
print(f"Tables found: {tables}")

for table in tables:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (table,))
    cols = cur.fetchall()
    print(f"  {table} columns:")
    for c in cols:
        print(f"    - {c[0]} ({c[1]})")

cur.close()
conn.close()
print("\nVerification complete!")
