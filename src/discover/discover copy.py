"""
Phase 1: Discovery and Inventory

This module scans a provided list of root directories for legacy Microsoft Access 
database files (.mdb, .accdb). It extracts critical metadata (timestamps, file size) 
and calculates an MD5 hash for exact-match deduplication.

Output is streamed directly to a CSV file to minimize memory overhead. 
Errors (e.g., permission denied, locked files) are safely caught and logged.
"""

import os
import hashlib
import csv
import logging
from datetime import datetime
from pathlib import Path

# Configure logging to track access issues without stopping the script
LOG_FILE = Path(__file__).parent.parent.parent / "LOGS" / "discovery.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True) # Ensure log directory exists

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_md5_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculates the MD5 hash of a file.
    
    Reads the file in chunks to ensure 32-bit Python memory limits 
    are not exceeded when encountering large files.
    
    Args:
        file_path (Path): The absolute path to the file.
        chunk_size (int): The number of bytes to read into memory at a time.
        
    Returns:
        str: The MD5 hash string, or "ERROR" if the file could not be read.
    """
    md5_hash = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash in chunks
            for chunk in iter(lambda: f.read(chunk_size), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except PermissionError:
        logging.warning("Permission denied reading file for hash: %s", file_path)
        return "ERROR_PERMISSION"
    except OSError as e:
        logging.warning("OS Error reading file for hash %s: %s", file_path, e)
        return "ERROR_LOCKED_OR_CORRUPT"

def discover_databases(directory_list: list, output_csv_path: Path) -> None:
    """
    Scans multiple root directories for Access databases and writes metadata to a CSV.
    
    Args:
        directory_list (list): A list of string or Path objects representing root folders.
        output_csv_path (Path): The path where the inventory CSV will be saved.
    """
    target_extensions = {".mdb", ".accdb"}
    
    # Ensure the output directory exists
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set up the CSV writer
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "Root_Source", "File_Name", "Extension", "File_Path", 
            "Size_Bytes", "Created_Date", "Modified_Date", "MD5_Hash"
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        logging.info("Starting discovery across %s directories.", len(directory_list))
        file_count = 0

        print(f"Starting discovery across {len(directory_list)} directories...")
        
        # Iterate through each root directory provided
        for root_dir in directory_list:
            root_path = Path(root_dir)
            
            if not root_path.exists() or not root_path.is_dir():
                logging.error("Provided root directory is invalid or inaccessible: %s", root_path)
                print(f"Skipping invalid directory: {root_path}")
                continue
                            
            logging.info("Scanning directory: %s", root_path)
            print(f"Scanning: {root_path} ...")
            
            # Walk the directory tree using os.walk to gracefully handle permission errors
            for dirpath, _, filenames in os.walk(root_path):
                for file_name in filenames:
                    file_path = Path(dirpath) / file_name
                    
                    if file_path.suffix.lower() in target_extensions:
                        try:
                            # Extract basic metadata
                            file_stat = file_path.stat()
                            size_bytes = file_stat.st_size
                            
                            # Convert timestamps to human-readable formats
                            created_dt = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                            modified_dt = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Calculate file hash for deduplication
                            file_hash = get_md5_hash(file_path)
                            
                            # Write record immediately to disk (CSV) to save memory
                            writer.writerow({
                                "Root_Source": str(root_path),
                                "File_Name": file_name,
                                "Extension": file_path.suffix.lower(),
                                "File_Path": str(file_path),
                                "Size_Bytes": size_bytes,
                                "Created_Date": created_dt,
                                "Modified_Date": modified_dt,
                                "MD5_Hash": file_hash
                            })

                            file_count += 1
                            if file_count % 100 == 0:
                                print(f"Scanned {file_count} database files...")

                        except PermissionError:
                            logging.warning("Permission denied accessing metadata: %s", file_path)
                        except OSError as e:
                            logging.warning("OS Error accessing metadata %s: %s", file_path, e)
    
    logging.info("Scan complete. Found %s Access databases.", file_count)
    logging.info("Discovery complete. Inventory saved to: %s", output_csv_path)
    
    print(f"\nDiscovery complete. Inventory saved to: {output_csv_path}")
    print(f"\nScan complete! Discovered {file_count} databases. Check discovery.log for any errors.")
    print(f"\nCheck {LOG_FILE} for any permission or access errors.")

if __name__ == "__main__":
    # Example usage:
    # Define your list of network drives, UNC paths, or local directories here
    target_directories = [
        r"..\..\data\input_samples",
        r"X:\CRSP Fieldwork 2025"
    ]
    
    # Define where the output goes (aligns with the project structure)
    inventory_output = Path(__file__).parent.parent.parent / "data" / "staging_exports" / "database_inventory.csv"
    
    # Run the discovery
    discover_databases(target_directories, inventory_output)