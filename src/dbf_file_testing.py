# %% imports

import pyodbc
import pandas as pd
import os
from collections import defaultdict
import hashlib
from dbfread import DBF
from db_utilities_extraction import *

# %% Get file paths for all database files in directories

# CRSP directories for storing project databases
# source_directories = [
#     "X:\\CRSP Databases",
#     "X:\\CRSP Fieldwork 2020",
#     "X:\\CRSP Fieldwork 2021",
#     "X:\\CRSP Fieldwork 2022",
# ]

# Use current tree for testing
source_directories = [os.getcwd()]

db_file_suffix = (".accdb", ".mdb.old", ".mdb", ".DBF")  # Include old files

# db_file_suffix = (".accdb", ".mdb")  # Only include active files

df_databases = pd.DataFrame()

for src in source_directories:
    df_databases = pd.concat(
        [df_databases, get_db_files(src, db_file_suffix)], ignore_index=True
    )


# %% Test connecting to dbf

dbf_path = (
    df_databases[df_databases["file_name"].str.endswith(".DBF")]
    .sample(n=1)["file_path"]
    .item()
)

# %%

dbf = DBF(dbf_path, ignore_missing_memofile=True)

df_dbf = pd.DataFrame(iter(dbf))

# %%
