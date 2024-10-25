# This is deprecated, because the worker node should NEVER talk to the DB directly, but instead should go always through the API.
# this is because the worker node could be in runpod, or in another AWS account.
import psycopg2

try:
    connection = psycopg2.connect(
        host="terraform-20241016020051445600000001.cny2uiqswlls.us-east-2.rds.amazonaws.com",
        database="dbm_my_rds_db",
        user="dbm_db_admin",
        password="mysecurepassword"
    )
    print("Database connection successful.")
    connection.close()
except Exception as e:
    print(f"Database connection failed: {e}")



