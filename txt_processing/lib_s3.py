#!/usr/bin/python3
# s3_uploader.py

import boto3
from botocore.exceptions import NoCredentialsError

class S3Uploader:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3')

    def upload_file(self, file_name, object_name=None):
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param object_name: S3 object name. If not specified, file_name is used
        :return: True if file was uploaded, else False
        """
        if object_name is None:
            object_name = file_name

        try:
            self.s3.upload_file(file_name, self.bucket_name, object_name)
            print(f"File {file_name} uploaded to {self.bucket_name}/{object_name}")
            return True
        except NoCredentialsError:
            print("Credentials not available")
            return False

