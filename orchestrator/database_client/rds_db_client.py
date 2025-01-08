#!/usr/bin/python3
import psycopg2
import boto3
import json

# Function to retrieve secrets from AWS Secrets Manager
def get_secrets():
    secret_name = "/DEV/audioClientServer/Orchestrator/v2"  # Using same secret path as first script
    secrets_client = boto3.client('secretsmanager', region_name='us-east-2')
    secret_value = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value['SecretString'])

# Pull credentials from AWS Secrets Manager
secrets = get_secrets()

# Establish connection to the PostgreSQL database
try:
    host, port = secrets['db_host'].split(':')  # Parse host:port like first script
    connection = psycopg2.connect(
        user=secrets['db_username'],      # Match secret key names from first script
        password=secrets['db_password'],
        host=host,
        port=int(port),
        database=secrets['db_name']
    )
    cursor = connection.cursor()

    # Fetch data from the `tasks` table
    fetch_query = "SELECT * FROM tasks"
    cursor.execute(fetch_query)
    result = cursor.fetchall()

    # Print out the results with aligned columns
    for row in result:
        print(f"Task ID: {row[0]:<36} Status: {row[3]:<10} Created At: {row[4]}")

except (Exception, psycopg2.DatabaseError) as error:
    print(f"Error fetching data from PostgreSQL: {error}")
finally:
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection closed")
