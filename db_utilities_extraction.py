# %% Imports

import os
from collections import defaultdict
import pandas as pd
import pyodbc

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
        pandas dataframe with file name, directory string, and full absolute
        path
    """

    df_files = pd.DataFrame(columns=["file_name", "file_dir", "file_path"])

    for root, _, files in os.walk(top_dir):
        for file in files:
            if file.endswith(file_ext):
                new_row = pd.Series(
                    {
                        "file_name": file,
                        "file_dir": root,
                        "file_path": os.path.join(root, file),
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
