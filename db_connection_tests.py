# %% Imports

import pyodbc
import pandas as pd
import os
from collections import defaultdict

# %% Get file paths for all database files in directories

db_files_list = []

# CRSP directories for storing project databases
# source_directories = [
#     "X:\\CRSP Databases",
#     "X:\\CRSP Fieldwork 2020",
#     "X:\\CRSP Fieldwork 2021",
#     "X:\\CRSP Fieldwork 2022",
# ]

# Use current tree for testing
source_directories = [os.getcwd()]

# db_file_suffix = (".accdb", ".mdb.old", ".mdb", ".DBF") # Include old files

db_file_suffix = (".accdb", ".mdb")  # Only include active files

for top_directory in source_directories:
    for root, dirs, files in os.walk(top_directory):
        for file in files:
            if file.endswith(db_file_suffix):
                db_files_list.append(os.path.join(root, file))

# %% Function to open ODBC database and return connection and cursor

def odbc_connect_ms_access(dbq_path: str):
    """ Returns pyodbc connection and cursor for a Microsoft Access
        database.

        :param dbq_path: full absolute file path of MS Access database
        :type dbq_path: str

        :rtype: obj, obj
        :return: odbc connection, connection cursor
    """
    
    # Required Microsoft Access ODBC driver
    odbc_driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"

    # ODBC connection string
    conn_str = rf"DRIVER={odbc_driver};" rf"DBQ={dbq_path};"

    # Open ODBC connection and cursor
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()

    return conn, cur


# %% Function to extract database schema

def extract_ms_access_db_schema(file_path):
    db_table_defs = defaultdict(dict)

    db_conn, db_cursor = odbc_connect_ms_access(file_path)

    db_table_names = [
        t.table_name 
        for t in db_cursor.tables(tableType="TABLE")
        ]

    for curr_table in db_table_names:
        db_table_defs[curr_table]={}

        db_table_defs[curr_table]['primary_key'] = [
            pk.column_name
            for pk in db_cursor.statistics(table=curr_table, unique=True)
            if pk.index_name == 'PrimaryKey'
            ]

        db_table_defs[curr_table]['column_defs']={}

        for col in db_cursor.columns(table=curr_table):
            db_table_defs[curr_table]['column_defs'][col.column_name] = {
                'data_type_name': col.type_name,
                'sql_data_type': col.sql_data_type, 
                'is_nullable': col.is_nullable
                }

    db_conn.close()

    return db_table_defs

# %% Connect to database


# Testing path for office workstation
# db_path = "C:\\Users\\scardina\\Documents\\Projects\\Active Projects\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

# Testing path for home workstation db_path =
# "C:\\Users\\Scott\\Documents\\2022_Database_Migration\\1BOW.00.101 Prattsville
# (10-2014).accdb"

db_path = db_files_list[5]

my_conn, my_cursor = odbc_connect_ms_access(db_path)

# %% Retrieve list of database user table names, excluding system tables and
# query views

# db_table_names = [t.table_name for t in my_cursor.tables(tableType="TABLE")]

# # %% Retrieve table definitions as dictionary

# db_table_def = defaultdict(dict)

# for t in db_table_names:
#     db_table_def[t]['primary_key'] = [
#         pk.column_name
#         for pk in my_cursor.statistics(table=t, unique=True)
#         if pk.index_name == 'PrimaryKey'
#     ]

#     db_table_def[t]['column_defs'] = {}
    
#     for c in my_cursor.columns(table=t):
#         db_table_def[t]['column_defs'][c.column_name] = {
#             'data_type_name': c.type_name,
#             'sql_data_type': c.sql_data_type, 
#             'is_nullable': c.is_nullable
#             }
    

# %% Close connection

my_conn.close()

# %%
