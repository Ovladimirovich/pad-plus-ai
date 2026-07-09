import os, psycopg2, time
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env.local'
load_dotenv(env_path)
url = os.environ['DATABASE_URL']

# Test: is the issue related to SHOW or just execute count?
for test_name, queries, expected_execs in [
    ("5 individual SELECTs", ["SELECT 1"] * 5, 5),
    ("SELECT+SHOW+SELECT individual", ["SELECT 1", "SHOW standard_conforming_strings", "SELECT 2"], 3),
    ("SHOW in batch + SELECT", ["SELECT 1; SHOW standard_conforming_strings; SELECT 2", "SELECT 3"], 2),
]:
    print(f"\n=== {test_name} ===")
    conn = psycopg2.connect(url, sslmode='require', connect_timeout=10)
    cur = conn.cursor()
    ok = 0
    for i, q in enumerate(queries):
        try:
            cur.execute(q)
            cur.fetchone()
            ok += 1
        except Exception as e:
            print(f"  Execute {i+1}: FAIL after {ok} OK")
            break
    else:
        print(f"  All {len(queries)} executes OK")
    conn.close()
    time.sleep(0.3)
