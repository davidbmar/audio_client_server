#!/usr/bin/python3
import boto3
import psycopg2
import json
import logging
import time
from urllib.parse import unquote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secrets():
    """Your existing get_secrets() function"""
    secret_name = "/DEV/audioClientServer/Orchestrator/v2"
    region_name = "us-east-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    secret_value = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value['SecretString'])

def normalize_keys(bucket_name):
    """Check and normalize any incorrectly encoded keys in S3."""
    s3 = boto3.client('s3')
    try:
        paginator = s3.get_paginator('list_objects_v2')
        fixed = 0

        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                for obj in page['Contents']:
                    old_key = obj['Key']
                    # Decode key completely
                    decoded = unquote(unquote(old_key))
                    # Encode once properly
                    new_key = decoded
                    
                    if old_key != new_key:
                        logger.info(f"Fixing key encoding: {old_key} -> {new_key}")
                        # Copy object with correct key
                        s3.copy_object(
                            Bucket=bucket_name,
                            CopySource={'Bucket': bucket_name, 'Key': old_key},
                            Key=new_key
                        )
                        # Delete old object
                        s3.delete_object(Bucket=bucket_name, Key=old_key)
                        fixed += 1

        logger.info(f"Fixed {fixed} incorrectly encoded keys in bucket {bucket_name}")
    except Exception as e:
        logger.error(f"Error normalizing keys in bucket {bucket_name}: {e}")

def cleanup_s3(bucket_name):
    """Delete all objects in the specified S3 bucket."""
    s3 = boto3.client('s3')
    try:
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
        
        # Wait a moment to ensure purge completes
        time.sleep(2)
        
        # Verify queue is empty
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 
                          'ApproximateNumberOfMessagesNotVisible']
        )['Attributes']
        
        if int(attrs['ApproximateNumberOfMessages']) > 0 or \
           int(attrs['ApproximateNumberOfMessagesNotVisible']) > 0:
            logger.warning(f"Queue {queue_url} may not be fully purged")
            
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
            # Get counts before cleanup
            cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            before_counts = cursor.fetchall()
            logger.info("Before cleanup task counts:")
            for status, count in before_counts:
                logger.info(f"- {status}: {count}")

            # Truncate the tasks table
            cursor.execute("TRUNCATE TABLE tasks")
            conn.commit()
            logger.info("Cleaned up database tables")

    except Exception as e:
        logger.error(f"Error cleaning database: {e}")
        conn.rollback()
    finally:
        conn.close()

def verify_clean_state(secrets):
    """Verify everything is in a clean state."""
    try:
        # Check S3 buckets
        s3 = boto3.client('s3')
        for bucket in [secrets['input_bucket'], secrets['output_bucket']]:
            response = s3.list_objects_v2(Bucket=bucket)
            if response.get('KeyCount', 0) > 0:
                logger.warning(f"Bucket {bucket} still has {response['KeyCount']} objects")

        # Check SQS queues
        sqs = boto3.client('sqs')
        for queue_url in [secrets['task_queue_url'], secrets['status_update_queue_url']]:
            attrs = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 
                              'ApproximateNumberOfMessagesNotVisible']
            )['Attributes']
            
            if int(attrs['ApproximateNumberOfMessages']) > 0 or \
               int(attrs['ApproximateNumberOfMessagesNotVisible']) > 0:
                logger.warning(f"Queue {queue_url} still has messages")

        # Check database
        host, port = secrets['db_host'].split(':')
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=secrets['db_name'],
            user=secrets['db_username'],
            password=secrets['db_password']
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tasks")
            count = cursor.fetchone()[0]
            if count > 0:
                logger.warning(f"Database still has {count} tasks")

        conn.close()

    except Exception as e:
        logger.error(f"Error verifying clean state: {e}")

def main():
    """Perform complete cleanup."""
    try:
        secrets = get_secrets()

        # Clean up S3 buckets
        for bucket in [secrets['input_bucket'], secrets['output_bucket']]:
            cleanup_s3(bucket)
            normalize_keys(bucket)

        # Clean up SQS queues
        for queue_url in [secrets['task_queue_url'], secrets['status_update_queue_url']]:
            cleanup_sqs(queue_url)

        # Clean up database
        cleanup_database()

        # Verify clean state
        logger.info("Verifying clean state...")
        verify_clean_state(secrets)

        logger.info("Cleanup completed successfully!")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()
