#!/usr/bin/python3
import requests

# Configuration
GET_URL_ENDPOINT = "http://localhost:8000/api/get-presigned-url"  # URL of the service generating pre-signed URLs
TEST_FILE = "test.webm"  # Replace with the path to your test file


def get_presigned_url():
    """Fetches a pre-signed URL from the service."""
    try:
        response = requests.get(GET_URL_ENDPOINT)
        response.raise_for_status()
        data = response.json()
        print(f"Pre-signed URL retrieved: {data['url']}")
        return data['url'], data['key']
    except requests.RequestException as e:
        print(f"Error fetching pre-signed URL: {e}")
        return None, None


def upload_file(url, file_path):
    """Uploads a file to S3 using the pre-signed URL."""
    try:
        headers = {
            "Content-Type": "audio/webm",  # Ensure this matches the ContentType in the pre-signed URL
            "x-amz-acl": "private"  # Ensure this matches the ACL in the pre-signed URL
        }

        with open(file_path, "rb") as file:
            response = requests.put(url, headers=headers, data=file)
            response.raise_for_status()

        print(f"File uploaded successfully to {url.split('?')[0]}")
    except requests.RequestException as e:
        print(f"Error uploading file: {e}")


def main():
    """Main function to test pre-signed URL upload."""
    print("Fetching pre-signed URL...")
    url, key = get_presigned_url()
    if not url:
        print("Failed to retrieve pre-signed URL. Exiting.")
        return

    print(f"Uploading file '{TEST_FILE}' to S3...")
    upload_file(url, TEST_FILE)
    print(f"File uploaded to S3 at key: {key}")


if __name__ == "__main__":
    main()

