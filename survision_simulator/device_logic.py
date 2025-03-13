import base64
import random
import time
from typing import Dict, Any, Optional, Tuple, Callable
import logging


from survision_simulator.config_manager import ConfigManager
from survision_simulator.data_store import DataStore
from survision_simulator.models import (
    GetDataBaseModel, GetDateMessage, KeepAliveMessage, SetupMessage, StreamConfig, GetCurrentLogMessage, TriggerOnMessage,
    TriggerOffMessage, LockMessage, SetConfigMessage, EditDatabaseMessage,
    MessageType, UpdateMessage, parse_message, GetConfigMessage, GetImageMessage, GetInfosMessage,
    GetLogMessage, GetTracesMessage, GetXSDMessage, OpenBarrierMessage, UnlockMessage,
    ResetConfigMessage, ResetEngineMessage, ResetCountersMessage, AllowSetConfigMessage,
    ForbidSetConfigMessage, CalibrateZoomFocusMessage, SetEnableStreamsRequest
)

# Type for message handler functions
HandlerResult = Dict[str, Any]
MessageHandler = Callable[[MessageType], HandlerResult]

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
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("DeviceLogic initialized with ConfigManager and DataStore")
        
        self.config_manager = config_manager
        self.data_store = data_store
        
        # Active trigger sessions
        self.active_triggers: Dict[str, Dict[str, Any]] = {}
        
        # Sample image data (base64 encoded)
        self.sample_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    def process_message(self, message: MessageType) -> Tuple[Dict[str, Any], int]:
        """
        Process an incoming CDK message.
        
        Args:
            message: CDK message as a Pydantic model
            
        Returns:
            Tuple of (response message, HTTP status code)
        """
        self.logger.info(f"Received message of type: {type(message).__name__}")
        match message:
            case GetConfigMessage():
                return self._handle_get_config(message), 200
            case GetCurrentLogMessage():
                return self._handle_get_current_log(message), 200
            case GetDataBaseModel():
                return self._handle_get_database(message), 200
            case GetDateMessage():
                return self._handle_get_date(message), 200
            case GetImageMessage():
                return self._handle_get_image(message), 200
            case GetInfosMessage():
                return self._handle_get_infos(message), 200
            case GetLogMessage():
                return self._handle_get_log(message), 200
            case GetTracesMessage():
                return self._handle_get_traces(message), 200
            case GetXSDMessage():
                return self._handle_get_xsd(message), 200
            case OpenBarrierMessage():
                return self._handle_open_barrier(message), 200
            case TriggerOnMessage():
                return self._handle_trigger_on(message), 200
            case TriggerOffMessage():
                return self._handle_trigger_off(message), 200
            case LockMessage():
                return self._handle_lock(message), 200
            case UnlockMessage():
                return self._handle_unlock(message), 200
            case ResetConfigMessage():
                return self._handle_reset_config(message), 200
            case ResetEngineMessage():
                return self._handle_reset_engine(message), 200
            case SetConfigMessage():
                return self._handle_set_config(message), 200
            case EditDatabaseMessage():
                return self._handle_edit_database(message), 200
            case ResetCountersMessage():
                return self._handle_reset_counters(message), 200
            case AllowSetConfigMessage():
                return self._handle_allow_set_config(message), 200
            case ForbidSetConfigMessage():
                return self._handle_forbid_set_config(message), 200
            case CalibrateZoomFocusMessage():
                return self._handle_calibrate_zoom_focus(message), 200
            case SetEnableStreamsRequest():
                return self._handle_set_enable_streams(message.set_enable_streams), 200
            case UpdateMessage():
                return self._handle_update(message), 200
            case SetupMessage():
                return self._handle_setup(message), 200
            case KeepAliveMessage():
                return self._handle_keep_alive(message), 200
        raise NotImplementedError(f"Unknown message type: {type(message).__name__}")
    
    def process_websocket_message(self, message: bytes) -> Optional[Dict[str, Any]]:
        """
        Process a WebSocket message.
        
        Args:
            message: WebSocket message
            
        Returns:
            Response message or None
        """
        self.logger.info("Received WebSocket message")
        # Parse the message
        parsed = parse_message(message)
        
        # Handle the message based on type
        if isinstance(parsed, SetEnableStreamsRequest):
            return self._handle_set_enable_streams(parsed.set_enable_streams)
        else:
            resp, code = self.process_message(parsed)
            if code != 200:
                raise Exception(f"Error processing message: {resp}")
            return resp
    
    def generate_recognition_event(self, plate: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a plate recognition event.
        
        Args:
            plate: License plate (random if None)
            
        Returns:
            Recognition event data
        """
        self.logger.info(f"Generating recognition event. Provided plate: {plate}")
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
        self.logger.info("Evaluating if a plate should be recognized based on configured success rate")
        success_rate = self.config_manager.get_value("recognitionSuccessRate", 75)
        return random.randint(1, 100) <= success_rate
    
    def _create_success_response(self) -> Dict[str, Any]:
        """
        Create a success response.
        
        Returns:
            Success response
        """
        self.logger.info("Creating a success response")
        return {"answer": {"@status": "ok"}}
    
    def _create_error_response(self, error_text: str) -> Dict[str, Any]:
        """
        Create an error response.
        
        Args:
            error_text: Error message
            
        Returns:
            Error response
        """
        self.logger.warning(f"Creating an error response with message: {error_text}")
        return {"answer": {"@status": "failed", "@errorText": error_text}}
    
    def _handle_get_config(self, message: GetConfigMessage) -> Dict[str, Any]:
        """
        Handle getConfig message.
        
        Args:
            message: GetConfigMessage model
            
        Returns:
            Config response
        """
        self.logger.info("Handling GetConfigMessage to retrieve current device configuration")
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
    
    def _handle_get_current_log(self, message: GetCurrentLogMessage) -> Dict[str, Any]:
        """
        Handle getCurrentLog message.
        
        Args:
            message: GetCurrentLogMessage model
            
        Returns:
            Current log response
        """
        self.logger.info("Handling GetCurrentLogMessage to retrieve the current log")
        # Get current recognition or generate a new one
        recognition = self.data_store.get_current_recognition()
        if recognition is None:
            if self.should_recognize_plate():
                recognition = self.generate_recognition_event()
            else:
                return self._create_error_response("No current recognition")
        
        return recognition
    
    def _handle_get_database(self, message: GetDataBaseModel) -> Dict[str, Any]:
        """
        Handle getDatabase message.
        
        Args:
            message: GetDatabaseMessage model
            
        Returns:
            Database response
        """
        self.logger.info("Handling GetDataBaseModel to retrieve database information")
        plates = self.data_store.get_database_plates()
        
        # Format plates for response
        plate_list = [{"@value": plate} for plate in plates]
        
        return {
            "database": {
                "plate": plate_list
            }
        }
    
    def _handle_get_date(self, message: GetDateMessage) -> Dict[str, Any]:
        """
        Handle getDate message.
        
        Args:
            message: GetDateMessage model
            
        Returns:
            Date response
        """
        self.logger.info("Handling GetDateMessage to retrieve the current simulated date")
        return {
            "date": {
                "@date": str(self.data_store.get_simulated_date())
            }
        }
    
    def _handle_get_image(self, message: GetImageMessage) -> Dict[str, Any]:
        """
        Handle getImage message.
        
        Args:
            message: GetImageMessage model
            
        Returns:
            Image response
        """
        self.logger.info("Handling GetImageMessage to retrieve the current image data")
        return {
            "image": {
                "@date": str(self.data_store.get_simulated_date()),
                "jpeg": self.sample_image
            }
        }
    
    def _handle_get_infos(self, message: GetInfosMessage) -> Dict[str, Any]:
        """
        Handle getInfos message.
        
        Args:
            message: GetInfosMessage model
            
        Returns:
            Infos response
        """
        self.logger.info("Handling GetInfosMessage to retrieve device information")
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
    
    def _handle_get_log(self, message: GetLogMessage) -> Dict[str, Any]:
        """
        Handle getLog message.
        
        Args:
            message: GetLogMessage model
            
        Returns:
            Log response
        """
        self.logger.info("Handling GetLogMessage to retrieve log data")
        # For simplicity, just return the current recognition
        recognition = self.data_store.get_current_recognition()
        if recognition is None:
            if self.should_recognize_plate():
                recognition = self.generate_recognition_event()
            else:
                return self._create_error_response("No current recognition")
        
        return recognition
    
    def _handle_get_traces(self, message: GetTracesMessage) -> Dict[str, Any]:
        """
        Handle getTraces message.
        
        Args:
            message: GetTracesMessage model
            
        Returns:
            Traces response
        """
        self.logger.info("Handling GetTracesMessage to retrieve trace data")
        return {
            "traces": {
                "currentExecution_old": "BASE64_TRACES_OLD",
                "currentExecution_current": "BASE64_TRACES_NEW"
            }
        }
    
    def _handle_get_xsd(self, message: GetXSDMessage) -> Dict[str, Any]:
        """
        Handle getXSD message.
        
        Args:
            message: GetXSDMessage model
            
        Returns:
            XSD response
        """
        self.logger.info("Handling GetXSDMessage to retrieve XSD schema")
        # Return a base64 encoded XSD (simplified for this implementation)
        xsd_content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"></xs:schema>"
        xsd_base64 = base64.b64encode(xsd_content.encode()).decode()
        
        return {
            "xsd": xsd_base64
        }
    
    def _handle_open_barrier(self, message: OpenBarrierMessage) -> Dict[str, Any]:
        """
        Handle openBarrier message.
        
        Args:
            message: OpenBarrierMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling OpenBarrierMessage to open the barrier")
        self.data_store.open_barrier()
        return self._create_success_response()
    
    def _handle_trigger_on(self, message: TriggerOnMessage) -> Dict[str, Any]:
        """
        Handle triggerOn message.
        
        Args:
            message: TriggerOnMessage model
            
        Returns:
            Trigger response
        """
        self.logger.info("Handling TriggerOnMessage to activate a trigger")
        # Extract parameters
        message_data = message.trigger_on
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
    
    def _handle_trigger_off(self, message: TriggerOffMessage) -> Dict[str, Any]:
        """
        Handle triggerOff message.
        
        Args:
            message: TriggerOffMessage model
            
        Returns:
            Trigger response
        """
        self.logger.info("Handling TriggerOffMessage to deactivate a trigger")
        # Extract parameters
        message_data = message.trigger_off
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
    
    def _handle_lock(self, message: LockMessage) -> Dict[str, Any]:
        """
        Handle lock message.
        
        Args:
            message: LockMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling LockMessage to lock the device")
        message_data = message.lock
        password = message_data.get("@password") if message_data else None
        if self.data_store.lock_device(password):
            return self._create_success_response()
        return self._create_error_response("Failed to lock device")
    
    def _handle_unlock(self, message: UnlockMessage) -> Dict[str, Any]:
        """
        Handle unlock message.
        
        Args:
            message: UnlockMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling UnlockMessage to unlock the device")
        if self.data_store.unlock_device():
            return self._create_success_response()
        return self._create_error_response("Failed to unlock device")
    
    def _handle_reset_config(self, message: ResetConfigMessage) -> Dict[str, Any]:
        """
        Handle resetConfig message.
        
        Args:
            message: ResetConfigMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling ResetConfigMessage to reset device configuration to default")
        self.config_manager.update_config(ConfigManager.DEFAULT_CONFIG)
        return self._create_success_response()
    
    def _handle_reset_engine(self, message: ResetEngineMessage) -> Dict[str, Any]:
        """
        Handle resetEngine message.
        
        Args:
            message: ResetEngineMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling ResetEngineMessage to reset the engine state")
        # Clear current recognition
        empty_recognition: Dict[str, Any] = {
            "anpr": {
                "@date": str(self.data_store.get_simulated_date()),
                "decision": {}
            }
        }
        self.data_store.set_current_recognition(empty_recognition)
        return self._create_success_response()
    
    def _handle_set_config(self, message: SetConfigMessage) -> Dict[str, Any]:
        """
        Handle setConfig message.
        
        Args:
            message: SetConfigMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling SetConfigMessage to update device configuration")
        if not self.data_store.is_config_allowed():
            return self._create_error_response("Configuration changes are not allowed")
        
        message_data = message.set_config
        if not message_data:
            return self._create_error_response("Invalid config data")
        
        # Extract plate reliability if present
        try:
            config = message_data.get("config", {})
            cameras = config.get("cameras", {})
            camera = cameras.get("camera", {})
            anpr = camera.get("anpr", {})
            plate_reliability = anpr.get("@plateReliability")
            
            if plate_reliability is not None:
                self.config_manager.set_value("plateReliability", int(plate_reliability))
        except (KeyError, ValueError, TypeError) as e:
            return self._create_error_response(f"Invalid config format: {str(e)}")
        
        return self._create_success_response()
    
    def _handle_edit_database(self, message: EditDatabaseMessage) -> Dict[str, Any]:
        """
        Handle editDatabase message.
        
        Args:
            message: EditDatabaseMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling EditDatabaseMessage to modify the database")
        message_data = message.edit_database
        
        # Handle add plate
        add_plate = getattr(message_data, 'add_plate', None)
        if add_plate is not None:
            try:
                plate = add_plate.value
                self.data_store.add_plate_to_database(plate)
                return self._create_success_response()
            except Exception as e:
                return self._create_error_response(f"Invalid add plate data: {str(e)}")
        
        # Handle delete plate
        del_plate = getattr(message_data, 'del_plate', None)
        if del_plate is not None:
            try:
                plate = del_plate.value
                if self.data_store.remove_plate_from_database(plate):
                    return self._create_success_response()
                return self._create_error_response(f"Plate not found: {plate}")
            except Exception as e:
                return self._create_error_response(f"Invalid delete plate data: {str(e)}")
        
        return self._create_error_response("Invalid database edit operation")
    
    def _handle_reset_counters(self, message: ResetCountersMessage) -> Dict[str, Any]:
        """
        Handle resetCounters message.
        
        Args:
            message: ResetCountersMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling ResetCountersMessage to reset counters")
        # No counters to reset in this implementation
        return self._create_success_response()
    
    def _handle_allow_set_config(self, message: AllowSetConfigMessage) -> Dict[str, Any]:
        """
        Handle allowSetConfig message.
        
        Args:
            message: AllowSetConfigMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling AllowSetConfigMessage to allow configuration changes")
        self.data_store.set_allow_config(True)
        return self._create_success_response()
    
    def _handle_forbid_set_config(self, message: ForbidSetConfigMessage) -> Dict[str, Any]:
        """
        Handle forbidSetConfig message.
        
        Args:
            message: ForbidSetConfigMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling ForbidSetConfigMessage to forbid configuration changes")
        self.data_store.set_allow_config(False)
        return self._create_success_response()
    
    def _handle_calibrate_zoom_focus(self, message: CalibrateZoomFocusMessage) -> Dict[str, Any]:
        """
        Handle calibrateZoomFocus message.
        
        Args:
            message: CalibrateZoomFocusMessage model
            
        Returns:
            Success response
        """
        self.logger.info("Handling CalibrateZoomFocusMessage to calibrate zoom and focus")
        # No actual calibration in this implementation
        return self._create_success_response()
    
    def _handle_set_enable_streams(self, stream_config: StreamConfig) -> Dict[str, Any]:
        """
        Handle setEnableStreams message.
        
        Args:
            stream_config: StreamConfig model
            
        Returns:
            Success response
        """
        self.logger.info("Handling SetEnableStreamsRequest to configure stream settings")
        # Convert to dictionary for response
        subscriptions = {
            "configChanges": stream_config.config_changes,
            "infoChanges": stream_config.info_changes,
            "traces": stream_config.traces
        }
        
        return {"subscriptions": subscriptions}

    def _handle_update(self, message: UpdateMessage) -> Dict[str, Any]:
        self.logger.info("Handling UpdateMessage to update device state")
        return self._create_success_response()

    def _handle_setup(self, message: SetupMessage) -> Dict[str, Any]:
        self.logger.info("Handling SetupMessage to perform setup operations")
        return self._create_success_response()

    def _handle_keep_alive(self, message: KeepAliveMessage) -> Dict[str, Any]:
        self.logger.info("Handling KeepAliveMessage to maintain connection")
        return self._create_success_response()
