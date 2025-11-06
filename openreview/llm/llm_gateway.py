"""Wrapper using litellm for OpenReview LLM integration."""

import base64
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import requests
from urllib.parse import urlparse


class LLMGateway:
    """Wrapper class for LLM using litellm with PDF upload support."""
    
    def __init__(self, api_key: str, model: str = "gemini/gemini-2.0-flash"):
        """
        Initialize the LLM wrapper.

        Args:
            api_key: The LLM API key
            model: The LLM model to use (default: gemini/gemini-2.0-flash)
        """
        
        self.api_key = api_key
        self.model = model
        self.system_message = None

    def set_system_message(self, message: str):
        """
        Set a system message to be included in all completions.

        Args:
            message: The system message content
        """
        self.system_message = message

    def completion(
        self, 
        messages: List[Dict[str, Any]], 
        **kwargs
    ) -> Any:
        """
        Generate a completion using the Gemini model.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments to pass to litellm.completion
            
        Returns:
            litellm completion response
        """
        import litellm  # Local import to avoid dependency if not used

        # Prepend system message if set
        if self.system_message is not None:
            system_msg = {"role": "system", "content": self.system_message}
            messages = [system_msg] + messages
            
        return litellm.completion(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            **kwargs
        )
    
    def chat(
        self, 
        prompt: str, 
        pdf_path: Optional[Union[str, Path]] = None,
        pdf_attachment: Optional[bytes] = None,
        **kwargs
    ) -> str:
        """
        Simple chat interface with optional PDF upload.
        
        Args:
            prompt: The text prompt
            pdf_path: Optional path to PDF file or URL to upload
            pdf_attachment: Optional PDF binary content (e.g., from get_attachment method)
            **kwargs: Additional arguments to pass to completion
            
        Returns:
            The response content as string
        """
        content = [{"type": "text", "text": prompt}]
        
        if pdf_path and pdf_attachment:
            raise ValueError("Cannot specify both pdf_path and pdf_attachment")
        
        if pdf_path:
            pdf_data = self._encode_pdf(pdf_path)
            content.append({
                "type": "file",
                "file": {
                    "file_data": pdf_data
                }
            })
        elif pdf_attachment:
            pdf_base64 = self.encode_pdf_from_bytes(pdf_attachment)
            content.append({
                "type": "file",
                "file": {
                    "file_data": f"data:application/pdf;base64,{pdf_base64}"
                }
            })
        
        messages = [{"role": "user", "content": content}]
        response = self.completion(messages, **kwargs)
        
        return response.choices[0].message.content
    
    def _encode_pdf(self, pdf_path: Union[str, Path]) -> str:
        """
        Encode a PDF file to base64 from local path or URL.
        
        Args:
            pdf_path: Path to the PDF file or URL
            
        Returns:
            Base64 encoded PDF with data URI prefix
        """
        pdf_str = str(pdf_path)
        
        # Check if it's a URL
        if self._is_url(pdf_str):
            pdf_bytes = self._download_pdf(pdf_str)
        else:
            # Handle as local file path
            pdf_path = Path(pdf_path)
            
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            if not pdf_path.suffix.lower() == '.pdf':
                raise ValueError(f"File must be a PDF: {pdf_path}")
            
            pdf_bytes = pdf_path.read_bytes()
        
        encoded_data = base64.b64encode(pdf_bytes).decode("utf-8")
        return f"data:application/pdf;base64,{encoded_data}"
    
    def _is_url(self, path: str) -> bool:
        """Check if a string is a valid URL."""
        parsed = urlparse(path)
        return parsed.scheme in ('http', 'https')
    
    def _download_pdf(self, url: str) -> bytes:
        """Download PDF from URL and return bytes."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if content type is PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                # Also check if URL ends with .pdf
                if not url.lower().endswith('.pdf'):
                    raise ValueError(f"URL does not point to a PDF file: {url}")
            
            return response.content
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to download PDF from URL {url}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error processing PDF from URL {url}: {e}")
        
    def encode_pdf_from_bytes(self, pdf_bytes: bytes) -> str:
        """
        Encode PDF bytes to base64.
        
        Args:
            pdf_bytes: PDF file bytes
            
        Returns:
            Base64 encoded PDF string (without data URI prefix)
        """
        return base64.b64encode(pdf_bytes).decode("utf-8")
    
    def set_model(self, model: str) -> None:
        """
        Change the model being used.
        
        Args:
            model: New model name (e.g., "gemini/gemini-pro", "gemini/gemini-1.5-flash")
        """
        self.model = model
