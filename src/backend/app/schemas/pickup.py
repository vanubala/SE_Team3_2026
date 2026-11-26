from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PickupVerifyRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lockerId: UUID
    pickupCode: str = Field(pattern=r'^\d{6}$', repr=False)


class PickupVerifyResponse(BaseModel):
    parcelId: UUID
    compartmentId: UUID
    compartmentNumber: int
    doorCommand: Literal['UNLOCK'] = 'UNLOCK'
    pickupSessionToken: str


class PickupConfirmRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    parcelId: UUID
    compartmentId: UUID
    doorClosed: bool
    parcelDetected: bool = False
    pickupSessionToken: str = Field(min_length=1, max_length=2048, repr=False)


class PickupConfirmResponse(BaseModel):
    parcelId: UUID
    status: str
    compartmentStatus: str
