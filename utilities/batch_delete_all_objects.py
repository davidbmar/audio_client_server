#!/usr/bin/python3
import boto3

def list_objects_in_bucket(bucket_name):
    """
    Lists all objects in an S3 bucket.
    
    Parameters:
    - bucket_name (str): The name of the S3 bucket.
    
    Returns:
    - list: A list of object keys in the bucket.
    """
    s3 = boto3.client('s3')
    contents = []
    kwargs = {'Bucket': bucket_name}
    
    while True:
        response = s3.list_objects_v2(**kwargs)
        if 'Contents' in response:
            contents.extend(response['Contents'])
        
        try:
            kwargs['ContinuationToken'] = response['NextContinuationToken']
        except KeyError:
            break
    
    return [content['Key'] for content in contents]

def batch_delete_all_objects(bucket_name):
    """
    Deletes all objects in an S3 bucket in batches.
    
    Parameters:
    - bucket_name (str): The name of the S3 bucket.
    """
    s3 = boto3.client('s3')
    object_keys = list_objects_in_bucket(bucket_name)
    
    if not object_keys:
        print("No objects to delete.")
        return
    
    print(f"Deleting {len(object_keys)} objects from {bucket_name}...")
    
    # Split keys into batches of 1000 for batch delete operation
    for i in range(0, len(object_keys), 1000):
        chunk_keys = object_keys[i:i + 1000]
        
        # Prepare the format for batch delete
        delete_dict = {'Objects': [{'Key': key} for key in chunk_keys]}
        
        # Perform batch delete
        s3.delete_objects(Bucket=bucket_name, Delete=delete_dict)
    
    print("Batch deletion complete.")

if __name__ == "__main__":
    bucket_name = "presigned-url-audio-uploads"  # Replace with your bucket name
    batch_delete_all_objects(bucket_name)
    bucket_name = "audioclientserver-transcribedobjects-public"  # Replace with your bucket name
    batch_delete_all_objects(bucket_name)

