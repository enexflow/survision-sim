import threading
import time
from typing import Dict, List, Any, Optional, Set


class DataStore:
    """
    In-memory data store for the Survision device simulator.
    Handles storage of device state, database plates, and logs.
    Thread-safe access for read/write operations.
    """
    
    def __init__(self):
        """Initialize the data store with default values."""
        self._lock = threading.RLock()
        
        # Device state
        self._is_locked = False
        self._barrier_open = False
        self._allow_set_config = True
        
        # Database of plates
        self._plates_database: Set[str] = set()
        
        # Current recognition data
        self._current_recognition: Optional[Dict[str, Any]] = None
        
        # Log of recent events (limited size)
        self._event_log: List[Dict[str, Any]] = []
        self._max_log_size = 100
        
        # WebSocket clients and their subscriptions
        self._ws_clients: Dict[Any, Dict[str, bool]] = {}
        
        # Simulated date (milliseconds since epoch)
        self._simulated_date = int(time.time() * 1000)
    
    def lock_device(self, password: Optional[str] = None) -> bool:
        """
        Lock the device with an optional password.
        
        Args:
            password: Optional password to lock the device
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._is_locked = True
            return True
    
    def unlock_device(self, password: Optional[str] = None) -> bool:
        """
        Unlock the device with an optional password.
        
        Args:
            password: Optional password to unlock the device
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._is_locked = False
            return True
    
    def is_device_locked(self) -> bool:
        """
        Check if the device is locked.
        
        Returns:
            True if locked, False otherwise
        """
        with self._lock:
            return self._is_locked
    
    def open_barrier(self) -> bool:
        """
        Open the barrier.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._barrier_open = True
            self._add_event_log({"type": "barrier", "action": "open"})
            return True
    
    def close_barrier(self) -> bool:
        """
        Close the barrier.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._barrier_open = False
            self._add_event_log({"type": "barrier", "action": "close"})
            return True
    
    def is_barrier_open(self) -> bool:
        """
        Check if the barrier is open.
        
        Returns:
            True if open, False otherwise
        """
        with self._lock:
            return self._barrier_open
    
    def set_allow_config(self, allow: bool) -> None:
        """
        Set whether configuration changes are allowed.
        
        Args:
            allow: True to allow, False to forbid
        """
        with self._lock:
            self._allow_set_config = allow
    
    def is_config_allowed(self) -> bool:
        """
        Check if configuration changes are allowed.
        
        Returns:
            True if allowed, False otherwise
        """
        with self._lock:
            return self._allow_set_config
    
    def add_plate_to_database(self, plate: str) -> bool:
        """
        Add a plate to the database.
        
        Args:
            plate: License plate to add
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._plates_database.add(plate)
            self._add_event_log({"type": "database", "action": "add", "plate": plate})
            return True
    
    def remove_plate_from_database(self, plate: str) -> bool:
        """
        Remove a plate from the database.
        
        Args:
            plate: License plate to remove
            
        Returns:
            True if successful, False if plate not in database
        """
        with self._lock:
            if plate in self._plates_database:
                self._plates_database.remove(plate)
                self._add_event_log({"type": "database", "action": "remove", "plate": plate})
                return True
            return False
    
    def get_database_plates(self) -> List[str]:
        """
        Get all plates in the database.
        
        Returns:
            List of plates
        """
        with self._lock:
            return list(self._plates_database)
    
    def set_current_recognition(self, recognition: Dict[str, Any]) -> None:
        """
        Set the current recognition data.
        
        Args:
            recognition: Recognition data
        """
        with self._lock:
            self._current_recognition = recognition
            self._add_event_log({"type": "recognition", "data": recognition})
    
    def get_current_recognition(self) -> Optional[Dict[str, Any]]:
        """
        Get the current recognition data.
        
        Returns:
            Current recognition data or None
        """
        with self._lock:
            return self._current_recognition
    
    def get_event_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent event logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of event logs
        """
        with self._lock:
            if limit is None:
                return self._event_log.copy()
            return self._event_log[-limit:].copy()
    
    def _add_event_log(self, event: Dict[str, Any]) -> None:
        """
        Add an event to the log, maintaining maximum size.
        
        Args:
            event: Event data to log
        """
        event["timestamp"] = self.get_simulated_date()
        self._event_log.append(event)
        
        # Trim log if it exceeds maximum size
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
    
    def register_ws_client(self, client: Any, subscriptions: Optional[Dict[str, bool]] = None) -> None:
        """
        Register a WebSocket client with optional subscriptions.
        
        Args:
            client: WebSocket client
            subscriptions: Dict of subscription flags
        """
        with self._lock:
            if subscriptions is None:
                subscriptions = {
                    "configChanges": False,
                    "infoChanges": False,
                    "traces": False
                }
            self._ws_clients[client] = subscriptions
    
    def unregister_ws_client(self, client: Any) -> None:
        """
        Unregister a WebSocket client.
        
        Args:
            client: WebSocket client
        """
        with self._lock:
            if client in self._ws_clients:
                del self._ws_clients[client]
    
    def update_ws_client_subscriptions(self, client: Any, subscriptions: Dict[str, bool]) -> None:
        """
        Update a WebSocket client's subscriptions.
        
        Args:
            client: WebSocket client
            subscriptions: Dict of subscription flags
        """
        with self._lock:
            if client in self._ws_clients:
                self._ws_clients[client].update(subscriptions)
    
    def get_ws_clients_for_event(self, event_type: str) -> List[Any]:
        """
        Get WebSocket clients subscribed to a specific event type.
        
        Args:
            event_type: Event type
            
        Returns:
            List of subscribed clients
        """
        with self._lock:
            return [client for client, subs in self._ws_clients.items() 
                    if subs.get(event_type, False)]
    
    def get_all_ws_clients(self) -> Dict[Any, Dict[str, bool]]:
        """
        Get all WebSocket clients and their subscriptions.
        
        Returns:
            Dict of clients and subscriptions
        """
        with self._lock:
            return self._ws_clients.copy()
    
    def set_simulated_date(self, date_ms: int) -> None:
        """
        Set the simulated date.
        
        Args:
            date_ms: Date in milliseconds since epoch
        """
        with self._lock:
            self._simulated_date = date_ms
    
    def get_simulated_date(self) -> int:
        """
        Get the simulated date.
        
        Returns:
            Date in milliseconds since epoch
        """
        with self._lock:
            return self._simulated_date
