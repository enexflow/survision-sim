import base64
import random
import time
from typing import Dict, Any, Optional, Tuple, Callable, TypeVar, cast

from pydantic import BaseModel, Field

from survision_simulator.config_manager import ConfigManager
from survision_simulator.data_store import DataStore
from survision_simulator.models import validate_model

# Type for message handler functions
T = TypeVar('T')
MessageHandler = Callable[[Any], Dict[str, Any]]


class PlateModel(BaseModel):
    value: str = Field(alias="@value")


class AddPlateModel(BaseModel):
    add_plate: PlateModel = Field(alias="addPlate")


class DelPlateModel(BaseModel):
    del_plate: PlateModel = Field(alias="delPlate")


class StreamConfigModel(BaseModel):
    config_changes: bool = Field(default=False, alias="@configChanges")
    info_changes: bool = Field(default=False, alias="@infoChanges")
    traces: bool = Field(default=False, alias="@traces")


class DeviceLogic:
    """
    Core business logic for the Survision device simulator.
    Handles device operations, plate recognition, and message processing.
    """
    
    def __init__(self, config_manager: ConfigManager, data_store: DataStore):
        """
        Initialize the device logic with configuration and data store.
        
        Args:
            config_manager: Configuration manager
            data_store: Data store
        """
        self.config_manager = config_manager
        self.data_store = data_store
        
        # Map of message types to handler functions
        self.message_handlers: Dict[str, MessageHandler] = {
            "getConfig": self._handle_get_config,
            "getCurrentLog": self._handle_get_current_log,
            "getDatabase": self._handle_get_database,
            "getDate": self._handle_get_date,
            "getImage": self._handle_get_image,
            "getInfos": self._handle_get_infos,
            "getLog": self._handle_get_log,
            "getTraces": self._handle_get_traces,
            "getXSD": self._handle_get_xsd,
            "openBarrier": self._handle_open_barrier,
            "triggerOn": self._handle_trigger_on,
            "triggerOff": self._handle_trigger_off,
            "lock": self._handle_lock,
            "unlock": self._handle_unlock,
            "resetConfig": self._handle_reset_config,
            "resetEngine": self._handle_reset_engine,
            "setConfig": self._handle_set_config,
            "editDatabase": self._handle_edit_database,
            "resetCounters": self._handle_reset_counters,
            "allowSetConfig": self._handle_allow_set_config,
            "forbidSetConfig": self._handle_forbid_set_config,
            "calibrateZoomFocus": self._handle_calibrate_zoom_focus
        }
        
        # Active trigger sessions
        self.active_triggers: Dict[str, Dict[str, Any]] = {}
        
        # Sample image data (base64 encoded)
        self.sample_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    def process_message(self, message: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Process an incoming CDK message.
        
        Args:
            message: CDK message
            
        Returns:
            Tuple of (response message, HTTP status code)
        """
        # Extract message type (first key in the message)
        if not message:
            return self._create_error_response("Invalid message format"), 400
        
        message_type = next(iter(message), None)
        if not message_type:
            return self._create_error_response("Empty message"), 400
        
        # Check if message type is supported
        if message_type not in self.message_handlers:
            return self._create_error_response(f"Unsupported message type: {message_type}"), 400
        
        # Check if device is locked for operations that require unlock
        locked_operations = {"resetConfig", "setConfig", "editDatabase", "allowSetConfig", "forbidSetConfig", "calibrateZoomFocus"}
        if message_type in locked_operations and self.data_store.is_device_locked():
            return self._create_error_response("Device is locked"), 403
        
        # Handle the message
        try:
            handler = self.message_handlers[message_type]
            return handler(message[message_type]), 200
        except Exception as e:
            return self._create_error_response(f"Error processing message: {str(e)}"), 500
    
    def process_websocket_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a WebSocket message.
        
        Args:
            message: WebSocket message
            
        Returns:
            Response message or None
        """
        # Currently only supports setEnableStreams
        if "setEnableStreams" in message:
            return self._handle_set_enable_streams(message["setEnableStreams"])
        return None
    
    def generate_recognition_event(self, plate: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a plate recognition event.
        
        Args:
            plate: License plate (random if None)
            
        Returns:
            Recognition event data
        """
        # Generate random plate if none provided
        if plate is None:
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            numbers = "0123456789"
            plate = "".join(random.choice(letters) for _ in range(2)) + \
                   "".join(random.choice(numbers) for _ in range(3)) + \
                   "".join(random.choice(letters) for _ in range(2))
        
        # Get configuration values
        reliability = int(self.config_manager.get_value("plateReliability", 80))
        context = self.config_manager.get_value("defaultContext", "F")
        
        # Create recognition data
        recognition = {
            "anpr": {
                "@date": str(self.data_store.get_simulated_date()),
                "decision": {
                    "@plate": plate,
                    "@reliability": str(reliability),
                    "@context": context,
                    "jpeg": self.sample_image
                }
            }
        }
        
        # Store current recognition
        self.data_store.set_current_recognition(recognition)
        
        return recognition
    
    def should_recognize_plate(self) -> bool:
        """
        Determine if a plate should be recognized based on success rate.
        
        Returns:
            True if plate should be recognized, False otherwise
        """
        success_rate = self.config_manager.get_value("recognitionSuccessRate", 75)
        return random.randint(1, 100) <= success_rate
    
    def _create_success_response(self) -> Dict[str, Any]:
        """
        Create a success response.
        
        Returns:
            Success response
        """
        return {"answer": {"@status": "ok"}}
    
    def _create_error_response(self, error_text: str) -> Dict[str, Any]:
        """
        Create an error response.
        
        Args:
            error_text: Error message
            
        Returns:
            Error response
        """
        return {"answer": {"@status": "failed", "@errorText": error_text}}
    
    def _handle_get_config(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getConfig message.
        
        Args:
            message_data: Message data
            
        Returns:
            Config response
        """
        # Create config response based on current configuration
        reliability = self.config_manager.get_value("plateReliability", 80)
        context = self.config_manager.get_value("defaultContext", "F")
        
        return {
            "config": {
                "device": {
                    "@name": "Simulator Device",
                    "@installationHeight_cm": "100"
                },
                "network": {
                    "interface": {
                        "@ipAddress": self.config_manager.get_value("ipAddress", "127.0.0.1"),
                        "@ipMask": "255.255.255.0"
                    },
                    "clp": {
                        "@port": str(self.config_manager.get_value("wsPort", 10001))
                    },
                    "ssws": {
                        "@httpPort": str(self.config_manager.get_value("httpPort", 8080))
                    }
                },
                "cameras": {
                    "camera": {
                        "anpr": {
                            "@context": f"{context}>OTHERS",
                            "@squarePlates": "0",
                            "@plateReliability": str(reliability)
                        }
                    }
                },
                "database": {
                    "@enabled": "0",
                    "@openForAll": "0"
                },
                "io": {
                    "defaultImpulse": {
                        "@pulseMode": "rising",
                        "@duration_ms": "500"
                    }
                }
            }
        }
    
    def _handle_get_current_log(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getCurrentLog message.
        
        Args:
            message_data: Message data
            
        Returns:
            Current log response
        """
        # Get current recognition or generate a new one
        recognition = self.data_store.get_current_recognition()
        if recognition is None:
            if self.should_recognize_plate():
                recognition = self.generate_recognition_event()
            else:
                return self._create_error_response("No current recognition")
        
        return recognition
    
    def _handle_get_database(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getDatabase message.
        
        Args:
            message_data: Message data
            
        Returns:
            Database response
        """
        plates = self.data_store.get_database_plates()
        
        # Format plates for response
        plate_list = [{"@value": plate} for plate in plates]
        
        return {
            "database": {
                "plate": plate_list
            }
        }
    
    def _handle_get_date(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getDate message.
        
        Args:
            message_data: Message data
            
        Returns:
            Date response
        """
        return {
            "date": {
                "@date": str(self.data_store.get_simulated_date())
            }
        }
    
    def _handle_get_image(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getImage message.
        
        Args:
            message_data: Message data
            
        Returns:
            Image response
        """
        return {
            "image": {
                "@date": str(self.data_store.get_simulated_date()),
                "jpeg": self.sample_image
            }
        }
    
    def _handle_get_infos(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getInfos message.
        
        Args:
            message_data: Message data
            
        Returns:
            Infos response
        """
        return {
            "infos": {
                "sensor": {
                    "@type": "Simulator",
                    "@firmwareVersion": "1.0",
                    "@serial": "SIM12345",
                    "@macAddress": "00:11:22:33:44:55",
                    "@status": "RUNNING",
                    "@locked": "1" if self.data_store.is_device_locked() else "0"
                },
                "cameras": {
                    "camera": {
                        "@id": "0",
                        "enabledAlgorithms": {
                            "anpr": None,
                            "trigger": None
                        }
                    }
                },
                "network": {
                    "interfaceWifi": {
                        "@macAddress": "00:22:55:00:aa:cc",
                        "@connected": "0"
                    }
                },
                "security": {
                    "@lockPasswordNeeded": "0",
                    "@rsaCrypted": "0"
                },
                "anpr": {
                    "@version": "1.0",
                    "@possibleContexts": "F>OTHERS"
                }
            }
        }
    
    def _handle_get_log(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getLog message.
        
        Args:
            message_data: Message data
            
        Returns:
            Log response
        """
        # For simplicity, just return the current recognition
        return self._handle_get_current_log(message_data)
    
    def _handle_get_traces(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getTraces message.
        
        Args:
            message_data: Message data
            
        Returns:
            Traces response
        """
        return {
            "traces": {
                "currentExecution_old": "BASE64_TRACES_OLD",
                "currentExecution_current": "BASE64_TRACES_NEW"
            }
        }
    
    def _handle_get_xsd(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle getXSD message.
        
        Args:
            message_data: Message data
            
        Returns:
            XSD response
        """
        # Return a base64 encoded XSD (simplified for this implementation)
        xsd_content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"></xs:schema>"
        xsd_base64 = base64.b64encode(xsd_content.encode()).decode()
        
        return {
            "xsd": xsd_base64
        }
    
    def _handle_open_barrier(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle openBarrier message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        self.data_store.open_barrier()
        return self._create_success_response()
    
    def _handle_trigger_on(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle triggerOn message.
        
        Args:
            message_data: Message data
            
        Returns:
            Trigger response
        """
        # Extract parameters
        camera_id = message_data.get("@cameraId", "0") if message_data else "0"
        timeout = int(message_data.get("@timeout", "1000")) if message_data else 1000
        
        # Generate trigger ID
        trigger_id = str(random.randint(1, 10000))
        
        # Store trigger session
        self.active_triggers[trigger_id] = {
            "cameraId": camera_id,
            "timeout": timeout,
            "startTime": time.time()
        }
        
        return {
            "triggerAnswer": {
                "@status": "ok",
                "@triggerId": trigger_id
            }
        }
    
    def _handle_trigger_off(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle triggerOff message.
        
        Args:
            message_data: Message data
            
        Returns:
            Trigger response
        """
        # Extract parameters
        camera_id = message_data.get("@cameraId", "0") if message_data else "0"
        
        # Find and remove trigger session
        for trigger_id, trigger in list(self.active_triggers.items()):
            if trigger["cameraId"] == camera_id:
                del self.active_triggers[trigger_id]
                return {
                    "triggerAnswer": {
                        "@status": "ok",
                        "@triggerId": trigger_id
                    }
                }
        
        return {
            "triggerAnswer": {
                "@status": "failed",
                "@errorText": "No active trigger session"
            }
        }
    
    def _handle_lock(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle lock message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        password = message_data.get("@password") if message_data else None
        if self.data_store.lock_device(password):
            return self._create_success_response()
        return self._create_error_response("Failed to lock device")
    
    def _handle_unlock(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle unlock message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        if self.data_store.unlock_device():
            return self._create_success_response()
        return self._create_error_response("Failed to unlock device")
    
    def _handle_reset_config(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle resetConfig message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        self.config_manager.update_config(ConfigManager.DEFAULT_CONFIG)
        return self._create_success_response()
    
    def _handle_reset_engine(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle resetEngine message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        # Clear current recognition
        empty_recognition: Dict[str, Any] = {
            "anpr": {
                "@date": str(self.data_store.get_simulated_date()),
                "decision": {}
            }
        }
        self.data_store.set_current_recognition(empty_recognition)
        return self._create_success_response()
    
    def _handle_set_config(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle setConfig message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        if not self.data_store.is_config_allowed():
            return self._create_error_response("Configuration changes are not allowed")
        
        if not message_data:
            return self._create_error_response("Invalid config data")
        
        # Extract plate reliability if present
        try:
            if isinstance(message_data, dict):
                # Use type ignore to suppress the type checker warnings
                config = message_data.get("config", {})  # type: ignore
                if isinstance(config, dict):
                    cameras = config.get("cameras", {})  # type: ignore
                    if isinstance(cameras, dict):
                        camera = cameras.get("camera", {})  # type: ignore
                        if isinstance(camera, dict):
                            anpr = camera.get("anpr", {})  # type: ignore
                            if isinstance(anpr, dict):
                                plate_reliability = anpr.get("@plateReliability")  # type: ignore
                                
                                if plate_reliability is not None:
                                    self.config_manager.set_value("plateReliability", int(cast(str, plate_reliability)))
        except (KeyError, ValueError, TypeError) as e:
            return self._create_error_response(f"Invalid config format: {str(e)}")
        
        return self._create_success_response()
    
    def _handle_edit_database(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle editDatabase message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        if not message_data or not isinstance(message_data, dict):
            return self._create_error_response("Invalid database edit data")
        
        # Handle add plate
        if "addPlate" in message_data:
            try:
                add_plate_model = validate_model(AddPlateModel, message_data)
                plate = add_plate_model.add_plate.value
                self.data_store.add_plate_to_database(plate)
                return self._create_success_response()
            except Exception as e:
                return self._create_error_response(f"Invalid add plate data: {str(e)}")
        
        # Handle delete plate
        if "delPlate" in message_data:
            try:
                del_plate_model = validate_model(DelPlateModel, message_data)
                plate = del_plate_model.del_plate.value
                if self.data_store.remove_plate_from_database(plate):
                    return self._create_success_response()
                return self._create_error_response(f"Plate not found: {plate}")
            except Exception as e:
                return self._create_error_response(f"Invalid delete plate data: {str(e)}")
        
        return self._create_error_response("Invalid database edit operation")
    
    def _handle_reset_counters(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle resetCounters message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        # No counters to reset in this implementation
        return self._create_success_response()
    
    def _handle_allow_set_config(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle allowSetConfig message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        self.data_store.set_allow_config(True)
        return self._create_success_response()
    
    def _handle_forbid_set_config(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle forbidSetConfig message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        self.data_store.set_allow_config(False)
        return self._create_success_response()
    
    def _handle_calibrate_zoom_focus(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle calibrateZoomFocus message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        # No actual calibration in this implementation
        return self._create_success_response()
    
    def _handle_set_enable_streams(self, message_data: Any) -> Dict[str, Any]:
        """
        Handle setEnableStreams message.
        
        Args:
            message_data: Message data
            
        Returns:
            Success response
        """
        if not message_data or not isinstance(message_data, dict):
            return self._create_error_response("Invalid stream configuration")
        
        try:
            stream_config = validate_model(StreamConfigModel, message_data)
            
            # Convert to dictionary for response
            subscriptions = {
                "configChanges": stream_config.config_changes,
                "infoChanges": stream_config.info_changes,
                "traces": stream_config.traces
            }
            
            return {"subscriptions": subscriptions}
        except Exception as e:
            return self._create_error_response(f"Invalid stream configuration: {str(e)}")
