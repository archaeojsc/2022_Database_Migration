# %% Imports

import pyodbc
import pandas as pd
import os

# %% Connection info

db_driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"

# Path for office workstation
db_path = "C:\\Users\\scardina\\Documents\\Projects\\Active Projects\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

# Path for home workstation
# db_path = "C:\\Users\\Scott\\Documents\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

conn_str = rf"DRIVER={db_driver};" rf"DBQ={db_path};"

# %% Open connection and cursor

conn = pyodbc.connect(conn_str)
cur = conn.cursor()


# %% Print tables

my_tables = [t.table_name for t in cur.tables(tableType="TABLE")]

# %% Table columns

for t in my_tables:
    print("Table:\t", t, "\n")
    for c in cur.columns(table=t):
        print("\t", c.column_name, "(", c.type_name, ")")
    print("\n")

# %% Primary Keys

for t in my_tables:
    print("Table:\t", t, "\n")
    for p_key in cur.foreignKeys(table=t):
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


# %% Get file paths for database files in directory

db_files_list = []

file_directory_start = [
    "X:\\CRSP Databases",
    "X:\\CRSP Fieldwork 2020",
    "X:\\CRSP Fieldwork 2021",
    "X:\\CRSP Fieldwork 2022",
]

# start_dir = os.getcwd()

# db_file_suffix = (".accdb", ".mdb.old", ".mdb", ".DBF")
db_file_suffix = (".accdb", ".mdb")

for top_directory in file_directory_start:
    for root, dirs, files in os.walk(top_directory):
        for file in files:
            if file.endswith(db_file_suffix):
                db_files_list.append(os.path.join(root, file))


# %%
