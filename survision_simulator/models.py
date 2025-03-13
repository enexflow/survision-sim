from datetime import datetime
from typing import Dict, Literal, Optional, Any, Type, TypeVar, Union, Set

from pydantic import BaseModel, Field, field_validator, model_validator, TypeAdapter

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


class RecognitionDecision(BaseModel):
    """Model for a recognition decision."""

    plate: str = Field(alias="@plate")
    reliability: int = Field(alias="@reliability")
    context: str = Field(alias="@context")
    jpeg: Optional[str] = None


class RecognitionEvent(BaseModel):
    """Model for a recognition event."""

    date: datetime = Field(alias="@date")
    decision: RecognitionDecision

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: Any) -> datetime:
        """Parse date from string if needed."""
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


class AnprEvent(BaseModel):
    """Model for an ANPR event."""

    anpr: RecognitionEvent


class DeviceInfo(BaseModel):
    """Model for device information."""

    type: str = Field(alias="@type")
    firmware_version: str = Field(alias="@firmwareVersion")
    serial: str = Field(alias="@serial")
    mac_address: str = Field(alias="@macAddress")
    status: str = Field(alias="@status")
    locked: bool = Field(alias="@locked")

    @field_validator("locked", mode="before")
    @classmethod
    def parse_locked(cls, value: Any) -> bool:
        """Parse locked from string if needed."""
        if isinstance(value, str):
            return value == "1"
        return bool(value)


class CameraInfo(BaseModel):
    """Model for camera information."""

    id: str = Field(alias="@id")
    enabled_algorithms: Dict[str, Optional[Any]] = Field(alias="enabledAlgorithms")


class NetworkInfo(BaseModel):
    """Model for network information."""

    mac_address: str = Field(alias="@macAddress")
    connected: bool = Field(alias="@connected")

    @field_validator("connected", mode="before")
    @classmethod
    def parse_connected(cls, value: Any) -> bool:
        """Parse connected from string if needed."""
        if isinstance(value, str):
            return value == "1"
        return bool(value)


class SecurityInfo(BaseModel):
    """Model for security information."""

    lock_password_needed: bool = Field(alias="@lockPasswordNeeded")
    rsa_crypted: bool = Field(alias="@rsaCrypted")

    @field_validator("lock_password_needed", "rsa_crypted", mode="before")
    @classmethod
    def parse_bool(cls, value: Any) -> bool:
        """Parse boolean from string if needed."""
        if isinstance(value, str):
            return value == "1"
        return bool(value)


class AnprInfo(BaseModel):
    """Model for ANPR information."""

    version: str = Field(alias="@version")
    possible_contexts: str = Field(alias="@possibleContexts")


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


class StreamConfig(BaseModel):
    """Model for stream configuration."""

    config_changes: bool = Field(default=False, alias="@configChanges")
    info_changes: bool = Field(default=False, alias="@infoChanges")
    traces: bool = Field(default=False, alias="@traces")

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

    get_current_log: Optional[Dict[str, Any]] = Field(default=None, alias="getCurrentLog")


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


class LockMessage(ProhibitedOverHTTPMessage):
    """Model for lock message."""

    lock: Dict[str, Any] = Field(alias="lock")

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set default values if needed."""
        if "lock" in data:
            lock_data = data["lock"]
            if lock_data is None:
                data["lock"] = {}
        return data


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

    allow_set_config: Optional[Dict[str, Any]] = Field(default=None, alias="allowSetConfig")


class ForbidSetConfigMessage(LockedOperationMessage):
    """Model for forbidSetConfig message."""

    forbid_set_config: Optional[Dict[str, Any]] = Field(default=None, alias="forbidSetConfig")


class CalibrateZoomFocusMessage(LockedOperationMessage):
    """Model for calibrateZoomFocus message."""

    calibrate_zoom_focus: Optional[Dict[str, Any]] = Field(default=None, alias="calibrateZoomFocus")


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

class Response(BaseModel):
    """Base model for responses."""


class SuccessResponse(Response):
    """Model for success response."""
    status: Literal["ok"] = Field(default="ok", alias="@status")


class ErrorResponse(Response):
    """Model for error response."""
    status: Literal["failed"] = Field(default="failed", alias="@status")
    error_text: str = Field(alias="@errorText")

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
