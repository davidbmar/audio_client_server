#!/usr/bin/python3
from urllib.parse import quote, unquote
import logging

logger = logging.getLogger(__name__)

class PathHandler:
    @staticmethod
    def encode_for_storage(raw_path: str) -> str:
        """Always encode paths before storage."""
        logger.debug(f"Encoding path: {raw_path}")
        encoded = quote(raw_path)
        logger.debug(f"Encoded result: {encoded}")
        return encoded
    
    @staticmethod
    def decode_for_use(stored_path: str) -> str:
        """Always decode paths immediately after retrieval."""
        logger.debug(f"Decoding path: {stored_path}")
        decoded = unquote(stored_path)
        logger.debug(f"Decoded result: {decoded}")
        return decoded
