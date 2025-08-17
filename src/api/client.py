import os
import requests
from typing import Any, Dict, Optional
import io


class RAGClient:
    """
    Simple HTTP client for interacting with the Local RAG API.
    Designed to be UI-friendly: returns dicts with ok/data/error instead of raising.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = timeout

    def query(self, question: str) -> Dict[str, Any]:
        """Send a question to the RAG API and return response dict.

        Returns a dict: {"ok": bool, "data": {...}} on success or {"ok": False, "error": str} on error.
        """
        endpoint = f"{self.base_url}/api/v1/query"
        try:
            resp = requests.post(endpoint, json={"question": question}, timeout=self.timeout)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    def upload_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload a file to the RAG API for ingestion.

        Args:
            file_content: The file content as bytes
            filename: The name of the file

        Returns a dict: {"ok": bool, "data": {...}} on success or {"ok": False, "error": str} on error.
        """
        # Validate inputs
        if not filename:
            return {"ok": False, "error": "Filename cannot be empty"}
        
        if not filename.lower().endswith('.txt'):
            return {"ok": False, "error": "Only .txt files are supported"}
        
        if not file_content:
            return {"ok": False, "error": "File content cannot be empty"}
        
        endpoint = f"{self.base_url}/api/v1/ingest"
        
        try:
            # Create a file-like object from bytes
            file_obj = io.BytesIO(file_content)
            
            # Prepare the files parameter for multipart/form-data
            files = {
                "file": (filename, file_obj, "text/plain")
            }
            
            resp = requests.post(endpoint, files=files, timeout=self.timeout)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

