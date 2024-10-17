#!/usr/bin/python3
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)

DB_HOST = "terraform-20241016044926222400000001.cny2uiqswlls.us-east-2.rds.amazonaws.com"
DB_NAME = "my_rds_db"
DB_USER = "dbm_db_admin"
DB_PASSWORD = "mysecurepassword"

def test_db_connection():
    logging.info("Testing database connection...")
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5  # Add a timeout to prevent hanging
        )
        logging.info("Database connection successful.")
        connection.close()
    except Exception as e:
        logging.error(f"Database connection failed: {e}", exc_info=True)

if __name__ == '__main__':
    test_db_connection()


