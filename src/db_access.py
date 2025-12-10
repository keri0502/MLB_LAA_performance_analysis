from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "db" / "MLBDashboard.db"



def query(sql: str) -> pd.DataFrame:
    connection = sqlite3.connect(database=DB_PATH)
    cur = connection.cursor()
    cur.execute(sql, ())
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    result = pd.DataFrame(data=rows, columns=col_names)
    connection.close()
    return result
