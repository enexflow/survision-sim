import base64
import random
import time
from typing import Dict, Any, Optional, Tuple, Callable, Union
import logging
from datetime import datetime


from survision_simulator.config_manager import ConfigManager
from survision_simulator.data_store import DataStore
from survision_simulator.models import (
    AnprInfo,
    AnswerType,
    CameraInfo,
    CharacterReliability,
    DatabaseMatch,
    DeviceInfo,
    DeviceInfoResponse,
    ErrorResponse,
    NetworkInfo,
    PlateReading,
    ReliabilityPerCharacter,
    SecurityInfo,
    StatusAnswer,
    GetDataBaseModel,
    GetDateMessage,
    KeepAliveMessage,
    SetupMessage,
    StreamConfig,
    GetCurrentLogMessage,
    SuccessResponse,
    TriggerAnswer,
    TriggerAnswerData,
    TriggerOnMessage,
    TriggerOffMessage,
    LockMessage,
    SetConfigMessage,
    EditDatabaseMessage,
    MessageType,
    UpdateMessage,
    XSDAnswer,
    parse_message,
    GetConfigMessage,
    GetImageMessage,
    GetInfosMessage,
    GetLogMessage,
    GetTracesMessage,
    GetXSDMessage,
    OpenBarrierMessage,
    UnlockMessage,
    ResetConfigMessage,
    ResetEngineMessage,
    ResetCountersMessage,
    AllowSetConfigMessage,
    ForbidSetConfigMessage,
    CalibrateZoomFocusMessage,
    SetEnableStreamsRequest,
    ConfigAnswer,
    DateAnswer,
    ImageAnswer,
    InfosAnswer,
    LogAnswer,
    TracesAnswer,
    DatabaseAnswer,
    AnprEvent,
    RecognitionEvent,
    RecognitionDecision,
    SetSecurityMessage,
    TestFTPMessage,
    TestNTPMessage,
    UpdateWebFirmwareMessage,
    EraseDatabaseMessage,
    RebootMessage,
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
        self.active_triggers: Dict[int, Dict[str, Any]] = {}

        # Sample image data (base64 encoded)
        self.sample_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

    def process_message(self, message: MessageType) -> Tuple[Union[AnswerType, None], int]:
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
            case SetSecurityMessage():
                return self._handle_set_security(message), 200
            case TestFTPMessage():
                return self._handle_test_ftp(message), 200
            case TestNTPMessage():
                return self._handle_test_ntp(message), 200
            case UpdateWebFirmwareMessage():
                return self._handle_update_web_firmware(message), 200
            case EraseDatabaseMessage():
                return self._handle_erase_database(message), 200
            case RebootMessage():
                return self._handle_reboot(message), 200
        raise NotImplementedError(f"Unknown message type: {type(message).__name__}")

    def process_websocket_message(self, message: bytes) -> Optional[AnswerType]:
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

    def generate_recognition_event(self, plate: Optional[str] = None) -> AnprEvent:
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
            all_plates = ["XX 000 XX", "XX 000 XY"]
            plate = random.choice(all_plates)

        # Get configuration values
        reliability = int(self.config_manager.get_value("plateReliability", 80))
        context = self.config_manager.get_value("defaultContext", "F")

        # Create recognition data
        recognition = AnprEvent(
            anpr=RecognitionEvent(
                date=datetime.now(),
                decision=RecognitionDecision(
                    plate=plate,
                    reliability=reliability,
                    context=context,
                    jpeg=self.sample_image,
                    reliability_per_character=ReliabilityPerCharacter(
                        char=[CharacterReliability(index=i, reliability=reliability) for i, _l in enumerate(plate)]
                    ),
                    database=DatabaseMatch(
                        plate=plate,
                        distance=0,
                    ) if plate in self.data_store.get_database_plates() else None
                ),
            )
        )
        # Store current recognition
        self.data_store.set_current_recognition(recognition)

        return recognition

    def should_recognize_plate(self) -> bool:
        """
        Determine if a plate should be recognized based on success rate.

        Returns:
            True if plate should be recognized, False otherwise
        """
        self.logger.info(
            "Evaluating if a plate should be recognized based on configured success rate"
        )
        success_rate = self.config_manager.get_value("recognitionSuccessRate", 75)
        return random.randint(1, 100) <= success_rate

    def _create_success_response(self) -> StatusAnswer:
        """
        Create a success response.

        Returns:
            Success response
        """
        self.logger.info("Creating a success response")
        return SuccessResponse().as_answer()

    def _create_error_response(self, error_text: str) -> StatusAnswer:
        """
        Create an error response.

        Args:
            error_text: Error message

        Returns:
            Error response
        """
        self.logger.warning(f"Creating an error response with message: {error_text}")
        return ErrorResponse.for_error_text(error_text).as_answer()

    def _handle_get_config(self, message: GetConfigMessage) -> AnswerType:
        """
        Handle getConfig message.

        Args:
            message: GetConfigMessage model

        Returns:
            Config response
        """
        self.logger.info(
            "Handling GetConfigMessage to retrieve current device configuration"
        )
        reliability = self.config_manager.get_value("plateReliability", 80)
        context = self.config_manager.get_value("defaultContext", "F")

        config = {
            "device": {"@name": "Simulator Device", "@installationHeight_cm": "100"},
            "network": {
                "interface": {
                    "@ipAddress": self.config_manager.get_value(
                        "ipAddress", "127.0.0.1"
                    ),
                    "@ipMask": "255.255.255.0",
                },
                "clp": {"@port": str(self.config_manager.get_value("wsPort", 10001))},
                "ssws": {
                    "@httpPort": str(self.config_manager.get_value("httpPort", 8080))
                },
            },
            "cameras": {
                "camera": {
                    "anpr": {
                        "@context": f"{context}>OTHERS",
                        "@squarePlates": "0",
                        "@plateReliability": str(reliability),
                    }
                }
            },
            "database": {"@enabled": "0", "@openForAll": "0"},
            "io": {"defaultImpulse": {"@pulseMode": "rising", "@duration_ms": "500"}},
        }
        return ConfigAnswer(config=config)

    def _handle_get_current_log(self, message: GetCurrentLogMessage) -> AnswerType:
        """
        Handle getCurrentLog message.

        Args:
            message: GetCurrentLogMessage model

        Returns:
            Current log response
        """
        self.logger.info("Handling GetCurrentLogMessage to retrieve the current log")
        recognition = self.data_store.get_current_recognition()
        if recognition is None:
            if self.should_recognize_plate():
                recognition = self.generate_recognition_event()
            else:
                return self._create_error_response("No current recognition")

        return LogAnswer(anpr=recognition.anpr)

    def _handle_get_database(self, message: GetDataBaseModel) -> AnswerType:
        """
        Handle getDatabase message.

        Args:
            message: GetDatabaseMessage model

        Returns:
            Database response
        """
        self.logger.info("Handling GetDataBaseModel to retrieve database information")
        plates = self.data_store.get_database_plates()

        return DatabaseAnswer(database=[
            PlateReading(value=plate)
            for plate in plates
        ])

    def _handle_get_date(self, message: GetDateMessage) -> AnswerType:
        """
        Handle getDate message.

        Args:
            message: GetDateMessage model

        Returns:
            Date response
        """
        self.logger.info(
            "Handling GetDateMessage to retrieve the current simulated date"
        )
        date = {"@date": str(self.data_store.get_simulated_date())}
        return DateAnswer(date=date)

    def _handle_get_image(self, message: GetImageMessage) -> AnswerType:
        """
        Handle getImage message.

        Args:
            message: GetImageMessage model

        Returns:
            Image response
        """
        self.logger.info("Handling GetImageMessage to retrieve the current image data")
        image = {
            "@date": str(self.data_store.get_simulated_date()),
            "jpeg": self.sample_image,
        }
        return ImageAnswer(image=image)

    def _handle_get_infos(self, message: GetInfosMessage) -> AnswerType:
        """
        Handle getInfos message.

        Args:
            message: GetInfosMessage model

        Returns:
            Infos response
        """
        self.logger.info("Handling GetInfosMessage to retrieve device information")
        infos = DeviceInfoResponse(
            sensor=DeviceInfo(
                type="Simulator",
                firmware_version="1.0",
                serial="SIM12345",
                mac_address="00:11:22:33:44:55",
                status="RUNNING",
                locked=self.data_store.is_device_locked(),
            ),
            cameras={
                "camera": CameraInfo(
                    id="0", enabled_algorithms={"anpr": None, "trigger": None}
                )
            },
            network={
                "interfaceWifi": NetworkInfo(
                    mac_address="00:22:55:00:aa:cc", connected=True
                )
            },
            security=SecurityInfo(lock_password_needed=False, rsa_crypted=False),
            anpr=AnprInfo(version="1.0", possible_contexts="F>OTHERS"),
        )
        return InfosAnswer(infos=infos)

    def _handle_get_log(self, message: GetLogMessage) -> AnswerType:
        """
        Handle getLog message.

        Args:
            message: GetLogMessage model

        Returns:
            Log response
        """
        self.logger.info("Handling GetLogMessage to retrieve log data")
        recognition = self.data_store.get_current_recognition()
        if recognition is None:
            if self.should_recognize_plate():
                recognition = self.generate_recognition_event()
            else:
                return self._create_error_response("No current recognition")

        return LogAnswer(anpr=recognition.anpr)

    def _handle_get_traces(self, message: GetTracesMessage) -> AnswerType:
        """
        Handle getTraces message.

        Args:
            message: GetTracesMessage model

        Returns:
            Traces response
        """
        self.logger.info("Handling GetTracesMessage to retrieve trace data")
        traces = {
            "currentExecution_old": "BASE64_TRACES_OLD",
            "currentExecution_current": "BASE64_TRACES_NEW",
        }
        return TracesAnswer(traces=traces)

    def _handle_get_xsd(self, message: GetXSDMessage) -> AnswerType:
        """
        Handle getXSD message.

        Args:
            message: GetXSDMessage model

        Returns:
            XSD response
        """
        self.logger.info("Handling GetXSDMessage to retrieve XSD schema")
        xsd_content = '<?xml version="1.0" encoding="UTF-8"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"></xs:schema>'
        xsd_base64 = base64.b64encode(xsd_content.encode()).decode()

        return XSDAnswer(xsd=xsd_base64)

    def _handle_open_barrier(self, message: OpenBarrierMessage) -> StatusAnswer:
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

    def _handle_trigger_on(self, message: TriggerOnMessage) -> TriggerAnswer:
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
        trigger_id = random.randint(1, 10000)

        # Store trigger session
        self.active_triggers[trigger_id] = {
            "cameraId": camera_id,
            "timeout": timeout,
            "startTime": time.time(),
        }

        return TriggerAnswerData.ok_for_id(trigger_id).as_answer()

    def _handle_trigger_off(self, message: TriggerOffMessage) -> TriggerAnswer:
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
                return TriggerAnswerData.ok_for_id(trigger_id).as_answer()

        return TriggerAnswerData.failed_for_id(0).as_answer()

    def _handle_lock(self, message: LockMessage) -> StatusAnswer:
        """
        Handle lock message.

        Args:
            message: LockMessage model

        Returns:
            Success response
        """
        self.logger.info("Handling LockMessage to lock the device")
        password = message.lock.password
        if self.data_store.lock_device(password):
            return self._create_success_response()
        return self._create_error_response("Failed to lock device")

    def _handle_unlock(self, message: UnlockMessage) -> StatusAnswer:
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

    def _handle_reset_config(self, message: ResetConfigMessage) -> StatusAnswer:
        """
        Handle resetConfig message.

        Args:
            message: ResetConfigMessage model

        Returns:
            Success response
        """
        self.logger.info(
            "Handling ResetConfigMessage to reset device configuration to default"
        )
        self.config_manager.update_config(ConfigManager.DEFAULT_CONFIG)
        return self._create_success_response()

    def _handle_reset_engine(self, message: ResetEngineMessage) -> AnswerType:
        """
        Handle resetEngine message.

        Args:
            message: ResetEngineMessage model

        Returns:
            Success response
        """
        self.logger.info("Handling ResetEngineMessage to reset the engine state")
        empty_recognition = AnprEvent(
            anpr=RecognitionEvent(
                date=datetime.fromtimestamp(0),
                decision=RecognitionDecision(
                    plate="", reliability=0, context="F", jpeg=None
                ),
            )
        )
        self.data_store.set_current_recognition(empty_recognition)
        return self._create_success_response()

    def _handle_set_config(self, message: SetConfigMessage) -> AnswerType:
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

        try:
            config = message_data.get("config", {})
            cameras = config.get("cameras", {})
            camera = cameras.get("camera", {})
            anpr = camera.get("anpr", {})
            plate_reliability = anpr.get("@plateReliability")

            if plate_reliability is not None:
                self.config_manager.set_value(
                    "plateReliability", int(plate_reliability)
                )
        except (KeyError, ValueError, TypeError) as e:
            return self._create_error_response(f"Invalid config format: {str(e)}")

        return self._create_success_response()

    def _handle_edit_database(self, message: EditDatabaseMessage) -> AnswerType:
        """
        Handle editDatabase message.

        Args:
            message: EditDatabaseMessage model

        Returns:
            Success response
        """
        self.logger.info("Handling EditDatabaseMessage to modify the database")
        message_data = message.edit_database

        add_plate = getattr(message_data, "add_plate", None)
        if add_plate is not None:
            try:
                plate = add_plate.value
                self.data_store.add_plate_to_database(plate)
                return self._create_success_response()
            except Exception as e:
                return self._create_error_response(f"Invalid add plate data: {str(e)}")

        del_plate = getattr(message_data, "del_plate", None)
        if del_plate is not None:
            try:
                plate = del_plate.value
                if self.data_store.remove_plate_from_database(plate):
                    return self._create_success_response()
                return self._create_error_response(f"Plate not found: {plate}")
            except Exception as e:
                return self._create_error_response(
                    f"Invalid delete plate data: {str(e)}"
                )

        return self._create_error_response("Invalid database edit operation")

    def _handle_reset_counters(self, message: ResetCountersMessage) -> AnswerType:
        """
        Handle resetCounters message.

        Args:
            message: ResetCountersMessage model

        Returns:
            Success response
        """
        self.logger.info("Handling ResetCountersMessage to reset counters")
        return self._create_success_response()

    def _handle_allow_set_config(self, message: AllowSetConfigMessage) -> AnswerType:
        """
        Handle allowSetConfig message.

        Args:
            message: AllowSetConfigMessage model

        Returns:
            Success response
        """
        self.logger.info(
            "Handling AllowSetConfigMessage to allow configuration changes"
        )
        self.data_store.set_allow_config(True)
        return self._create_success_response()

    def _handle_forbid_set_config(self, message: ForbidSetConfigMessage) -> AnswerType:
        """
        Handle forbidSetConfig message.

        Args:
            message: ForbidSetConfigMessage model

        Returns:
            Success response
        """
        self.logger.info(
            "Handling ForbidSetConfigMessage to forbid configuration changes"
        )
        self.data_store.set_allow_config(False)
        return self._create_success_response()

    def _handle_calibrate_zoom_focus(
        self, message: CalibrateZoomFocusMessage
    ) -> AnswerType:
        """
        Handle calibrateZoomFocus message.

        Args:
            message: CalibrateZoomFocusMessage model

        Returns:
            Success response
        """
        self.logger.info(
            "Handling CalibrateZoomFocusMessage to calibrate zoom and focus"
        )
        return self._create_success_response()

    def _handle_set_enable_streams(self, stream_config: StreamConfig) -> None:
        """
        Handle setEnableStreams message.

        Args:
            stream_config: StreamConfig model

        Returns:
            Stream response
        """
        self.logger.info(
            "Handling SetEnableStreamsRequest to configure stream settings"
        )
        self.data_store.set_stream_config(stream_config)


    def _handle_update(self, message: UpdateMessage) -> AnswerType:
        self.logger.info("Handling UpdateMessage to update device state")
        return self._create_success_response()

    def _handle_setup(self, message: SetupMessage) -> AnswerType:
        self.logger.info("Handling SetupMessage to perform setup operations")
        return self._create_success_response()

    def _handle_keep_alive(self, message: KeepAliveMessage) -> AnswerType:
        self.logger.info("Handling KeepAliveMessage to maintain connection")
        return self._create_success_response()

    def _handle_set_security(self, message: SetSecurityMessage) -> AnswerType:
        """
        Handle setSecurity message.

        Args:
            message: SetSecurityMessage model

        Returns:
            Success response or error response
        """
        self.logger.info("Handling SetSecurityMessage to update security settings")
        
        if not self.data_store.is_device_locked():
            return self._create_error_response("Device must be locked to change security settings")
        
        # Extract security settings from message
        security_config = message.set_security
        
        # Check for lock password changes
        if security_config.new_lock_password is not None:
            # Verify current password if needed
            if self.data_store.has_lock_password() and security_config.current_lock_password is None:
                return self._create_error_response("Current password required to change lock password")
            
            # Update lock password
            self.data_store.set_lock_password(security_config.new_lock_password)
            
            # Update password hint if provided
            if security_config.lock_password_hint is not None:
                self.data_store.set_lock_password_hint(security_config.lock_password_hint)
        
        # Handle RSA encryption settings if present
        if security_config.rsa_hint is not None:
            self.data_store.set_rsa_hint(security_config.rsa_hint)
        
        return self._create_success_response()

    def _handle_test_ftp(self, message: TestFTPMessage) -> AnswerType:
        """
        Handle testFTP message.

        Args:
            message: TestFTPMessage model

        Returns:
            Success response or error response
        """
        self.logger.info("Handling TestFTPMessage to test FTP server connectivity")
        
        # Extract FTP server details
        ftp_config = message.test_ftp
        
        if not ftp_config.address:
            return self._create_error_response("FTP server address is required")
        
        # In a real implementation, we would test the connection
        # For simulation, we'll just return success
        self.logger.info(f"Simulating FTP test to server: {ftp_config.address}")
        
        return self._create_success_response()

    def _handle_test_ntp(self, message: TestNTPMessage) -> AnswerType:
        """
        Handle testNTP message.

        Args:
            message: TestNTPMessage model

        Returns:
            Success response or error response
        """
        self.logger.info("Handling TestNTPMessage to test NTP server connectivity")
        
        # Extract NTP server details
        ntp_config = message.test_ntp
        
        if not ntp_config.host:
            return self._create_error_response("NTP server host is required")
        
        # In a real implementation, we would test the connection
        # For simulation, we'll just return success
        self.logger.info(f"Simulating NTP test to server: {ntp_config.host}")
        
        return self._create_success_response()

    def _handle_update_web_firmware(self, message: UpdateWebFirmwareMessage) -> AnswerType:
        """
        Handle updateWebFirmware message.

        Args:
            message: UpdateWebFirmwareMessage model

        Returns:
            Success response or error response
        """
        self.logger.info("Handling UpdateWebFirmwareMessage to update firmware from web")
        
        # Extract firmware URL
        firmware_config = message.update_web_firmware
        
        if not firmware_config.url:
            return self._create_error_response("Firmware URL is required")
        
        # In a real implementation, we would download and install the firmware
        # For simulation, we'll just return success
        self.logger.info(f"Simulating firmware update from URL: {firmware_config.url}")
        
        return self._create_success_response()

    def _handle_erase_database(self, message: EraseDatabaseMessage) -> AnswerType:
        """
        Handle eraseDatabase message.

        Args:
            message: EraseDatabaseMessage model

        Returns:
            Success response or error response
        """
        self.logger.info("Handling EraseDatabaseMessage to erase the internal database")
        
        if not self.data_store.is_device_locked():
            return self._create_error_response("Device must be locked to erase database")
        
        # Clear the database
        if self.data_store.clear_database():
            return self._create_success_response()
        
        return self._create_error_response("Failed to erase database")

    def _handle_reboot(self, message: RebootMessage) -> AnswerType:
        """
        Handle reboot message.

        Args:
            message: RebootMessage model

        Returns:
            Success response or error response
        """
        self.logger.info("Handling RebootMessage to reboot the device")
        
        if not self.data_store.is_device_locked():
            return self._create_error_response("Device must be locked to reboot")
        
        # In a real implementation, we would reboot the device
        # For simulation, we'll just reset some state
        self.data_store.simulate_reboot()
        
        return self._create_success_response()
