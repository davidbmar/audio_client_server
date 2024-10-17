#!/usr/bin/python3
import psycopg2
import boto3
import json

# Function to retrieve DB credentials from AWS Secrets Manager
def get_db_credentials(secret_name):
    client = boto3.client("secretsmanager", region_name="us-east-2")
    secret_value = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_value["SecretString"])
    return secret

# Pull credentials from AWS Secrets Manager
db_credentials = get_db_credentials("RDS_DB_Credentials")  # Your secret name here

# Establish connection to the PostgreSQL database
try:
    connection = psycopg2.connect(
        user=db_credentials["db_user"],
        password=db_credentials["db_password"],
        host=db_credentials["db_host"],
        database=db_credentials["db_name"],  # Name of your DB created during the setup
        port="5432"
    )
    cursor = connection.cursor()

    # Fetch data from the `tasks` table
    fetch_query = "SELECT * FROM tasks"
    cursor.execute(fetch_query)
    result = cursor.fetchall()

    # Print out the results
    for row in result:
        print(f"Task ID: {row[0]}, Status: {row[3]}, Created At: {row[4]}")

except (Exception, psycopg2.DatabaseError) as error:
    print(f"Error fetching data from PostgreSQL: {error}")
finally:
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection closed")

