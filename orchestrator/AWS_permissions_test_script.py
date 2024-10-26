#!/usr/bin/python3
import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_permissions():
    try:
        # Test SQS permissions
        sqs = boto3.client('sqs', region_name='us-east-2')
        queue_url = "https://sqs.us-east-2.amazonaws.com/635071011057/2024-09-23-audiotranscribe-my-application-queue"
        
        logger.info("Testing SQS permissions...")
        sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        logger.info("✓ Can access SQS queue")
        
        # Test S3 permissions
        s3 = boto3.client('s3', region_name='us-east-2')
        logger.info("Testing S3 permissions...")
        s3.head_bucket(Bucket='2024-09-23-audiotranscribe-input-bucket')
        logger.info("✓ Can access input S3 bucket")
        
        # Test Secrets Manager permissions
        secrets = boto3.client('secretsmanager', region_name='us-east-2')
        logger.info("Testing Secrets Manager permissions...")
        secrets.get_secret_value(SecretId='/DEV/audioClientServer/Orchestrator/v2')
        logger.info("✓ Can access secrets")
        
        # Test DB connection
        secret = json.loads(secrets.get_secret_value(SecretId='/DEV/audioClientServer/Orchestrator/v2')['SecretString'])
        import psycopg2
        logger.info("Testing database connection...")
        conn = psycopg2.connect(
            host=secret['db_host'].split(':')[0],
            port=int(secret['db_host'].split(':')[1]),
            database=secret['db_name'],
            user=secret['db_username'],
            password=secret['db_password']
        )
        conn.close()
        logger.info("✓ Can connect to database")
        
    except Exception as e:
        logger.error("Permission test failed: %s", str(e))

if __name__ == "__main__":
    test_permissions()
