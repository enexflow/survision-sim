from datetime import datetime
from typing import Dict, Optional, Any, Type, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar('T', bound=BaseModel)


def validate_model(model_class: Type[T], data: Any) -> T:
    """Helper function to validate data with a model class."""
    return model_class.model_validate(data)



class PlateModel(BaseModel):
    """Model for a license plate."""
    value: str = Field(alias="@value")


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


class SetEnableStreamsRequest(BaseModel):
    """Model for setEnableStreams request."""
    set_enable_streams: StreamConfig = Field(alias="setEnableStreams")


class SuccessResponse(BaseModel):
    """Model for success response."""
    answer: Dict[str, str] = Field(default_factory=lambda: {"@status": "ok"})


class ErrorResponse(BaseModel):
    """Model for error response."""
    answer: Dict[str, str]

    @classmethod
    def create(cls, error_text: str) -> "ErrorResponse":
        """Create an error response."""
        return cls(answer={"@status": "failed", "@errorText": error_text}) 