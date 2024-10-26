#!/usr/bin/python3
import psycopg2
import boto3
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_secret():
    """Retrieve credentials from AWS Secrets Manager."""
    secret_name = "/DEV/audioClientServer/Orchestrator/v2"
    region_name = "us-east-2"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        secret_value = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(secret_value['SecretString'])
        return secret
    except Exception as e:
        logger.error(f"Error getting secret: {str(e)}")
        raise

def test_db_connection():
    """Test PostgreSQL database connection."""
    try:
        # Get credentials from Secrets Manager
        logger.info("Retrieving credentials from Secrets Manager...")
        secret = get_secret()
        
        # Split host and port from db_host value
        host_port = secret['db_host'].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        
        # Log connection attempt (without sensitive info)
        logger.info(f"Attempting to connect to database at {host} on port {port}")
        
        # Attempt connection with separate host and port parameters
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=secret['db_name'],
            user=secret['db_username'],
            password=secret['db_password'],
            connect_timeout=5
        )
        
        # Test the connection with a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"Successfully connected to PostgreSQL. Version: {version[0]}")
            
            # Test tasks table
            cursor.execute("SELECT COUNT(*) FROM tasks;")
            count = cursor.fetchone()
            logger.info(f"Number of tasks in database: {count[0]}")
            
        conn.close()
        logger.info("Database connection test completed successfully")
        return True
        
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection()
