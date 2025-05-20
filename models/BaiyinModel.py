from typing import Optional, Union

from pydantic import BaseModel, field_validator, model_validator

from utils.util import to_timestamp


class CouponRequest(BaseModel):
    id: str
    anchorCouponScene: str
    couponName: str
    applyTimeType: str
    applyTime: Optional[str] = ""
    startApplyTime: Union[str, int]
    endApplyTime: Union[str, int]
    kolUserTag: str
    maxApplyTimes: str
    type: str
    threshold: Optional[str] = ""
    goodsIdList: Optional[str] = ""
    goodsIdType: Optional[str] = ""
    credit: str
    totalAmount: str
    useTimeType: str
    useTime: Optional[str] = ""
    startUseTime: Union[str, int]
    endUseTime: Union[str, int]
    deviceNoList: str

    @model_validator(mode="before")
    def convert_times(cls, values: dict) -> dict:
        for field in ("startApplyTime", "endApplyTime", "startUseTime", "endUseTime"):
            val = values.get(field)
            if isinstance(val, str) and val:
                values[field] = to_timestamp(val)
        return values

    @field_validator("startApplyTime", "endApplyTime", "startUseTime", "endUseTime")
    def must_be_int(cls, v):
        if not isinstance(v, int):
            raise TypeError(f"时间字段必须为时间戳(int)，当前: {v}")
        return v


class LivingRequest(BaseModel):
    deviceNoList: str


class LivingCoreDataRequest(BaseModel):
    userId: str
    roomId: str
