import sqlite3
import pandas as pd


def create_connection(db_name="covid_analysis.db"):
    """Tworzy połączenie z bazą SQLite"""
    conn = sqlite3.connect(db_name)
    return conn


def save_daily_deaths(df_daily):
    """Zapisuje dataframe do SQLite"""

    conn = create_connection()

    df_daily.to_sql(
        "daily_deaths",
        conn,
        if_exists="replace",
        index=False
    )

    conn.commit()
    conn.close()

    print("Tabela daily_deaths zapisana w bazie SQLite.")