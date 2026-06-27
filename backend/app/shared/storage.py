"""
File storage utilities.

Handles file uploads and storage operations.
"""

import os
import shutil
from pathlib import Path
from typing import Tuple
import logging
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


def save_uploaded_file(file_path: str, file_content: bytes) -> Tuple[bool, str]:
    """
    Save uploaded file to disk.

    Args:
        file_path: Relative path within upload directory
        file_content: File content as bytes

    Returns:
        tuple: (success, full_path or error_message)
    """
    try:
        full_path = os.path.join(settings.UPLOAD_DIRECTORY, file_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save file
        with open(full_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"File saved: {full_path}")
        return True, full_path
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return False, str(e)


def delete_file(file_path: str) -> Tuple[bool, str]:
    """
    Delete a file from storage.

    Args:
        file_path: File path

    Returns:
        tuple: (success, message)
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True, "File deleted successfully"
        return False, "File not found"
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False, str(e)


def read_excel_file(file_path: str) -> pd.DataFrame:
    """
    Read Excel file into DataFrame.

    Args:
        file_path: Path to Excel file

    Returns:
        pd.DataFrame: Data from Excel file

    Raises:
        Exception: If file cannot be read
    """
    try:
        # Read first sheet
        df = pd.read_excel(file_path, sheet_name=0)
        logger.info(f"Excel file read successfully: {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        raise


def read_csv_file(file_path: str) -> pd.DataFrame:
    """
    Read CSV file into DataFrame.

    Args:
        file_path: Path to CSV file

    Returns:
        pd.DataFrame: Data from CSV file

    Raises:
        Exception: If file cannot be read
    """
    try:
        # Try with common encodings
        for encoding in ["utf-8", "iso-8859-1", "cp1252"]:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"CSV file read successfully: {file_path}")
                return df
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, raise error
        raise ValueError("Could not read CSV file with any supported encoding")
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        raise


def validate_file_type(filename: str) -> Tuple[bool, str]:
    """
    Validate file type based on extension.

    Args:
        filename: Original filename

    Returns:
        tuple: (is_valid, error_message)
    """
    valid_extensions = [".csv", ".xlsx", ".xls"]
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in valid_extensions:
        return False, f"Invalid file type. Supported: {', '.join(valid_extensions)}"
    
    return True, ""


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Validate file size.

    Args:
        file_size: File size in bytes

    Returns:
        tuple: (is_valid, error_message)
    """
    max_size = settings.MAX_UPLOAD_SIZE
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File size exceeds limit of {max_mb}MB"
    
    return True, ""
