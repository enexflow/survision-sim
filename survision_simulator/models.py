from datetime import datetime
from typing import Dict, List, Literal, Optional, Any, Type, TypeVar, Union

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    TypeAdapter,
    ConfigDict,
)

T = TypeVar("T", bound=BaseModel)


def validate_model(model_class: Type[T], data: Any) -> T:
    """Helper function to validate data with a model class."""
    return model_class.model_validate(data)


class PlateModel(BaseModel):
    """Model for a license plate."""

    value: str = Field(alias="@value")


class AddPlateModel(BaseModel):
    """Model for adding a plate."""

    add_plate: PlateModel = Field(alias="addPlate")


class DelPlateModel(BaseModel):
    """Model for deleting a plate."""

    del_plate: PlateModel = Field(alias="delPlate")


class DatabaseMatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    plate: str = Field(alias=str("@plate"))
    distance: Optional[int] = Field(alias=str("@distance"))

class CharacterReliability(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    index: int = Field(alias=str("@index"))
    reliability: int = Field(alias=str("@reliability"))

class ReliabilityPerCharacter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    char: List[CharacterReliability]

class Speed(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    instant_speed_km_h: Optional[int] = Field(alias=str("@instantSpeed_km_h"))
    interdistance_ms: Optional[int] = Field(alias=str("@interdistance_ms"))
    reliability_speed: Optional[int] = Field(alias=str("@reliability_speed"))
    plate_from: Optional[str] = Field(alias=str("@plateFrom"))

class RecognitionDecision(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    plate: Optional[str] = Field(alias=str("@plate"))
    x: Optional[int] = Field(alias=str("@x"), default=None)
    y: Optional[int] = Field(alias=str("@y"), default=None)
    x_origin: Optional[int] = Field(alias=str("@xOrigin"), default=None)
    y_origin: Optional[int] = Field(alias=str("@yOrigin"), default=None)
    width: Optional[int] = Field(alias=str("@width"), default=None)
    height: Optional[int] = Field(alias=str("@height"), default=None)
    sinus: Optional[float] = Field(alias=str("@sinus"), default=None)
    reliability: Optional[int] = Field(alias=str("@reliability"), default=None)
    direction: Optional[str] = Field(alias=str("@direction"), default=None)
    context: Optional[str] = Field(alias=str("@context"), default=None)
    context_iso_alpha2: Optional[str] = Field(alias=str("@context_isoAlpha2"), default=None)
    context_iso_alpha3: Optional[str] = Field(alias=str("@context_isoAlpha3"), default=None)
    plate_occurences: Optional[int] = Field(alias=str("@plateOccurences"), default=None)
    plate_from: Optional[str] = Field(alias=str("@plateFrom"), default=None)
    plate_background: Optional[str] = Field(alias=str("@plateBackground"), default=None)
    contrast: Optional[int] = Field(alias=str("@contrast"), default=None)
    square_plate: Optional[bool] = Field(alias=str("@squarePlate"), default=None)
    
    database: Optional[DatabaseMatch] = None
    reliability_per_character: Optional[ReliabilityPerCharacter] = None
    jpeg: Optional[str] = None
    context_jpeg: Optional[str] = None
    speed: Optional[Speed] = None


class RecognitionEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: datetime = Field(alias=str("@date"), default_factory=datetime.now)
    id: int = Field(alias=str("@id"), default=0)
    session: int = Field(alias=str("@session"), default=0)
    decision: RecognitionDecision

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: Any) -> datetime:
        """Parse date from string if needed."""
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


class AnprEvent(BaseModel):
    """Model for an ANPR (automatic number plate recognition) event."""

    anpr: RecognitionEvent


class DeviceInfo(BaseModel):
    """Model for device information."""

    type: str = Field(serialization_alias="@type")
    firmware_version: str = Field(serialization_alias="@firmwareVersion")
    serial: str = Field(serialization_alias="@serial")
    mac_address: str = Field(serialization_alias="@macAddress")
    status: str = Field(serialization_alias="@status")
    locked: bool = Field(serialization_alias="@locked")

    @field_validator("locked", mode="before")
    @classmethod
    def parse_locked(cls, value: Any) -> bool:
        """Parse locked from string if needed."""
        if isinstance(value, str):
            return value == "1"
        return bool(value)


class CameraInfo(BaseModel):
    """Model for camera information."""

    id: str = Field(serialization_alias="@id")
    enabled_algorithms: Dict[str, Optional[Any]] = Field(
        serialization_alias="enabledAlgorithms"
    )


class NetworkInfo(BaseModel):
    """Model for network information."""

    mac_address: str = Field(serialization_alias="@macAddress")
    connected: bool = Field(serialization_alias="@connected")

    @field_validator("connected", mode="before")
    @classmethod
    def parse_connected(cls, value: Any) -> bool:
        """Parse connected from string if needed."""
        if isinstance(value, str):
            return value == "1"
        return bool(value)


class SecurityInfo(BaseModel):
    """Model for security information."""

    lock_password_needed: bool = Field(serialization_alias="@lockPasswordNeeded")
    rsa_crypted: bool = Field(serialization_alias="@rsaCrypted")

    @field_validator("lock_password_needed", "rsa_crypted", mode="before")
    @classmethod
    def parse_bool(cls, value: Any) -> bool:
        """Parse boolean from string if needed."""
        if isinstance(value, str):
            return value == "1"
        return bool(value)


class AnprInfo(BaseModel):
    """Model for ANPR information."""

    version: str = Field(serialization_alias="@version")
    possible_contexts: str = Field(serialization_alias="@possibleContexts")


class DeviceInfoResponse(BaseModel):
    """Model for device information response."""

    sensor: DeviceInfo
    cameras: Dict[str, CameraInfo]
    network: Dict[str, NetworkInfo]
    security: SecurityInfo
    anpr: AnprInfo


class InfosResponse(BaseModel):
    """Model for infos response."""

    infos: DeviceInfoResponse


class CameraStreamConfig(BaseModel):
    id: str = Field(alias="@id")
    enabled: bool = Field(alias="@enabled")


class StreamConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    config_changes: bool = Field(default=False, alias=str("@configChanges"))
    info_changes: bool = Field(default=False, alias=str("@infoChanges"))
    traces: bool = Field(default=False, alias=str("@traces"))
    cameras: Dict[str, CameraStreamConfig] = Field(default_factory=dict)

    @field_validator("config_changes", "info_changes", "traces", mode="before")
    @classmethod
    def parse_bool(cls, value: Any) -> bool:
        """Parse boolean from string if needed."""
        if isinstance(value, str):
            return value == "1"
        return bool(value)


class LockedOperationMessage(BaseModel):
    """Base class for messages that require device locking."""

    pass


class ProhibitedOverHTTPMessage(BaseModel):
    """Base class for messages that are prohibited over HTTP."""

    pass


class GetConfigMessage(BaseModel):
    """Model for getConfig message."""

    get_config: None = Field(default=None, alias="getConfig")


class GetCurrentLogMessage(BaseModel):
    """Model for getCurrentLog message."""

    get_current_log: Optional[Dict[str, Any]] = Field(
        default=None, alias="getCurrentLog"
    )


class GetDataBaseModel(BaseModel):
    """Model for getDatabase message."""

    get_database: None = Field(default=None, alias="getDatabase")


class GetDateMessage(BaseModel):
    """Model for getDate message."""

    get_date: None = Field(default=None, alias="getDate")


class GetImageMessage(BaseModel):
    """Model for getImage message."""

    get_image: Optional[Dict[str, Any]] = Field(default=None, alias="getImage")


class GetInfosMessage(BaseModel):
    """Model for getInfos message."""

    get_infos: None = Field(default=None, alias="getInfos")


class GetLogMessage(BaseModel):
    """Model for getLog message."""

    get_log: Optional[Dict[str, Any]] = Field(default=None, alias="getLog")


class GetTracesMessage(BaseModel):
    """Model for getTraces message."""

    get_traces: None = Field(default=None, alias="getTraces")


class GetXSDMessage(BaseModel):
    """Model for getXSD message."""

    get_xsd: None = Field(default=None, alias="getXSD")


class OpenBarrierMessage(BaseModel):
    """Model for openBarrier message."""

    open_barrier: None = Field(default=None, alias="openBarrier")


class TriggerOnMessage(BaseModel):
    """Model for triggerOn message."""

    trigger_on: Dict[str, Any] = Field(alias="triggerOn")

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set default values if needed."""
        if "triggerOn" in data:
            trigger_data = data["triggerOn"]
            if trigger_data is None:
                data["triggerOn"] = {}
        return data


class TriggerOffMessage(BaseModel):
    """Model for triggerOff message."""

    trigger_off: Dict[str, Any] = Field(alias="triggerOff")

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set default values if needed."""
        if "triggerOff" in data:
            trigger_data = data["triggerOff"]
            if trigger_data is None:
                data["triggerOff"] = {}
        return data


class LockPassword(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    password: str = Field(alias=str("@password"))


class LockMessage(ProhibitedOverHTTPMessage):
    """Model for lock message."""

    lock: LockPassword


class UnlockMessage(BaseModel):
    """Model for unlock message."""

    unlock: None = Field(default=None, alias="unlock")


class ResetConfigMessage(LockedOperationMessage):
    """Model for resetConfig message."""

    reset_config: None = Field(default=None, alias="resetConfig")


class ResetEngineMessage(BaseModel):
    """Model for resetEngine message."""

    reset_engine: None = Field(default=None, alias="resetEngine")


class AnprConfig(BaseModel):
    """Model for ANPR configuration."""

    plate_reliability: Optional[str] = Field(default=None, alias="@plateReliability")
    context: Optional[str] = Field(default=None, alias="@context")
    square_plates: Optional[str] = Field(default=None, alias="@squarePlates")


class CameraConfig(BaseModel):
    """Model for camera configuration."""

    anpr: Optional[AnprConfig] = None


class CamerasConfig(BaseModel):
    """Model for cameras configuration."""

    camera: Optional[CameraConfig] = None


class Config(BaseModel):
    """Model for configuration."""

    cameras: Optional[CamerasConfig] = None


class SetConfigMessage(LockedOperationMessage):
    """Model for setConfig message."""

    set_config: Dict[str, Any] = Field(alias="setConfig")

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set default values if needed."""
        if "setConfig" in data:
            config_data = data["setConfig"]
            if config_data is None:
                data["setConfig"] = {}
        return data


class EditDatabaseMessage(LockedOperationMessage):
    """Model for editDatabase message."""

    edit_database: Union[AddPlateModel, DelPlateModel] = Field(alias="editDatabase")


class ResetCountersMessage(BaseModel):
    """Model for resetCounters message."""

    reset_counters: None = Field(default=None, alias="resetCounters")


class AllowSetConfigMessage(LockedOperationMessage):
    """Model for allowSetConfig message."""

    allow_set_config: Optional[Dict[str, Any]] = Field(
        default=None, alias="allowSetConfig"
    )


class ForbidSetConfigMessage(LockedOperationMessage):
    """Model for forbidSetConfig message."""

    forbid_set_config: Optional[Dict[str, Any]] = Field(
        default=None, alias="forbidSetConfig"
    )


class CalibrateZoomFocusMessage(LockedOperationMessage):
    """Model for calibrateZoomFocus message."""

    calibrate_zoom_focus: Optional[Dict[str, Any]] = Field(
        default=None, alias="calibrateZoomFocus"
    )


class SetEnableStreamsRequest(BaseModel):
    """Model for setEnableStreams request."""

    set_enable_streams: StreamConfig = Field(alias="setEnableStreams")


class KeepAliveMessage(ProhibitedOverHTTPMessage):
    """Model for keepAlive message."""

    keep_alive: None = Field(default=None, alias="keepAlive")


class UpdateMessage(ProhibitedOverHTTPMessage):
    """Model for update message."""

    update: Dict[str, Any] = Field(alias="update")


class SetupMessage(ProhibitedOverHTTPMessage):
    """Model for setup message."""

    setup: Dict[str, Any] = Field(alias="setup")


class IEEE8021XConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    certificate_password: Optional[str] = Field(
        default=None, alias=str("@certificatePassword")
    )
    identity: Optional[str] = Field(default=None, alias=str("@identity"))
    authentication: str = Field(alias=str("@authentication"))
    pfx: Optional[str] = Field(default=None, alias="PFX")
    certificate: Optional[str] = Field(default=None, alias="certificate")
    private_key: Optional[str] = Field(default=None, alias="privateKey")
    certificate_authority: Optional[str] = Field(
        default=None, alias="certificateAuthority"
    )


class SecurityConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    new_lock_password: Optional[str] = Field(
        default=None, alias=str("@newLockPassword")
    )
    current_lock_password: Optional[str] = Field(
        default=None, alias=str("@currentLockPassword")
    )
    lock_password_hint: Optional[str] = Field(
        default=None, alias=str("@lockPasswordHint")
    )
    rsa_hint: Optional[str] = Field(default=None, alias=str("@rsaHint"))
    rsa_public_key_password: Optional[str] = Field(
        default=None, alias=str("@rsaPublicKeyPassword")
    )
    ssl_certificate_password: Optional[str] = Field(
        default=None, alias=str("@sslCertificatePassword")
    )
    ssl_certificate_reset: Optional[bool] = Field(
        default=None, alias=str("@sslCertificateReset")
    )
    ssl_pfx: Optional[str] = Field(default=None, alias="sslPFX")
    ssl_certificate: Optional[str] = Field(default=None, alias="sslCertificate")
    ssl_private_key: Optional[str] = Field(default=None, alias="sslPrivateKey")
    ssl_certificate_authority: Optional[str] = Field(
        default=None, alias="sslCertificateAuthority"
    )
    rsa_public_key: Optional[str] = Field(default=None, alias="rsaPublicKey")
    ieee8021x: Optional[IEEE8021XConfig] = Field(default=None, alias="IEEE8021X")

    @field_validator("ssl_certificate_reset", mode="before")
    @classmethod
    def parse_bool(cls, value: Any) -> Optional[bool]:
        """Parse boolean from string if needed."""
        if value is None:
            return None
        if isinstance(value, str):
            return value == "1" or value.lower() == "true"
        return bool(value)


class TestFTPConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    address: str = Field(alias=str("@address"))
    port: Optional[int] = Field(default=None, alias=str("@port"))
    login: Optional[str] = Field(default=None, alias=str("@login"))
    password: Optional[str] = Field(default=None, alias=str("@password"))
    protocol: Optional[str] = Field(default=None, alias=str("@protocol"))
    file_name: Optional[str] = Field(default=None, alias=str("@fileName"))


class TestNTPConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    host: str = Field(alias=str("@host"))


class UpdateWebFirmwareConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(alias=str("@url"))


class SetSecurityMessage(LockedOperationMessage):
    """Model for setSecurity message."""

    set_security: SecurityConfig = Field(alias="setSecurity")


class TestFTPMessage(BaseModel):
    """Model for testFTP message."""

    test_ftp: TestFTPConfig = Field(alias="testFTP")


class TestNTPMessage(BaseModel):
    """Model for testNTP message."""

    test_ntp: TestNTPConfig = Field(alias="testNTP")


class UpdateWebFirmwareMessage(BaseModel):
    """Model for updateWebFirmware message."""

    update_web_firmware: UpdateWebFirmwareConfig = Field(alias="updateWebFirmware")


class EraseDatabaseMessage(LockedOperationMessage):
    """Model for eraseDatabase message."""

    erase_database: None = Field(default=None, alias="eraseDatabase")


class RebootMessage(LockedOperationMessage):
    """Model for reboot message."""

    reboot: None = Field(default=None, alias="reboot")


class Warning(BaseModel):
    text: str = Field(serialization_alias="@text")
    config_path: Optional[str] = Field(default=None, serialization_alias="@configPath")
    source_location: Optional[str] = Field(
        default=None, serialization_alias="@sourceLocation"
    )

    def as_answer(self) -> "StatusAnswer":
        return StatusAnswer(answer=self)


class SuccessResponse(BaseModel):
    """Model for success response."""

    status: Literal["ok"] = Field(default="ok", alias="@status")

    def as_answer(self) -> "StatusAnswer":
        return StatusAnswer(answer=self)


class ErrorResponse(BaseModel):
    """Model for error response."""

    status: Literal["failed"] = Field(default="failed", alias="@status")
    error_text: str = Field(serialization_alias="@errorText")

    @classmethod
    def for_error_text(cls, error_text: str) -> "ErrorResponse":
        """Create an error response for a given error text."""
        return cls(error_text=error_text)

    def as_answer(self) -> "StatusAnswer":
        return StatusAnswer(answer=self)


class StatusAnswer(BaseModel):
    """Base model for responses."""

    answer: Union[SuccessResponse, ErrorResponse, Warning]


class TriggerAnswerData(BaseModel):
    """Model for trigger response data."""

    status: Literal["ok", "failed"] = Field(serialization_alias="@status")
    trigger_id: int = Field(serialization_alias="@triggerId")
    error_text: Optional[str] = Field(default=None, serialization_alias="@errorText")

    @classmethod
    def ok_for_id(cls, id: int) -> "TriggerAnswerData":
        """Check if the trigger answer is ok for a given id."""
        return cls(status="ok", trigger_id=id)

    @classmethod
    def failed_for_id(cls, id: int) -> "TriggerAnswerData":
        """Check if the trigger answer is failed for a given id."""
        return cls(status="failed", trigger_id=id)

    def as_answer(self) -> "TriggerAnswer":
        """Convert the trigger answer data to a trigger answer."""
        return TriggerAnswer(triggerAnswer=self)


class TriggerAnswer(BaseModel):
    """Model for trigger response."""

    trigger_answer: TriggerAnswerData = Field(alias="triggerAnswer")


class ConfigAnswer(BaseModel):
    """Model for config response."""

    config: Dict[str, Any]


class PlateReading(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: str = Field(alias=str("@value"))


class DatabaseAnswer(BaseModel):
    """Model for database response."""

    database: List[PlateReading]


class DateAnswer(BaseModel):
    """Model for date response."""

    date: Dict[str, Any]


class ImageAnswer(BaseModel):
    """Model for image response."""

    image: Dict[str, Any] = Field(...)


class InfosAnswer(BaseModel):
    """Model for infos response."""

    infos: DeviceInfoResponse = Field(...)


class LogAnswer(BaseModel):
    """Model for log response."""

    anpr: RecognitionEvent = Field(...)


class TracesAnswer(BaseModel):
    """Model for traces response."""

    traces: Dict[str, Any] = Field(...)


class XSDAnswer(BaseModel):
    """Model for XSD response."""

    xsd: str = Field(...)


class StreamAnswer(BaseModel):
    """Model for stream response."""

    subscriptions: Dict[str, bool] = Field(...)


AnswerType = Union[
    StatusAnswer,
    TriggerAnswer,
    ConfigAnswer,
    DatabaseAnswer,
    DateAnswer,
    ImageAnswer,
    InfosAnswer,
    LogAnswer,
    TracesAnswer,
    XSDAnswer,
    StreamAnswer,
]

MessageType = Union[
    GetConfigMessage,
    GetCurrentLogMessage,
    GetDataBaseModel,
    GetDateMessage,
    GetImageMessage,
    GetInfosMessage,
    GetLogMessage,
    GetTracesMessage,
    GetXSDMessage,
    OpenBarrierMessage,
    TriggerOnMessage,
    TriggerOffMessage,
    LockMessage,
    UnlockMessage,
    ResetConfigMessage,
    ResetEngineMessage,
    SetConfigMessage,
    EditDatabaseMessage,
    ResetCountersMessage,
    AllowSetConfigMessage,
    ForbidSetConfigMessage,
    CalibrateZoomFocusMessage,
    SetEnableStreamsRequest,
    KeepAliveMessage,
    UpdateMessage,
    SetupMessage,
    SetSecurityMessage,
    TestFTPMessage,
    TestNTPMessage,
    UpdateWebFirmwareMessage,
    EraseDatabaseMessage,
    RebootMessage,
]
MessageTypeModel: TypeAdapter[MessageType] = TypeAdapter(MessageType)


def parse_message(json_data: bytes) -> MessageType:
    """
    Parse a JSON message into the appropriate Pydantic model.

    Args:
        json_data: JSON data

    Returns:
        Pydantic model
    """
    if not json_data:
        raise ValueError("Empty message")
    return MessageTypeModel.validate_json(json_data)


def requires_locking(message: MessageType) -> bool:
    """
    Check if a message requires device locking.

    Args:
        message: The message to check

    Returns:
        True if the message requires locking, False otherwise
    """
    return isinstance(message, LockedOperationMessage)


def is_prohibited_over_http(message: MessageType) -> bool:
    """
    Check if a message is prohibited over HTTP.

    Args:
        message: The message to check

    Returns:
        True if the message is prohibited over HTTP, False otherwise
    """
    return isinstance(message, ProhibitedOverHTTPMessage)
