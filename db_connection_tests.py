# %% Imports

import pyodbc
import pandas as pd
import os

# %% Get file paths for all database files in directories

db_files_list = []

file_directory_start = [
    "X:\\CRSP Databases",
    "X:\\CRSP Fieldwork 2020",
    "X:\\CRSP Fieldwork 2021",
    "X:\\CRSP Fieldwork 2022",
]

# start_dir = os.getcwd()

# db_file_suffix = (".accdb", ".mdb.old", ".mdb", ".DBF") # Include old files

db_file_suffix = (".accdb", ".mdb")  # Only include active files

for top_directory in file_directory_start:
    for root, dirs, files in os.walk(top_directory):
        for file in files:
            if file.endswith(db_file_suffix):
                db_files_list.append(os.path.join(root, file))


# %% ODBC Connection info

db_driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"

# Testing path for office workstation
db_path = "C:\\Users\\scardina\\Documents\\Projects\\Active Projects\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

# Testing path for home workstation
# db_path = "C:\\Users\\Scott\\Documents\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

# ODBC connection string
conn_str = rf"DRIVER={db_driver};" rf"DBQ={db_path};"

# %% Open ODBC connection and cursor

conn = pyodbc.connect(conn_str)
cur = conn.cursor()

# %% Retrieve list of database tables, excluding system tables and query views

my_tables = [t.table_name for t in cur.tables(tableType="TABLE")]


# %% Table columns

for t in my_tables:
    print("Table:\t", t, "\n")
    for c in cur.columns(table=t):
        print("\t", c.column_name, c.type_name, c.sql_data_type, c.is_nullable)
    print("\n")

# %% Primary Keys

for t in my_tables:
    print("Table:\t", t, "\n")
    for p_key in cur.primaryKeys(table=t):
        print("\t", p_key)
    print("\n")

# %% Foreign Keys

for t in my_tables:
    print("Table:\t", t, "\n")
    for f_key in cur.foreignKeys(table=t):
        print("\t", f_key)
    print("\n")

# %% table statistics

for t in my_tables:
    print("Table:\t", t, "\n")
    for t_stat in cur.statistics(table=t, unique=True):
        print("\t", t_stat)
    print("\n")


# %% Close connection

conn.close()


# %%
