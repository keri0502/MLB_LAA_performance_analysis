import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px



BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "MLBDashboard.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def load_batter_data():
    with get_connection() as conn:
        query = "SELECT * FROM Batters"
        df = pd.read_sql_query(query, conn)
    return df

def load_pitcher_data():
    with get_connection() as conn:
        query = "SELECT * FROM Pitchers"
        df = pd.read_sql_query(query, conn)
    return df

def load_team_data():
    with get_connection() as conn:
        query = "SELECT * FROM Teams"
        df = pd.read_sql_query(query, conn)
    return df

def create_radar_figure(
    side: str = "batter",
    position: str = "ALL",
    metrics: list[str] | None = None,
):
    if side == "batter":
        df = load_batter_data()
    else:
        df = load_pitcher_data()

def create_bar_figure(
    side: str = "batter",
    metric: str = "OPS",
):
    if side == "batter":
        df = load_batter_data()
        y_label = metric
    else:
        df = load_pitcher_data()
        y_label = metric

def create_scatter_figure(
    side: str = "batter",
):
    if side == "batter":
        df = load_batter_data()
    else:
        df = load_pitcher_data()