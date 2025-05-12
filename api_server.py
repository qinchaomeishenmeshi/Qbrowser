import asyncio
import time
from datetime import datetime
from threading import Thread
from typing import List, Optional, Union

import uvicorn
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, model_validator

from browser_manager import BrowserManager
from log.logger import logger
from worker.main import main as attach_main
from worker.server import anchor_coupon_create_main


def to_timestamp(dt_str: str) -> int:
    """Convert datetime string to UNIX timestamp in seconds."""
    try:
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"时间格式错误，需为 'YYYY-MM-DD HH:MM:SS'，收到: {dt_str}")
    return int(time.mktime(dt_obj.timetuple()))


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


class BrowserManagerStore:
    def __init__(self):
        self._managers: List[BrowserManager] = []
        self._lock = asyncio.Lock()

    async def add(self, manager: BrowserManager):
        async with self._lock:
            self._managers.append(manager)

    async def clear(self):
        async with self._lock:
            for m in self._managers:
                if m.is_running:
                    await asyncio.to_thread(m.cleanup)
            self._managers.clear()

    async def count(self) -> int:
        async with self._lock:
            return len(self._managers)


app = FastAPI()
api_router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.manager_store = BrowserManagerStore()


def get_store():
    return app.state.manager_store


@api_router.get("/status")
async def get_status(store: BrowserManagerStore = Depends(get_store)):
    count = await store.count()
    return {"running": True, "user_count": count}


@api_router.post("/start/{user_id}")
async def start_browser(user_id: str, store: BrowserManagerStore = Depends(get_store)):
    port = 9000 + (await store.count())
    manager = BrowserManager(user_id=user_id, port=port)
    success = await asyncio.to_thread(manager.initialize)
    if not success:
        raise HTTPException(status_code=500, detail=f"启动失败: {user_id}")
    await store.add(manager)
    return {"status": "success", "user_id": user_id, "port": port}


@api_router.post("/stop")
async def stop_all(store: BrowserManagerStore = Depends(get_store)):
    await store.clear()
    return {"status": "success", "message": "所有浏览器已关闭"}


@api_router.get("/attachBrowser")
async def attach_browser_api():
    try:
        result = attach_main()
    except Exception as e:
        logger.error("attachBrowser exception: %s", e)
        raise HTTPException(status_code=500, detail="连接浏览器启动失败")
    if not result:
        raise HTTPException(status_code=500, detail="连接浏览器启动失败, 无返回数据")
    return {"status": "success", "data": result}


@api_router.post("/anchor_coupon/create")
async def create_anchor_coupon(data: CouponRequest):
    payload = data.model_dump()
    result = anchor_coupon_create_main(payload)
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return {"code": 200, "status": "success", "data": result.get("data")}


app.include_router(api_router)


def run_server(host: str = "127.0.0.1", port: int = 8000):
    def _run():
        uvicorn.run(app, host=host, port=port, log_level="info")

    Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    run_server()
