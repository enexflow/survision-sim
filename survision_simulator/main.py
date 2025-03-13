import os
import signal
import sys
import threading
import time
import logging
import logging.config
from typing import Optional, Any

from survision_simulator.config_manager import ConfigManager
from survision_simulator.data_store import DataStore
from survision_simulator.device_logic import DeviceLogic
from survision_simulator.server.http_server import SurvisionHTTPServer
from survision_simulator.server.websocket_server import SurvisionWebSocketServer


class SurvisionSimulator:
    """
    Main class for the Survision device simulator.
    Initializes and manages all components.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the simulator.
        
        Args:
            config_file: Path to the configuration file
        """
        # Setup logging
        self.logger = logging.getLogger("simulator.main")
        
        # Initialize components
        self.config_manager = ConfigManager(config_file)
        self.data_store = DataStore()
        self.device_logic = DeviceLogic(self.config_manager, self.data_store)
        
        # Get configuration values
        host = self.config_manager.get_value("ipAddress", "127.0.0.1")
        http_port = self.config_manager.get_value("httpPort", 8080)
        ws_port = self.config_manager.get_value("wsPort", 10001)
        
        # Get static files directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(current_dir, "webui", "static_files")
        
        # Initialize servers
        self.http_server = SurvisionHTTPServer(host, http_port, self.device_logic, static_dir)
        self.ws_server = SurvisionWebSocketServer(host, ws_port, self.device_logic, self.data_store)
        
        # Server threads
        self.http_thread: Optional[threading.Thread] = None
        self.running = False
    
    def start(self) -> None:
        """Start the simulator."""
        self.running = True
        
        # Start WebSocket server
        self.ws_server.start()
        
        # Start HTTP server in the main thread
        self.http_thread = threading.Thread(target=self.http_server.start)
        self.http_thread.daemon = True
        self.http_thread.start()
        
        self.logger.info("Survision Device Simulator started")
        self.logger.info(f"HTTP server: http://{self.config_manager.get_value('ipAddress', '127.0.0.1')}:{self.config_manager.get_value('httpPort', 8080)}")
        self.logger.info(f"WebSocket server: ws://{self.config_manager.get_value('ipAddress', '127.0.0.1')}:{self.config_manager.get_value('wsPort', 10001)}/async")
        self.logger.info("Press Ctrl+C to stop")
        
        # Keep the main thread running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop the simulator."""
        self.running = False
        
        # Stop servers
        self.ws_server.stop()
        self.http_server.stop()
        
        self.logger.info("Survision Device Simulator stopped")


def signal_handler(sig: int, frame: Any) -> None:
    """
    Handle signals (e.g., SIGINT).
    
    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger = logging.getLogger("simulator.main")
    logger.info("Received signal to terminate")
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start simulator
    simulator = SurvisionSimulator()
    simulator.start()


if __name__ == "__main__":
    main()
