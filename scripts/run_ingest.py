#!/usr/bin/env python3
"""
CLI tool for uploading documents to the RAG system via API.

Usage:
    python scripts/run_ingest.py --file path/to/document.txt
    python scripts/run_ingest.py --file document.txt --api-url http://localhost:8000
"""

import argparse
import sys
import os
from pathlib import Path
import requests
from typing import Optional
import json

# Add src to Python path to access settings if needed
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.config.settings import settings
    DEFAULT_API_URL = f"http://{settings.api_host}:{settings.api_port}"
except ImportError:
    DEFAULT_API_URL = "http://localhost:8000"


def validate_file_exists(file_path: str) -> bool:
    """Check if the file exists and is readable"""
    if not os.path.exists(file_path):
        return False
    if not os.path.isfile(file_path):
        return False
    if not os.access(file_path, os.R_OK):
        return False
    return True


def validate_file_type(file_path: str) -> bool:
    """Check if file has .txt extension"""
    return file_path.lower().endswith('.txt')


def upload_file(file_path: str, api_url: str) -> dict:
    """
    Upload file to the RAG API
    
    Args:
        file_path: Path to the file to upload
        api_url: Base URL of the API
        
    Returns:
        Response data from the API
        
    Raises:
        requests.exceptions.ConnectionError: If API is not reachable
        requests.exceptions.RequestException: For other HTTP errors
    """
    endpoint = f"{api_url}/api/v1/ingest"
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'text/plain')}
        
        response = requests.post(endpoint, files=files, timeout=300)  # 5 min timeout
        response.raise_for_status()
        
        return response.json()


def print_response(response_data: dict, status_code: int):
    """Print the API response in a user-friendly format"""
    print(f"\n✅ Success! (Status: {status_code})")
    print(f"📄 File: {response_data.get('filename', 'Unknown')}")
    print(f"📊 Status: {response_data.get('status', 'Unknown')}")
    
    if 'document_id' in response_data:
        print(f"🆔 Document ID: {response_data['document_id']}")
    
    if 'chunks_created' in response_data:
        print(f"📝 Chunks created: {response_data['chunks_created']}")
    
    if 'message' in response_data:
        print(f"💬 Message: {response_data['message']}")
    
    print(f"\n📋 Full Response:")
    print(json.dumps(response_data, indent=2, ensure_ascii=False))


def print_error(error_message: str, error_type: str = "ERROR"):
    """Print error message in a user-friendly format"""
    print(f"\n❌ {error_type}: {error_message}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload documents to the RAG system via API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_ingest.py --file document.txt
  python scripts/run_ingest.py --file /path/to/document.txt --api-url http://localhost:8000
  python scripts/run_ingest.py --file example.txt --verbose
        """
    )
    
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the .txt file to upload"
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help=f"Base URL of the RAG API (default: {DEFAULT_API_URL})"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"🔧 Using API URL: {args.api_url}")
        print(f"📁 File to upload: {args.file}")
    
    # Validate file exists
    if not validate_file_exists(args.file):
        print_error("File not found or not readable. Please check the file path.", "FILE ERROR")
        sys.exit(1)
    
    # Validate file type
    if not validate_file_type(args.file):
        print_error("Only .txt files are supported. Please provide a text file.", "FILE TYPE ERROR")
        sys.exit(1)
    
    if args.verbose:
        file_size = os.path.getsize(args.file)
        print(f"📊 File size: {file_size} bytes")
    
    try:
        print(f"📤 Uploading {os.path.basename(args.file)} to {args.api_url}...")
        
        response_data = upload_file(args.file, args.api_url)
        print_response(response_data, 201)
        
    except requests.exceptions.ConnectionError:
        print_error(
            f"Could not connect to the API at {args.api_url}. "
            "Please ensure the RAG API server is running.",
            "CONNECTION ERROR"
        )
        sys.exit(1)
        
    except requests.exceptions.Timeout:
        print_error(
            "Request timed out. The file might be too large or the server is overloaded.",
            "TIMEOUT ERROR"
        )
        sys.exit(1)
        
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            detail = error_data.get('detail', str(e))
        except (ValueError, AttributeError):
            detail = str(e)
        
        print_error(
            f"HTTP {e.response.status_code}: {detail}",
            "API ERROR"
        )
        sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}", "REQUEST ERROR")
        sys.exit(1)
        
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}", "UNEXPECTED ERROR")
        sys.exit(1)
    
    print("\n🎉 Document upload completed successfully!")


if __name__ == "__main__":
    main()