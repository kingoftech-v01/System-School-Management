"""
Database readiness checker.
Waits for PostgreSQL to be ready before proceeding.
"""

import os
import sys
import time
import psycopg2
from psycopg2 import OperationalError

def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be ready."""
    db_config = {
        'dbname': os.getenv('DB_NAME', 'school_management'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
    }

    print(f"Waiting for database at {db_config['host']}:{db_config['port']}...")
    print(f"Database: {db_config['dbname']}, User: {db_config['user']}")

    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(**db_config)
            conn.close()
            print(f"[OK] Database is ready! (attempt {attempt}/{max_retries})")
            return True
        except OperationalError as e:
            if attempt == max_retries:
                print(f"[FAIL] Could not connect to database after {max_retries} attempts")
                print(f"Error: {e}")
                sys.exit(1)

            print(f"[{attempt}/{max_retries}] Database not ready yet, waiting {delay}s...")
            time.sleep(delay)

    return False

if __name__ == '__main__':
    wait_for_db()
