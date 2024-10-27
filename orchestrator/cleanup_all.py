#!/usr/bin/python3
import boto3
import psycopg2
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secrets():
    """Retrieve configuration from AWS Secrets Manager."""
    secret_name = "/DEV/audioClientServer/Orchestrator/v2"
    region_name = "us-east-2"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    secret_value = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value['SecretString'])

def cleanup_s3(bucket_name):
    """Delete all objects in the specified S3 bucket."""
    s3 = boto3.client('s3')
    try:
        # List all objects in the bucket
        paginator = s3.get_paginator('list_objects_v2')
        count = 0
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                if objects:
                    s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects}
                    )
                    count += len(objects)
        
        logger.info(f"Deleted {count} objects from bucket {bucket_name}")
    except Exception as e:
        logger.error(f"Error cleaning S3 bucket {bucket_name}: {e}")

def cleanup_sqs(queue_url):
    """Purge all messages from the specified SQS queue."""
    sqs = boto3.client('sqs')
    try:
        # Purge the queue
        sqs.purge_queue(QueueUrl=queue_url)
        logger.info(f"Purged queue {queue_url}")
    except Exception as e:
        logger.error(f"Error purging queue {queue_url}: {e}")

def cleanup_database():
    """Clean up the database tables."""
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
            # Truncate the tasks table
            cursor.execute("TRUNCATE TABLE tasks")
            conn.commit()
            logger.info("Cleaned up database tables")
    except Exception as e:
        logger.error(f"Error cleaning database: {e}")
    finally:
        conn.close()

def main():
    """Perform complete cleanup."""
    try:
        secrets = get_secrets()
        
        # Clean up S3 buckets
        cleanup_s3(secrets['input_bucket'])
        cleanup_s3(secrets['output_bucket'])
        
        # Clean up SQS queues
        cleanup_sqs(secrets['task_queue_url'])
        cleanup_sqs(secrets['status_update_queue_url'])
        
        # Clean up database
        cleanup_database()
        
        logger.info("Cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()
