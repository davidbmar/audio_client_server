#!/usr/bin/python3

import boto3
import psycopg2
import logging
from urllib.parse import quote
import json
import time
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AWS Configuration
REGION_NAME = 'us-east-2'
SECRET_NAME = "/DEV/audioClientServer/Orchestrator/v2"

def get_secrets():
    """Retrieve configuration from AWS Secrets Manager."""
    try:
        secrets_client = boto3.client('secretsmanager', region_name=REGION_NAME)
        secret_value = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        return json.loads(secret_value['SecretString'])
    except Exception as e:
        logger.error(f"Error retrieving secrets: {e}")
        raise

def get_db_connection(secrets):
    """Establish database connection."""
    try:
        # Split host and port from db_host value
        host_port = secrets['db_host'].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432

        return psycopg2.connect(
            host=host,
            port=port,
            database=secrets['db_name'],
            user=secrets['db_username'],
            password=secrets['db_password']
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def encode_key(key):
    """Fully URL encode a key."""
    return quote(key, safe='')

def migrate_s3_objects(s3_client, source_bucket, encoded_mapping):
    """
    Migrate S3 objects to use URL encoded keys.
    Returns dict of {old_key: new_key} for successfully migrated objects.
    """
    successful_migrations = {}
    
    try:
        for old_key, new_key in encoded_mapping.items():
            if old_key == new_key:
                logger.info(f"Key already encoded, skipping: {old_key}")
                continue

            try:
                # Copy object with new key
                copy_source = {'Bucket': source_bucket, 'Key': old_key}
                logger.info(f"Copying {old_key} to {new_key}")
                s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=source_bucket,
                    Key=new_key
                )

                # Verify the new object exists
                s3_client.head_object(Bucket=source_bucket, Key=new_key)
                
                # Delete old object
                logger.info(f"Deleting old object: {old_key}")
                s3_client.delete_object(Bucket=source_bucket, Key=old_key)
                
                successful_migrations[old_key] = new_key
                logger.info(f"Successfully migrated: {old_key} -> {new_key}")
                
            except ClientError as e:
                logger.error(f"Error migrating object {old_key}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in S3 migration: {e}")
        
    return successful_migrations

def migrate_database(conn, successful_s3_migrations):
    """Update database records with encoded keys."""
    try:
        with conn.cursor() as cursor:
            # First, get all tasks
            cursor.execute("SELECT task_id, object_key FROM tasks")
            tasks = cursor.fetchall()
            
            # Update each task with encoded key
            for task_id, object_key in tasks:
                if object_key in successful_s3_migrations:
                    new_key = successful_s3_migrations[object_key]
                    logger.info(f"Updating task {task_id} with new key: {new_key}")
                    
                    cursor.execute("""
                        UPDATE tasks 
                        SET object_key = %s,
                            updated_at = NOW()
                        WHERE task_id = %s
                    """, (new_key, task_id))
            
            conn.commit()
            logger.info("Database migration completed successfully")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in database migration: {e}")
        raise

def main():
    try:
        # Get configuration
        secrets = get_secrets()
        logger.info("Retrieved secrets successfully")

        # Initialize AWS clients
        s3 = boto3.client('s3', region_name=REGION_NAME)
        
        # Get database connection
        conn = get_db_connection(secrets)
        logger.info("Database connection established")

        try:
            # Get all objects from input bucket
            input_bucket = secrets['input_bucket']
            paginator = s3.get_paginator('list_objects_v2')
            
            # Create mapping of current keys to encoded keys
            encoded_mapping = {}
            
            for page in paginator.paginate(Bucket=input_bucket):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        current_key = obj['Key']
                        encoded_key = encode_key(current_key)
                        encoded_mapping[current_key] = encoded_key

            logger.info(f"Found {len(encoded_mapping)} objects to process")

            # Migrate S3 objects
            logger.info("Starting S3 migration...")
            successful_migrations = migrate_s3_objects(s3, input_bucket, encoded_mapping)
            logger.info(f"S3 migration completed. {len(successful_migrations)} objects migrated")

            # Update database records
            logger.info("Starting database migration...")
            migrate_database(conn, successful_migrations)
            logger.info("Migration completed successfully")

        finally:
            conn.close()
            logger.info("Database connection closed")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()
