# %% Imports

import pyodbc
import pandas as pd
import os

# %% Connection info

db_driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"
# db_path = "C:\\Users\\scardina\\Documents\\Projects\\Active Projects\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"
db_path = "C:\\Users\\Scott\\Documents\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

conn_str = rf"DRIVER={db_driver};" rf"DBQ={db_path};"

# %% Open connection and cursor

conn = pyodbc.connect(conn_str)
cur = conn.cursor()

# %% Print tables

my_tables = [t.table_name for t in cur.tables(tableType="TABLE")]

# %%

for t in my_tables:
    print("Table:\t", t, "\n")
    for c in cur.columns(table=t):
        print("\t", c.column_name, "(", c.type_name, ")")
    print("\n")

# %% Close connection

conn.close()


# %% Get file paths for database files in directory

filelist = []

# start_dir = "X:\\CRSP Databases"
start_dir = os.getcwd()

file_sfx = (".accdb", ".mdb.old", ".mdb", ".DBF")

for root, dirs, files in os.walk(start_dir):
    for file in files:
        if file.endswith(file_sfx):
            filelist.append(os.path.join(root, file))


# %%
