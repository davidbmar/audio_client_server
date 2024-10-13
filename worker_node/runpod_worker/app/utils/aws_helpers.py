# file: utils/aws_helpers.py

import hashlib
import logging
import requests

logger = logging.getLogger(__name__)

def compute_md5(file_path: str) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

