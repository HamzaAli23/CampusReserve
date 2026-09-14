from datetime import datetime, timezone
from enum import StrEnum

from pydantic import field_serializer
from sqlmodel import Field, SQLModel


class BookingStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class ResourceBase(SQLModel):
    name: str = Field(min_length=2, max_length=80)
    kind: str = Field(min_length=2, max_length=40)
    capacity: int = Field(default=1, ge=1, le=1000)


class Resource(ResourceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ResourceCreate(ResourceBase):
    pass


class BookingBase(SQLModel):
    resource_id: int = Field(foreign_key="resource.id")
    booked_by: str = Field(min_length=2, max_length=100)
    starts_at: datetime
    ends_at: datetime
    purpose: str = Field(default="Study", min_length=2, max_length=160)


class Booking(BookingBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: BookingStatus = Field(default=BookingStatus.ACTIVE)


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: int
    status: BookingStatus

    @field_serializer("starts_at", "ends_at")
    def serialize_utc_datetime(self, value: datetime) -> str:
        """Mark SQLite's naive stored timestamps as UTC in API responses."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
