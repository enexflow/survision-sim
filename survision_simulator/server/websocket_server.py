import asyncio
import json
import logging
import threading
from typing import Dict, Any, Optional, Set

import websockets
from websockets.legacy.server import WebSocketServerProtocol, serve

from survision_simulator.device_logic import DeviceLogic
from survision_simulator.data_store import DataStore
from survision_simulator.models import ErrorResponse, StreamAnswer


class SurvisionWebSocketServer:
    """
    WebSocket server for the Survision device simulator.
    Handles asynchronous communication with clients.
    """
    
    def __init__(self, host: str, port: int, device_logic: DeviceLogic, data_store: DataStore):
        """
        Initialize the WebSocket server.
        
        Args:
            host: Host address
            port: Port number
            device_logic: Device logic instance
            data_store: Data store instance
        """
        self.host = host
        self.port = port
        self.device_logic = device_logic
        self.data_store = data_store
        self.server = None
        self.clients: Set[WebSocketServerProtocol] = set()
        self.running = False
        self.thread = None
        self.loop = None
        self.logger = logging.getLogger("simulator.websocket")
    
    def start(self):
        """Start the WebSocket server in a separate thread."""
        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the WebSocket server."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        self.logger.info("WebSocket server stopped")
    
    def _run_server(self):
        """Run the WebSocket server event loop."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        
        # Define the server coroutine
        async def start_server():
            # Define the handler for each connection
            async def handler(websocket: WebSocketServerProtocol) -> None:
                # Check path from request headers
                path = websocket.path
                if path != "/async":
                    await websocket.close(1008, "Invalid endpoint")
                    return
                
                # Register client
                self.clients.add(websocket)
                self.data_store.register_ws_client(websocket)
                
                try:
                    # Handle client messages
                    async for message in websocket:
                        try:
                            # Process message
                            msg_bytes = message if isinstance(message, bytes) else message.encode("utf-8")
                            
                            # For WebSockets, locking must be explicit via the lock message
                            # We don't need to check for locked operations here as that's handled by the device logic
                            response = self.device_logic.process_websocket_message(msg_bytes)
                            
                            # Update client subscriptions if needed
                            if response and isinstance(response, StreamAnswer):
                                self.data_store.update_ws_client_subscriptions(websocket, response.subscriptions)
                            
                            # Send response if needed
                            if response:
                                await websocket.send(response.model_dump_json())
                        except Exception as e:
                            # Other errors
                            err_type = type(e).__name__
                            err_msg = str(e)
                            await websocket.send(ErrorResponse.for_error_text(f"{err_type}: {err_msg}").as_answer().model_dump_json())
                except websockets.exceptions.ConnectionClosed:
                    pass
                finally:
                    # Unregister client
                    self.clients.remove(websocket)
                    self.data_store.unregister_ws_client(websocket)
            
            # Start the server
            server = await serve(handler, self.host, self.port)
            self.server = server
            self.logger.info(f"WebSocket server: ws://{self.host}:{self.port}/async")
            
            # Keep the server running until stopped
            while self.running:
                await asyncio.sleep(1)
            
            # Close the server when done
            if self.server:
                self.server.close()
                await self.server.wait_closed()
        
        # Run the server coroutine
        try:
            loop.run_until_complete(start_server())
        except Exception as e:
            self.logger.error(f"WebSocket server error: {e}")
        finally:
            loop.close()
    
    def broadcast_message_sync(self, message: Dict[str, Any], event_type: Optional[str] = None):
        """
        Synchronous wrapper for broadcast_message.
        
        Args:
            message: Message to broadcast
            event_type: Event type for filtering clients
        """
        if not self.running or not self.clients or not self.loop:
            return
        
        # Define the broadcast coroutine
        async def broadcast():
            if not self.clients:
                return
            
            # Convert message to JSON
            message_json = json.dumps(message)
            
            # Get clients to broadcast to
            clients = []
            if event_type:
                clients = self.data_store.get_ws_clients_for_event(event_type)
            else:
                clients = list(self.clients)
            
            # Send message to each client
            for client in clients:
                if client in self.clients:  # Check if client is still connected
                    try:
                        await client.send(message_json)
                    except websockets.exceptions.ConnectionClosed:
                        pass
        
        # Run the broadcast coroutine in the server's event loop
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(), self.loop)
