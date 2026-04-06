
import urllib
import pandas as pd
from sqlalchemy import create_engine, inspect

# SQL Server ODBC connection (replace placeholders)
odbc = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\Warehouse;"
    "DATABASE=NGX;"
    "UID=sa;"
    "PWD=P@ssword123$;"
)
params = urllib.parse.quote_plus(odbc)
mssql_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)

# Output SQLite file (will be created)
sqlite_engine = create_engine("sqlite:///C:/Users/HP/Desktop/G_Stock/G_stock/utility/ngx.sqlite")

inspector = inspect(mssql_engine)
schema = "dbo"  # change if your tables live in another schema
tables = inspector.get_table_names(schema=schema)

for table in tables:
    print("Exporting", table)
    first_chunk = True
    qry = f"SELECT * FROM [{schema}].[{table}]"
    for chunk in pd.read_sql_query(qry, con=mssql_engine, chunksize=10000):
        chunk.to_sql(table, sqlite_engine, if_exists="replace" if first_chunk else "append", index=False)
        first_chunk = False

print("Done — sqlite DB at:", "C:/Users/HP/Desktop/G_Stock/G_stock/utility/ngx.sqlite")
