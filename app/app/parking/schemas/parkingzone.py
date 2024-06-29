from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParkingZoneBase(BaseModel):
    name: str | None = None
    tag: str | None = None
    parking_id: int | None = None
    parent_id: int | None = None
    floor_name: str | None = None
    floor_number: int | None = None


class ParkingZoneComplete(ParkingZoneBase):
    parent: ParkingZoneBase | None = None
    children: list["ParkingZone"] = Field(default_factory=list)
    pricings: list["ParkingZonePrice"] = Field(default_factory=list)


class ParkingZoneCreate(ParkingZoneBase):
    name: str


class ParkingZoneUpdate(ParkingZoneBase): ...


class ParkingZoneInDBBase(ParkingZoneComplete):
    id: int | None = None 
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class ParkingZone(ParkingZoneInDBBase):
    parent: str| None = Field(default=None, exclude=True)
    class Config:
        @staticmethod
        def json_schema_extra(schema, model):
            if "properties" in schema:
                schema["properties"].pop("parent", None)


class ParkingZoneInDB(ParkingZoneInDBBase): ...


class ParkingZonePriceBase(BaseModel):
    priority: int | None = None
    zone_id: int | None = None
    price_id: int | None = None


class ParkingZonePriceCreate(ParkingZonePriceBase):
    priority: int = Field(ge=1, le=100)
    zone_id: int
    price_id: int


class ParkingZonePriceUpdate(ParkingZonePriceBase): ...


class ParkingZonePriceInDBBase(ParkingZonePriceBase):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class ParkingZonePrice(ParkingZonePriceInDBBase): ...


class ParkingZonePriceInDB(ParkingZonePriceInDBBase): ...


class SetZonePriceInput(BaseModel):
    price_id: int
    priority: int = Field(ge=1, le=100)


class ParkingZoneRule(ParkingZoneBase):
    id: int | None = None
