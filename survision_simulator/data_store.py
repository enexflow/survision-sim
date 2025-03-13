import threading
import time
from typing import Dict, List, Literal, Optional, Set, Protocol, Union
from dataclasses import dataclass
from enum import Enum, auto

from survision_simulator.models import (
    AnprEvent, RecognitionEvent,
    StreamConfig
)


class EventType(Enum):
    BARRIER = auto()
    DATABASE = auto()
    RECOGNITION = auto()
    SECURITY = auto()
    REBOOT = auto()


class WebSocketClient(Protocol):
    """Protocol for WebSocket clients to ensure type safety."""
    def send(self, data: str) -> None: ...


@dataclass
class BarrierEvent:
    action: Literal["open", "close"]
    timestamp: int


@dataclass
class DatabaseEvent:
    action: Literal["add", "remove", "clear"]
    plate: Optional[str]
    timestamp: int


@dataclass
class SecurityEvent:
    action: Literal["password_change", "rsa_change"]
    timestamp: int


@dataclass
class RebootEvent:
    timestamp: int


Event = Union[BarrierEvent, DatabaseEvent, RecognitionEvent, SecurityEvent, RebootEvent]


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
        
        # Security settings
        self._lock_password = None
        self._lock_password_hint = None
        self._rsa_hint = None
        
        # Database of plates
        self._plates_database: Set[str] = set()
        
        # Current recognition data
        self._current_recognition: Optional[AnprEvent] = None
        
        # Log of recent events (limited size)
        self._event_log: List[Event] = []
        self._max_log_size = 100
        
        # WebSocket clients and their subscriptions
        self._ws_clients: Dict[str, StreamConfig] = {}
        
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
            # If a lock password is set, verify it
            if self._lock_password is not None and password != self._lock_password:
                return False
                
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
    
    def has_lock_password(self) -> bool:
        """
        Check if a lock password is set.
        
        Returns:
            True if a password is set, False otherwise
        """
        with self._lock:
            return self._lock_password is not None
    
    def set_lock_password(self, password: str) -> None:
        """
        Set the lock password.
        
        Args:
            password: Password to set
        """
        with self._lock:
            self._lock_password = password
            self._add_event_log(SecurityEvent(
                action="password_change",
                timestamp=self.get_simulated_date()
            ))
    
    def set_lock_password_hint(self, hint: str) -> None:
        """
        Set the lock password hint.
        
        Args:
            hint: Password hint to set
        """
        with self._lock:
            self._lock_password_hint = hint
    
    def get_lock_password_hint(self) -> Optional[str]:
        """
        Get the lock password hint.
        
        Returns:
            Password hint or None
        """
        with self._lock:
            return self._lock_password_hint
    
    def set_rsa_hint(self, hint: str) -> None:
        """
        Set the RSA hint.
        
        Args:
            hint: RSA hint to set
        """
        with self._lock:
            self._rsa_hint = hint
            self._add_event_log(SecurityEvent(
                action="rsa_change",
                timestamp=self.get_simulated_date()
            ))
    
    def get_rsa_hint(self) -> Optional[str]:
        """
        Get the RSA hint.
        
        Returns:
            RSA hint or None
        """
        with self._lock:
            return self._rsa_hint
    
    def open_barrier(self) -> bool:
        """
        Open the barrier.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._barrier_open = True
            self._add_event_log(BarrierEvent(
                action="open",
                timestamp=self.get_simulated_date()
            ))
            return True
    
    def close_barrier(self) -> bool:
        """
        Close the barrier.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._barrier_open = False
            self._add_event_log(BarrierEvent(
                action="close",
                timestamp=self.get_simulated_date()
            ))
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
            self._add_event_log(DatabaseEvent(
                action="add",
                plate=plate,
                timestamp=self.get_simulated_date()
            ))
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
                self._add_event_log(DatabaseEvent(
                    action="remove",
                    plate=plate,
                    timestamp=self.get_simulated_date()
                ))
                return True
            return False
    
    def clear_database(self) -> bool:
        """
        Clear all plates from the database.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._plates_database.clear()
            self._add_event_log(DatabaseEvent(
                action="clear",
                plate=None,
                timestamp=self.get_simulated_date()
            ))
            return True
    
    def get_database_plates(self) -> List[str]:
        """
        Get all plates in the database.
        
        Returns:
            List of plates
        """
        with self._lock:
            return list(self._plates_database)
    
    def set_current_recognition(self, recognition: AnprEvent) -> None:
        """
        Set the current recognition data.
        
        Args:
            recognition: Recognition data
        """
        with self._lock:
            self._current_recognition = recognition
            self._add_event_log(recognition.anpr)
    
    def get_current_recognition(self) -> Optional[AnprEvent]:
        """
        Get the current recognition data.
        
        Returns:
            Current recognition data or None
        """
        with self._lock:
            return self._current_recognition
    
    def simulate_reboot(self) -> None:
        """
        Simulate a device reboot.
        
        This resets certain device state but preserves configuration.
        """
        with self._lock:
            # Reset device state
            self._is_locked = False
            self._barrier_open = False
            
            # Reset current recognition
            self._current_recognition = None
            
            # Log the reboot event
            self._add_event_log(RebootEvent(
                timestamp=self.get_simulated_date()
            ))
    
    def get_event_logs(self, limit: Optional[int] = None) -> List[Event]:
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
    
    def _add_event_log(self, event: Event) -> None:
        """
        Add an event to the log, maintaining maximum size.
        
        Args:
            event: Event data to log
        """
        self._event_log.append(event)
        
        # Trim log if it exceeds maximum size
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
    
    def register_ws_client(self, client: str, subscriptions: Optional[StreamConfig] = None) -> None:
        """
        Register a WebSocket client with optional subscriptions.
        
        Args:
            client: WebSocket client ID
            subscriptions: Dict of subscription flags
        """
        with self._lock:
            if subscriptions is None:
                subscriptions = StreamConfig(
                    config_changes=False,
                    info_changes=False,
                    traces=False,
                    cameras={}
                )
            self._ws_clients[client] = subscriptions
    
    def unregister_ws_client(self, client: str) -> None:
        """
        Unregister a WebSocket client.
        
        Args:
            client: WebSocket client ID
        """
        with self._lock:
            if client in self._ws_clients:
                del self._ws_clients[client]
    
    def update_ws_client_subscriptions(self, client: str, subscriptions: StreamConfig) -> None:
        """
        Update a WebSocket client's subscriptions.
        
        Args:
            client: WebSocket client ID
            subscriptions: Dict of subscription flags
        """
        with self._lock:
            if client in self._ws_clients:
                self._ws_clients[client] = subscriptions
    
    def set_stream_config(self, stream_config: StreamConfig) -> None:
        """
        Set the stream configuration.
        """
        with self._lock:
            self._stream_config = stream_config

    def get_ws_clients_for_event(self, event_type: EventType) -> List[str]:
        """
        Get WebSocket clients subscribed to a specific event type.
        
        Args:
            event_type: Event type
            
        Returns:
            List of subscribed client IDs
        """
        with self._lock:
            return [client for client, subs in self._ws_clients.items() 
                    if getattr(subs, event_type.name.lower(), False)]
    
    def get_all_ws_clients(self) -> Dict[str, StreamConfig]:
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
