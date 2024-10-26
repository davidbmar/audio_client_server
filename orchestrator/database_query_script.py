#!/usr/bin/python3
import psycopg2
import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secrets():
    secret_name = "/DEV/audioClientServer/Orchestrator/v2"
    secrets_client = boto3.client('secretsmanager', region_name='us-east-2')
    secret_value = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value['SecretString'])

def check_tasks():
    """Check the status of tasks in the database."""
    secrets = get_secrets()
    
    host, port = secrets['db_host'].split(':')
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=secrets['db_name'],
        user=secrets['db_username'],
        password=secrets['db_password']
    )
    
    try:
        with conn.cursor() as cursor:
            # Get task counts by status
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM tasks 
                GROUP BY status;
            """)
            status_counts = cursor.fetchall()
            logger.info("Task counts by status:")
            for status, count in status_counts:
                logger.info(f"  {status}: {count}")
            
            # Get recent tasks
            cursor.execute("""
                SELECT task_id, object_key, status, created_at, updated_at
                FROM tasks
                ORDER BY created_at DESC
                LIMIT 5;
            """)
            recent_tasks = cursor.fetchall()
            logger.info("\nMost recent tasks:")
            for task in recent_tasks:
                logger.info(f"  Task ID: {task[0]}")
                logger.info(f"  Object Key: {task[1]}")
                logger.info(f"  Status: {task[2]}")
                logger.info(f"  Created: {task[3]}")
                logger.info(f"  Updated: {task[4]}")
                logger.info("")
                
    finally:
        conn.close()

if __name__ == "__main__":
    check_tasks()
