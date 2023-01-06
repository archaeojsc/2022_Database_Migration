# %% Imports

import pyodbc
import pandas as pd
import os
from collections import defaultdict
import random
import hashlib

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


# %% Function to retrieve list of files, return pandas dataframe of file
# information


def get_db_files(top_dir: str, file_ext):
    """
    Return dataframe of information for files with specified extensions found
    under starting directory.

    Parameters
    ----------
    top_dir : str
        directory to begin search
    file_ext : list, tuple, or str
        file extensions to include in search

    Returns
    -------
    dataframe
        pandas dataframe with id hash index, file name, directory string, and full absolute
        path
    """

    df_files = pd.DataFrame(columns=["db_id", "file_name", "file_dir", "file_path"])

    for root, _, files in os.walk(top_dir):
        for file in files:
            if file.endswith(file_ext):
                new_row = pd.Series(
                    {
                        "file_name": file,
                        "file_dir": root,
                        "file_path": os.path.join(root, file),
                        "database_identifier": hashlib.md5(
                            os.path.join(root, file).encode(
                                encoding="UTF-8", errors="strict"
                            )
                        ).hexdigest(),
                    }
                )
                df_files = pd.concat(
                    [df_files, new_row.to_frame().T], ignore_index=True
                )

    return df_files


# %% Function to open ODBC database and return connection and cursor


def odbc_connect_ms_access(dbq_path: str):
    """
    Returns pyodbc connection and cursor for a Microsoft Access database.

    Parameters
    ----------
    dbq_path : str
        full absolute file path of MS Access database

    Returns
    -------
    obj, obj
        odbc connection, odbc connection cursor
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


def extract_ms_access_db_schema(file_path: str):
    """
    Extracts table schema from Microsoft Access database using pyodbc.

    Parameters
    ----------
    file_path : str
        full absolute file path of MS Access database

    Returns
    -------
    dict
        dictionary of table definitions
    """

    db_table_defs = defaultdict(dict)

    db_conn, db_cursor = odbc_connect_ms_access(file_path)

    db_table_names = [t.table_name for t in db_cursor.tables(tableType="TABLE")]

    for curr_table in db_table_names:
        db_table_defs[curr_table] = {}

        db_table_defs[curr_table]["unique_indices"] = {}

        for s in db_cursor.statistics(table=curr_table, unique=True):
            if s.index_name:
                if s.index_name in db_table_defs[curr_table]["unique_indices"]:
                    db_table_defs[curr_table]["unique_indices"][s.index_name].append(
                        s.column_name
                    )
                else:
                    db_table_defs[curr_table]["unique_indices"][s.index_name] = [
                        s.column_name
                    ]

        db_table_defs[curr_table]["column_defs"] = {}

        for col in db_cursor.columns(table=curr_table):
            db_table_defs[curr_table]["column_defs"][col.column_name] = {
                "data_type_name": col.type_name,
                "sql_data_type": col.sql_data_type,
                "is_nullable": col.is_nullable,
            }

    db_conn.close()

    return db_table_defs


# %% Build dictionary of database schema


# %% Testing connection to database


# Testing path for office workstation
# db_path = "C:\\Users\\scardina\\Documents\\Projects\\Active Projects\\2022_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

# Testing path for home workstation db_path =
# "C:\\Users\\Scott\\Documents\\2022_Database_Migration\\1BOW.00.101 Prattsville
# (10-2014).accdb"

db_files_list = get_db_files(source_directories[0], db_file_suffix)

db_index = random.randint(0, len(db_files_list))

db_path = db_files_list.iloc[db_index]["file_path"]

my_conn, my_cursor = odbc_connect_ms_access(db_path)

my_conn.close()

# %% Index extraction testing

# stat_keys = (
#     "table_cat",
#     "table_schem",
#     "table_name",
#     "non_unique",
#     "index_qualifier",
#     "index_name",
#     "type",
#     "ordinal_position",
#     "column_name",
#     "asc_or_desc",
#     "cardinality",
#     "pages",
#     "filter_condition",
# )

# my_table = "Provenience"

# unique_indices = defaultdict(dict)

# for s in my_cursor.statistics(table=my_table, unique=True):
#     if s.index_name:
#         if s.index_name in unique_indices:
#             unique_indices[s.index_name].append(s.column_name)
#         else:
#             unique_indices[s.index_name] = [s.column_name]

# my_conn.close()

# %% Testing extraction of database schema from dictionary

# Choose random db from file list

db_index = random.randint(0, len(db_files_list))

test_db = db_files_list.iloc[db_index]["file_path"]

test_db_schema = extract_ms_access_db_schema(test_db)

# List of tables
test_db_tables = [tbl for tbl in test_db_schema.keys()]

# %% Function to return pandas df of table columns definitions


def extract_db_table_def_df(db: dict):

    df_table_def = pd.DataFrame(
        columns=["db_table", "db_table_columns", "db_table_primary_key"]
    )

    df_tables = [t for t in db.keys()]

    for tab in df_tables:
        new_def = pd.Series(
            {
                "db_table": tab,
                "db_table_columns": [col for col in db[tab]["column_defs"].keys()],
                "db_table_primary_key": [
                    v
                    for k, v in db[tab]["unique_indices"].items()
                    if (k == "PrimaryKey")
                ],
            }
        )
        df_table_def = pd.concat(
            [df_table_def, new_def.to_frame().T], ignore_index=True
        )

    return df_table_def


# %%
