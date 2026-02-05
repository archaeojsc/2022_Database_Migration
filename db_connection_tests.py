# %% Imports

import hashlib
import os

from collections import defaultdict
from typing import Tuple, Any, Dict
from pathlib import Path

import pandas as pd
import pyodbc

# import random



# %% Function to retrieve list of databases


def get_db_files(top_dir: str, file_ext):
    """
    Return dataframe of information for files with specified extensions found
    recursively under starting directory.
    """

    if isinstance(file_ext, str):
        file_ext = (file_ext.lower(),)
    else:
        file_ext = tuple(ext.lower() for ext in file_ext)

    rows = []

    for root, _, files in os.walk(top_dir):
        for file in files:
            if file.lower().endswith(file_ext):
                full_path = os.path.join(root, file)
                rows.append(
                    {
                        "file_name": file,
                        "file_ext": os.path.splitext(file)[-1].lower(),
                        "file_dir": root,
                        "file_path": full_path,
                        "db_identifier": hashlib.md5(
                            full_path.encode("utf-8")
                        ).hexdigest(),
                    }
                )

    return pd.DataFrame(
        rows,
        columns=["db_identifier", "file_ext", "file_name", "file_dir", "file_path"],
    )



# %% Get file paths for all database files in directories

# CRSP directories for storing project databases
source_directories = [
    "X:\\CRSP Databases",
    "X:\\CRSP Fieldwork 2020 to 2022",
    "X:\\CRSP Fieldwork 2023",
    "X:\\CRSP Fieldwork 2024",
    "X:\\CRSP Fieldwork 2025"
]

# Use current tree for testing
# source_directories = [os.getcwd()]

# db_file_suffix = (".accdb", ".mdb.old", ".mdb", ".DBF")  # Include old files

db_file_suffix = (".accdb")  # Only include active files

df_databases = pd.DataFrame()

for src in source_directories:
    df_databases = pd.concat(
        [df_databases, get_db_files(src, db_file_suffix)], ignore_index=True
    )


# %% Function to open ODBC database and return connection and cursor


def _decode_bad_utf16(raw: bytes) -> str:
    """
    Workaround for MS Access ODBC UTF-16LE truncation issues.
    """
    s = raw.decode("utf-16le", errors="ignore")
    null_pos = s.find("\x00")
    return s if null_pos == -1 else s[:null_pos]


def odbc_connect_ms_access(dbq_path: str) -> Tuple[pyodbc.Connection, pyodbc.Cursor]:
    """
    Returns a pyodbc connection and cursor for a Microsoft Access database.

    Parameters
    ----------
    dbq_path : str
        Absolute file path to a .mdb or .accdb database

    Returns
    -------
    (pyodbc.Connection, pyodbc.Cursor)
    """

    if not isinstance(dbq_path, str) or not dbq_path.strip():
        raise ValueError("dbq_path must be a non-empty string")

    if not os.path.isfile(dbq_path):
        raise FileNotFoundError(f"Access database not found: {dbq_path}")

    if not dbq_path.lower().endswith((".mdb", ".accdb")):
        raise ValueError("Unsupported file type (expected .mdb or .accdb)")

    drivers = [d for d in pyodbc.drivers() if "Access Driver" in d]
    if not drivers:
        raise RuntimeError(
            "Microsoft Access ODBC driver not found. "
            "Install the Microsoft Access Database Engine."
        )

    driver = drivers[-1]  # prefer newest driver

    conn_str = (
        f"DRIVER={driver};"
        f"DBQ={dbq_path};"
        "ExtendedAnsiSQL=1;"
    )

    try:
        conn = pyodbc.connect(conn_str, autocommit=False)
    except pyodbc.Error as exc:
        raise ConnectionError("Failed to connect to Access database") from exc

    # Register UTF-16 workaround
    conn.add_output_converter(pyodbc.SQL_WVARCHAR, _decode_bad_utf16)

    return conn, conn.cursor()

# %% Testing connection to database


# Testing path for office workstation
# db_path = "C:\\Users\\scardina\\OneDrive - New York State Education Department\\Documents\\Projects\\CRSP_Access_Database_Migration\\1BOW.00.101 Prattsville (10-2014).accdb"

# Testing path for home workstation db_path =
# "C:\\Users\\Scott\\Documents\\2022_Database_Migration\\1BOW.00.101 Prattsville
# (10-2014).accdb"

db_path = df_databases.sample(n=1)["file_path"].item()

my_conn, my_cursor = odbc_connect_ms_access(db_path)

my_cursor.close()
my_conn.close()


# %% Function to extract database schema


class AccessSchemaError(RuntimeError):
    """Raised when schema extraction from MS Access fails."""


def extract_ms_access_db_schema(file_path: str) -> Dict[str, Any]:
    """
    Extract table schema from a Microsoft Access database using pyodbc,
    including primary key detection with multiple fallback strategies.

    Parameters
    ----------
    file_path : str
        Absolute path to .mdb or .accdb file

    Returns
    -------
    dict
        Schema definition keyed by table name
    """
    path = Path(file_path)

    if path.suffix.lower() not in {".mdb", ".accdb"}:
        raise ValueError("file_path must reference a .mdb or .accdb file")

    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {path}")

    schema: Dict[str, Any] = {}

    conn = None
    cursor = None

    try:
        conn, cursor = odbc_connect_ms_access(str(path))

        excluded_prefixes = ("MSys", "USys")
        excluded_exact = {"Paste Errors", "Switchboard Items"}

        try:
            tables = [
                t.table_name
                for t in cursor.tables(tableType="TABLE")
                if not (
                    t.table_name in excluded_exact
                    or t.table_name.startswith(excluded_prefixes)
                )
            ]
        except pyodbc.Error as e:
            raise AccessSchemaError("Failed to enumerate tables") from e

        for table in tables:
            table_def = {
                "primary_key": {
                    "columns": [],
                    "source": None,
                },
                "unique_indices": defaultdict(list),
                "column_defs": {},
            }

            # -------------------------
            # COLUMN METADATA
            # -------------------------
            try:
                for col in cursor.columns(table=table):
                    table_def["column_defs"][col.column_name] = {
                        "data_type_name": col.type_name,
                        "sql_data_type": col.sql_data_type,
                        "is_nullable": bool(col.is_nullable),
                        "column_size": col.column_size,
                        "decimal_digits": col.decimal_digits,
                    }
            except pyodbc.Error as e:
                raise AccessSchemaError(
                    f"Failed to extract columns for table '{table}'"
                ) from e

            # -------------------------
            # PRIMARY KEY – STRATEGY 1
            # cursor.primaryKeys()
            # -------------------------
            try:
                pk_cols = [
                    pk.column_name
                    for pk in cursor.primaryKeys(table=table)
                ]
                if pk_cols:
                    table_def["primary_key"] = {
                        "columns": pk_cols,
                        "source": "primaryKeys",
                    }
            except pyodbc.Error:
                # Driver does not support this reliably
                pass

            # -------------------------
            # INDEX METADATA
            # -------------------------
            try:
                for stat in cursor.statistics(table=table):
                    if not stat.index_name:
                        continue

                    if stat.non_unique == 0:
                        table_def["unique_indices"][stat.index_name].append(
                            stat.column_name
                        )
            except pyodbc.Error as e:
                raise AccessSchemaError(
                    f"Failed to extract index metadata for table '{table}'"
                ) from e

            table_def["unique_indices"] = dict(table_def["unique_indices"])

            # -------------------------
            # PRIMARY KEY – STRATEGY 2
            # Unique index fallback
            # -------------------------
            if not table_def["primary_key"]["columns"]:
                for idx_name, cols in table_def["unique_indices"].items():
                    # Access often names PK index "PrimaryKey" or similar
                    if idx_name.lower().startswith("primary"):
                        table_def["primary_key"] = {
                            "columns": cols,
                            "source": "unique_index",
                        }
                        break

            # -------------------------
            # PRIMARY KEY – STRATEGY 3
            # Heuristic inference
            # -------------------------
            if not table_def["primary_key"]["columns"]:
                candidates: List[str] = []

                for col_name, col_def in table_def["column_defs"].items():
                    if not col_def["is_nullable"]:
                        lname = col_name.lower()
                        if lname == "id" or lname == f"{table.lower()}_id":
                            candidates.append(col_name)

                if len(candidates) == 1:
                    table_def["primary_key"] = {
                        "columns": candidates,
                        "source": "heuristic",
                    }

            schema[table] = table_def

    except pyodbc.Error as e:
        raise AccessSchemaError(
            f"ODBC error while reading Access schema: {e}"
        ) from e

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except pyodbc.Error:
                pass

        if conn is not None:
            try:
                conn.close()
            except pyodbc.Error:
                pass

    return schema


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

test_db = df_databases.sample(n=1)["file_path"].item()

test_db_schema = extract_ms_access_db_schema(test_db)

# List of tables
df_db_tables = [tbl for tbl in test_db_schema.keys()]

# %% Function to return pandas df of table columns definitions


def extract_db_table_def_df(id: str, db: dict):
    """
    Create pandas data frame of database table definitions

    Parameters
    ----------
    id : str
        Unique database identifier
    db : dict
        Dictionary containing database schema information retrieved from
        extract_ms_access_db_schema

    Returns
    -------
    object
        Returns pandas data frame of database identifier, table name, list of
        unique indices, and list of table columns
    """
    df_table_def = pd.DataFrame()

    db_tables = [t for t in db.keys()]

    for tab in db_tables:
        new_def = pd.Series(
            {
                "db_id": id,
                "db_table": tab,
                "db_table_columns": tuple(
                    [col for col in db[tab]["column_defs"].keys()]
                ),
                "db_table_primary_key": db[tab]["unique_indices"]["PrimaryKey"]
                if "PrimaryKey" in db[tab]["unique_indices"].keys()
                else None,
            }
        )
        df_table_def = pd.concat(
            [df_table_def, new_def.to_frame().T], ignore_index=True
        )

    return df_table_def


# %% Build dictionary of schema from all databases

db_pull_test = {
    id: extract_ms_access_db_schema(db_path)
    for id, db_path in zip(df_databases["db_identifier"], df_databases["file_path"])
}


# %%

df_db_tables = pd.DataFrame(
    [
        [db, tuple([k for k in db_pull_test[db].keys()])]
        for db in db_pull_test.keys()
        if db_pull_test[db]
    ],
    columns=["db_id", "db_tables"],
)

# %%

unique_table_schema = pd.Series(
    [list(x) for x in set(tuple(x) for x in df_db_tables["db_tables"])],
    name="table_schema",
)

# %% Get counts of unique table schema

table_schema_counts = (
    df_db_tables["db_tables"]
    .value_counts()
    .rename_axis("table_schema")
    .reset_index(name="schema_count")
)


# %% testing build table defs

df_db_table_defs = pd.DataFrame()

for db in df_db_tables["db_id"]:
    if db_pull_test[db]:
        df_db_table_defs = pd.concat(
            [df_db_table_defs, extract_db_table_def_df(db, db_pull_test[db])],
            ignore_index=True,
        )

# %%

table_def_counts = pd.DataFrame(columns=["db_table"])

for table in df_db_table_defs["db_table"].unique():
    new_def_counts = (
        df_db_table_defs[df_db_table_defs["db_table"] == table]["db_table_columns"]
        .value_counts()
        .rename_axis("table_def")
        .reset_index(name="def_count")
    )
    new_def_counts["db_table"] = table
    table_def_counts = pd.concat([table_def_counts, new_def_counts], ignore_index=True)

# %%

unique_table_defs = (
    table_def_counts.groupby(["db_table"])["table_def"]
    .nunique()
    .sort_values(ascending=False)
)

# %%

table_def_counts.groupby(["db_table"]).agg({"def_count": sum})["def_count"].nlargest(20)


# %%

table_def_counts[table_def_counts["db_table"].str.contains("Site")].groupby(
    ["db_table"], group_keys=False
).agg({"def_count": sum})["def_count"].sort_values(ascending=False)

# %%

table_def_counts[table_def_counts["db_table"].str.contains("Provenience")].groupby(
    ["db_table"], group_keys=False
)["table_def"].nunique().sort_values(ascending=False)

# %% Create dataframe of tables and fields

table_def_fields = df_db_table_defs.explode(column="db_table_columns").reset_index(
    drop=True
)

table_def_fields["is_primary_key"] = table_def_fields.apply(
    lambda x: x["db_table_columns"] in x["db_table_primary_key"]
    if x["db_table_primary_key"] is not None
    else False,
    axis=1,
)

# %%
