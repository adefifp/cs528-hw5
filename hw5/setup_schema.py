import sys
import os
import pymysql

DB_HOST = os.environ.get("DB_HOST", sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "cs528password")
DB_NAME = "cs528_hw5"

def initialize_database():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True
    )
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
    cursor.execute(f"USE {DB_NAME};")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS successful_requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        country VARCHAR(100),
        client_ip VARCHAR(45),
        gender VARCHAR(20),
        age INT,
        income VARCHAR(50),
        is_banned BOOLEAN,
        time_of_day VARCHAR(50),
        requested_file VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS failed_requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        time_of_request VARCHAR(50),
        requested_file VARCHAR(255),
        error_code INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    initialize_database()
