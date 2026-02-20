"""
Access Database Discovery and Inventory Utility
================================================

This script performs a recursive filesystem scan to discover Microsoft Access
database files (.mdb, .accdb) within a specified root directory and generates
a structured CSV inventory of discovered files. It is designed to support
large-scale legacy data audits, archival assessments, and data migration
planning workflows.

Core Functionality
------------------
1. Recursively traverses a root directory using pathlib.Path.rglob().
2. Identifies Access database files by extension (.mdb, .accdb).
3. Extracts file-level metadata:
   - File name
   - File extension
   - Absolute file path
   - File size (bytes)
   - Creation timestamp (ISO 8601 format)
   - Last modified timestamp (ISO 8601 format)
4. Generates an MD5 checksum for each file to support:
   - Deduplication analysis
   - Integrity verification
   - Change detection
5. Writes results to a structured CSV inventory file.
6. Logs permission errors, hashing failures, and unexpected exceptions
   to `discovery.log`.

Design Considerations
---------------------
- Uses chunked file reads when hashing to prevent excessive memory
  consumption, especially in 32-bit Python environments.
- Avoids loading entire files into memory.
- Designed to tolerate:
    * Permission-restricted files
    * Corrupted files
    * Intermittent filesystem issues
- Logging provides traceability for audit and troubleshooting purposes.

Logging
-------
All operational events and errors are written to:
    discovery.log

Log levels:
    INFO     – Scan lifecycle events
    WARNING  – Permission-denied files
    ERROR    – Hashing or unexpected processing failures

Typical Use Case
----------------
Intended for environments containing large volumes (e.g., thousands) of
legacy Microsoft Access databases distributed across network storage.
Supports downstream data consolidation, migration, or archival projects
by producing a normalized inventory dataset.

Execution
---------
Configure:
    NETWORK_DRIVE_PATH
    OUTPUT_INVENTORY_CSV

Then execute the script directly:

    python discover_access_databases.py

Dependencies
------------
- Python 3.8+
- Standard library only (os, pathlib, hashlib, csv, logging, datetime)

Output
------
A UTF-8 encoded CSV file containing one row per discovered database file.

Author
------
Designed for structured legacy data discovery and consolidation workflows.
"""

import os
import hashlib
import csv
import logging
from datetime import datetime
from pathlib import Path

# Set up logging to capture permission errors or corrupted files
logging.basicConfig(
    filename="discovery.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def generate_md5(file_path, chunk_size=8192):
    """
    Generates an MD5 hash of a file.
    Reads in chunks to prevent memory overload in 32-bit Python.
    """
    md5_hash = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks
            for chunk in iter(lambda: f.read(chunk_size), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except (IOError, OSError) as e:
        logging.error("Failed to hash %s: %s", file_path, e)
        return "ERROR"


def scan_directory(root_dir, output_csv):
    """
    Scans the root directory for Access databases and writes metadata to a CSV.
    """
    root_path = Path(root_dir)

    # Define the extensions we care about (ignoring .ldb/.laccdb lock files for now)
    target_extensions = {".mdb", ".accdb"}

    # Prepare the CSV output
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "file_name",
            "file_extension",
            "file_path",
            "size_bytes",
            "creation_date",
            "modified_date",
            "md5_hash",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        logging.info("Starting scan of directory: %s", root_dir)
        file_count = 0

        # Walk through the directory structure
        for file_path in root_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in target_extensions:
                try:
                    # Extract basic file metadata
                    stats = file_path.stat()
                    size_bytes = stats.st_size

                    # Convert timestamps to readable format
                    created = datetime.fromtimestamp(stats.st_ctime).isoformat()
                    modified = datetime.fromtimestamp(stats.st_mtime).isoformat()

                    # Generate hash for deduplication
                    # Note: We hash AFTER getting stats so we don't alter access times unnecessarily
                    file_hash = generate_md5(file_path)

                    # Write to CSV
                    writer.writerow(
                        {
                            "file_name": file_path.name,
                            "file_extension": file_path.suffix.lower(),
                            "file_path": str(file_path.absolute()),
                            "size_bytes": size_bytes,
                            "creation_date": created,
                            "modified_date": modified,
                            "md5_hash": file_hash,
                        }
                    )

                    file_count += 1
                    if file_count % 100 == 0:
                        print(f"Scanned {file_count} database files...")

                except PermissionError:
                    logging.warning("Permission denied: %s", file_path)
                except (OSError, IOError, ValueError) as e:
                    logging.error("Unexpected error processing %s: %s", file_path, e)

        logging.info("Scan complete. Found %s Access databases.", file_count)
        print(
            f"\nScan complete! Discovered {file_count} databases. Check discovery.log for any errors."
        )


if __name__ == "__main__":
    # --- Configuration ---
    # Replace this with the path to the network drive or top-level directory
    NETWORK_DRIVE_PATH = r"..\..\data\input_samples"

    # The output inventory file (maps to the structure defined earlier)
    OUTPUT_INVENTORY_CSV = r"..\..\data\staging_exports\master_database_inventory.csv"

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(OUTPUT_INVENTORY_CSV), exist_ok=True)

    # Run the scanner
    scan_directory(NETWORK_DRIVE_PATH, OUTPUT_INVENTORY_CSV)
