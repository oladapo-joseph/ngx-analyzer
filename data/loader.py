# data/loader.py — all database interactions

import pandas as pd
import streamlit as st
from dotenv import dotenv_values
from utility.db import connect_to_db, close_connection

_env = dotenv_values(".env")
_DB_PATH = "utility/ngx.sqlite"


@st.cache_data(ttl=300, show_spinner=False)
def load_stock_list() -> list[str]:
    """Return sorted list of all distinct stock Symbols."""
    conn = connect_to_db(_DB_PATH)
    df = pd.read_sql_query("SELECT DISTINCT Symbol FROM Trades ORDER BY Symbol", conn)
    close_connection(conn)
    return df["Symbol"].tolist()


@st.cache_data(ttl=300, show_spinner=False)
def load_stock_data(Symbol: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
        price_df  — DateTimeIndex, single column ClosePrice
        full_df   — DateTimeIndex, all OHLCV columns
    """
    conn = connect_to_db(_DB_PATH)
    df = pd.read_sql_query(
        "SELECT DISTINCT * FROM Trades WHERE Symbol = ?", conn, params=(Symbol,)
    )
    close_connection(conn)

    df["TradeDate"] = pd.to_datetime(df["TradeDate"], format="mixed")
    df.set_index("TradeDate", inplace=True)
    df.sort_index(inplace=True)

    price_df = df[["ClosePrice"]].copy()
    return price_df, df


@st.cache_data(ttl=600, show_spinner=False)
def load_sector_map() -> pd.DataFrame:
    """Return DataFrame with columns Symbol, Sector."""
    conn = connect_to_db(_DB_PATH)
    df = pd.read_sql_query("SELECT Symbol, Sector FROM IndustryData", conn)
    close_connection(conn)
    return df


def filter_by_dates(
    df: pd.DataFrame, start_date, end_date
) -> pd.DataFrame:
    """Slice a DateTimeIndex DataFrame to [start_date, end_date]."""
    if start_date and end_date:
        s = pd.to_datetime(start_date)
        e = pd.to_datetime(end_date)
        return df[(df.index >= s) & (df.index <= e)]
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_latest_market(sector_map: pd.DataFrame = None) -> pd.DataFrame:
    """
    Return one row per Symbol for the most recent trading date,
    with % Change and optionally Sector joined in.
    """
    conn = connect_to_db(_DB_PATH)
    query = """
        SELECT DISTINCT t.*
        FROM Trades t
        INNER JOIN (
            SELECT Symbol, MAX(TradeDate) AS LatestDate
            FROM Trades
            GROUP BY Symbol
        ) latest
        ON t.Symbol = latest.Symbol AND t.TradeDate = latest.LatestDate
    """
    df = pd.read_sql_query(query, conn)
    close_connection(conn)

    df["TradeDate"] = pd.to_datetime(df["TradeDate"], format="mixed")
    prev = df["PrevClosingPrice"].replace(0, pd.NA)
    df["PctChange"] = ((df["ClosePrice"] - prev) / prev * 100).round(2)

    if sector_map is not None and not sector_map.empty:
        sm = sector_map.copy()
        if "Symbol" in sm.columns and "Sector" in sm.columns:
            df = df.merge(sm[["Symbol", "Sector"]], on="Symbol", how="left")

    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_sector_performance() -> pd.DataFrame:
    """
    Return avg % change and total value per sector for the latest trading day.
    """
    conn = connect_to_db(_DB_PATH)
    query = """
        SELECT si.Sector,
               AVG((t.ClosePrice - t.PrevClosingPrice)
                   / NULLIF(t.PrevClosingPrice, 0) * 100) AS AvgPctChange,
               SUM(t.Value)   AS TotalValue,
               SUM(t.Volume)  AS TotalVolume,
               COUNT(*)       AS StockCount
        FROM Trades t
        INNER JOIN (
            SELECT Symbol, MAX(TradeDate) AS LatestDate
            FROM Trades
            GROUP BY Symbol
        ) latest ON t.Symbol = latest.Symbol AND t.TradeDate = latest.LatestDate
        INNER JOIN IndustryData si ON t.Symbol = si.Symbol
        GROUP BY si.Sector
    """
    df = pd.read_sql_query(query, conn)
    close_connection(conn)
    df["AvgPctChange"] = df["AvgPctChange"].round(2)
    return df
