import os
import requests
from typing import Any, Dict, Optional
import io


class RAGClient:
    """
    Simple HTTP client for interacting with the Local RAG API.
    Designed to be UI-friendly: returns dicts with ok/data/error instead of raising.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0):
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

    def upload_file(self, file_content: bytes, filename: str, embedding_provider: str = "ollama", upload_timeout: Optional[float] = None) -> Dict[str, Any]:
        """Upload a file to the RAG API for ingestion.

        Args:
            file_content: The file content as bytes
            filename: The name of the file
            embedding_provider: The embedding provider to use ('ollama' or 'openai')
            upload_timeout: Optional timeout for upload (defaults to adaptive timeout based on file size)

        Returns a dict: {"ok": bool, "data": {...}} on success or {"ok": False, "error": str} on error.
        """
        # Validate inputs
        if not filename:
            return {"ok": False, "error": "Filename cannot be empty"}
        
        if not filename.lower().endswith('.txt'):
            return {"ok": False, "error": "Only .txt files are supported"}
        
        if not file_content:
            return {"ok": False, "error": "File content cannot be empty"}
        
        # Validate file size (maximum 10MB)
        file_size_mb = len(file_content) / (1024 * 1024)
        max_size_mb = 10.0
        if file_size_mb > max_size_mb:
            return {"ok": False, "error": f"File too large ({file_size_mb:.2f} MB). Maximum size allowed is {max_size_mb} MB"}
        
        # Calculate adaptive timeout based on file size
        if upload_timeout is None:
            # Base timeout of 60s + 30s per MB (minimum 120s, maximum 600s)
            adaptive_timeout = max(120.0, min(600.0, 60.0 + (file_size_mb * 30.0)))
        else:
            adaptive_timeout = upload_timeout
        
        endpoint = f"{self.base_url}/api/v1/ingest"
        
        try:
            # Create a file-like object from bytes
            file_obj = io.BytesIO(file_content)
            
            # Prepare the files parameter for multipart/form-data
            files = {
                "file": (filename, file_obj, "text/plain")
            }
            
            # Prepare the data payload
            data = {
                "embedding_provider": embedding_provider
            }
            
            resp = requests.post(endpoint, files=files, data=data, timeout=adaptive_timeout)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

