import json
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import pydantic_core

from survision_simulator.device_logic import DeviceLogic
from survision_simulator.models import parse_message, requires_locking, is_prohibited_over_http


class SurvisionHTTPHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the Survision device simulator.
    Handles HTTP requests to the /sync endpoint and serves static files for the web UI.
    """
    
    # Class variable to store device logic reference
    device_logic: Optional[DeviceLogic] = None
    
    # Directory containing static files
    static_dir: str = ""
    
    # Logger
    logger = logging.getLogger("simulator.http")
    
    def do_GET(self) -> None:
        """Handle GET requests (for static files)."""
        # Serve static files for web UI
        if self.path == "/":
            self.path = "/index.html"
        
        # Try to serve a static file
        file_path = os.path.join(self.static_dir, self.path.lstrip("/"))
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self._serve_static_file(file_path)
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self) -> None:
        """Handle POST requests (for /sync endpoint)."""
        if self.path == "/sync":
            self._handle_sync_request()
        else:
            self.send_error(404, "Endpoint not found")
    
    def _handle_sync_request(self) -> None:
        """Handle a request to the /sync endpoint."""
        # Check if device logic is available
        if not self.device_logic:
            self.send_error(500, "Server not properly initialized")
            return
        
        # Get content length
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            self.send_error(400, "Empty request body")
            return
        
        # Read request body
        request_body = self.rfile.read(content_length)
        
        # Parse JSON
        try:
            message = parse_message(request_body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
            return
        except ValueError as e:
            self.send_error(400, str(e))
            return
        
        # Check for prohibited operations
        if is_prohibited_over_http(message):
            message_type = type(message).__name__
            if message_type.endswith("Message"):
                message_type = message_type[:-7]  # Remove "Message"
            self.send_error(400, f"Operation {message_type} is prohibited over HTTP")
            return
        
        # Handle implicit locking if needed
        password = self.headers.get("Password")
        locked = False
        
        if requires_locking(message):
            # Try to lock the device
            locked = self._implicit_lock(password)
            if not locked:
                self.send_error(403, "Device is locked or invalid password")
                return
        
        try:
            # Process message
            response, status_code = self.device_logic.process_message(message)
            
            # Send response
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            response_json_bytes = pydantic_core.to_json(response, by_alias=True)
            self.wfile.write(response_json_bytes)
        finally:
            # Implicit unlock if we locked the device
            if locked:
                self._implicit_unlock()
    
    def _implicit_lock(self, password: Optional[str]) -> bool:
        """
        Implicitly lock the device.
        
        Args:
            password: The password to use for locking
            
        Returns:
            True if the device was successfully locked, False otherwise
        """
        if not self.device_logic:
            return False
        
        # Check if device is already locked
        if self.device_logic.data_store.is_device_locked():
            return False
        
        # Lock the device
        return self.device_logic.data_store.lock_device(password)
    
    def _implicit_unlock(self) -> None:
        """Implicitly unlock the device."""
        if self.device_logic:
            self.device_logic.data_store.unlock_device()
    
    def _serve_static_file(self, file_path: str) -> None:
        """
        Serve a static file.
        
        Args:
            file_path: Path to the file
        """
        # Determine content type based on file extension
        _, ext = os.path.splitext(file_path)
        content_type = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml"
        }.get(ext.lower(), "application/octet-stream")
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except IOError:
            self.send_error(500, f"Error reading file: {file_path}")


class SurvisionHTTPServer:
    """
    HTTP server for the Survision device simulator.
    """
    
    def __init__(self, host: str, port: int, device_logic: DeviceLogic, static_dir: str):
        """
        Initialize the HTTP server.
        
        Args:
            host: Host address
            port: Port number
            device_logic: Device logic instance
            static_dir: Directory containing static files
        """
        self.host = host
        self.port = port
        self.device_logic = device_logic
        self.static_dir = static_dir
        self.server: Optional[HTTPServer] = None
        self.logger = logging.getLogger("simulator.http")
        
        # Set class variables in handler
        SurvisionHTTPHandler.device_logic = device_logic
        SurvisionHTTPHandler.static_dir = static_dir
    
    def start(self) -> None:
        """Start the HTTP server."""
        self.server = HTTPServer((self.host, self.port), SurvisionHTTPHandler)
        self.logger.info(f"HTTP server started at http://{self.host}:{self.port}")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
    
    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.logger.info("HTTP server stopped")
