import asyncio
import time
from datetime import datetime
from threading import Thread
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from browser_manager import BrowserManager
from log.logger import logger
from worker.main import main
from worker.server import anchor_coupon_create_main


def to_timestamp(dt_str: str) -> int:
    """将字符串时间转为时间戳（秒）"""
    dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(dt_obj.timetuple()))


class CouponRequest(BaseModel):
    id: str
    anchorCouponScene: str
    couponName: str
    applyTimeType: str
    applyTime: Optional[str] = ""
    startApplyTime: str
    endApplyTime: str
    kolUserTag: str
    maxApplyTimes: str
    type: str
    threshold: Optional[str] = ""
    credit: str
    totalAmount: str
    useTimeType: str
    useTime: Optional[str] = ""
    startUseTime: str
    endUseTime: str
    deviceNoList: str


class ApiServer:
    def __init__(self):
        self.app = FastAPI()
        self.browser_managers: list[BrowserManager] = []

        self._setup_routes()

    def _setup_routes(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.get("/status")
        async def get_status():
            logger.info("get status")
            return {"running": True, "user_count": len(self.browser_managers)}

        @self.app.post("/start/{user_id}")
        async def start_browser(user_id: str):
            port = 9000 + len(self.browser_managers)
            manager = BrowserManager(user_id=user_id, port=port)
            ok = await asyncio.to_thread(manager.initialize)
            if ok:
                self.browser_managers.append(manager)
                return {"status": "success", "user_id": user_id, "port": port}
            return JSONResponse(status_code=500, content={"status": "fail", "message": f"启动失败: {user_id}"})

        @self.app.post("/stop")
        async def stop_all():
            await asyncio.gather(*(asyncio.to_thread(m.cleanup) for m in self.browser_managers if m.is_running))
            self.browser_managers.clear()
            return {"status": "success", "message": "所有浏览器已关闭"}

        @self.app.get("/attachBrowser")
        async def attach_browser_api():
            result = main()
            if result:
                return {"status": "success", "data": result}
            return JSONResponse(status_code=500, content={"status": "fail", "message": f"连接浏览器启动失败"})

        @self.app.post("/anchor_coupon/create")
        async def get_basic_list_api(data: CouponRequest):
            request_data = {
                "id": data.id,
                "couponName": data.couponName,
                "startApplyTime": to_timestamp(data.startApplyTime),
                "endApplyTime": to_timestamp(data.endApplyTime),
                "startUseTime": to_timestamp(data.startUseTime),
                "endUseTime": to_timestamp(data.endUseTime),
                "anchorCouponScene": data.anchorCouponScene,
                "applyTimeType": data.applyTimeType,
                "applyTime": data.applyTime,
                "kolUserTag": data.kolUserTag,
                "maxApplyTimes": data.maxApplyTimes,
                "type": data.type,
                "threshold": data.threshold,
                "credit": data.credit,
                "totalAmount": data.totalAmount,
                "useTimeType": data.useTimeType,
                "useTime": data.useTime,
                "deviceNoList": data.deviceNoList,
            }
            result = anchor_coupon_create_main(request_data)
            response_status = result.get("status")
            response_data = result.get("data")
            response_msg = result.get("message")
            if response_status == "success":
                return JSONResponse(status_code=200,
                                    content={"status": response_status, "data": response_data})
            return JSONResponse(status_code=500,
                                content={"status": response_status, "message": response_msg})

    def start(self, host="127.0.0.1", port=8000):
        def _run():
            uvicorn.run(self.app, host=host, port=port, log_level="info")

        Thread(target=_run, daemon=True).start()
