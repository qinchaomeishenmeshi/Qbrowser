from fastapi import APIRouter, HTTPException

from models.BaiyinModel import CouponRequest, LivingRequest, LivingCoreDataRequest
from service.browser_service import browser_service
from worker.coupon_client import anchor_coupon_create_main
from worker.living_client import get_history_live_main, get_core_data_main
from worker.eos_client import get_live_room_list_main,get_replay_punish_list_main

# from worker.live_client import test

business_router = APIRouter()


@business_router.post("/anchor_coupon/create")
async def create_anchor_coupon(data: CouponRequest):
    # 1. 解析 user_id 列表
    payload = data.model_dump()
    print("请求参数:", payload)

    user_ids = payload.get("deviceNoList")
    if not user_ids:
        raise HTTPException(status_code=400, detail="缺少 设备编号 字段")
    # 兼容字符串和列表
    if isinstance(user_ids, str):
        user_ids = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
    if not isinstance(user_ids, list) or not user_ids:
        raise HTTPException(
            status_code=400, detail="deviceNoList/user_ids 格式错误或为空"
        )

    # 2. 确保所有 user_id 的浏览器实例已存在且唯一
    results = await browser_service.start_browsers(user_ids)
    success_status = {"started", "already_running"}
    failed = [r for r in results if r["status"] not in success_status]
    if failed:
        raise HTTPException(status_code=500, detail=f"部分浏览器启动失败: {failed}")

    # 3. 执行业务逻辑
    try:
        result = await anchor_coupon_create_main(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"业务处理失败: {e}")

    # 4. 返回结果
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return {"code": 200, "status": "success", "data": result.get("data")}


@business_router.post("/live/data")
async def get_live_data(data: LivingRequest):
    """
    获取直播间数据
    :param user_id: 用户ID
    :return: 直播间数据
    """
    # 确保所有用户浏览器实例已启动
    # 1. 解析 user_id 列表
    payload = data.model_dump()
    print("请求参数:", payload)

    user_ids = payload.get("deviceNoList")
    if not user_ids:
        raise HTTPException(status_code=400, detail="缺少 设备编号 字段")
    # 兼容字符串和列表
    if isinstance(user_ids, str):
        user_ids = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
    if not isinstance(user_ids, list) or not user_ids:
        raise HTTPException(
            status_code=400, detail="deviceNoList/user_ids 格式错误或为空"
        )

    # 2. 确保所有 user_id 的浏览器实例已存在且唯一
    results = await browser_service.start_browsers(user_ids)
    success_status = {"started", "already_running"}
    failed = [r for r in results if r["status"] not in success_status]
    if failed:
        raise HTTPException(status_code=500, detail=f"部分浏览器启动失败: {failed}")

    # 3. 执行业务逻辑
    try:
        result = await get_history_live_main(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"业务处理失败: {e}")

    # 4. 返回结果
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return {"code": 200, "status": "success", "data": result.get("data")}


@business_router.post("/live/live_screen/core_data")
async def get_live_screen_core_data(data: LivingCoreDataRequest):
    """
    获取直播间数据
    :param data: {userId:"",roomId:""}
    :return: 直播间大屏数据
    """
    # 确保所有用户浏览器实例已启动
    # 1. 解析 user_id 列表
    payload = data.model_dump()
    print("请求参数:", payload)

    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 设备编号 字段")
    room_id = payload.get("roomId")
    if not room_id:
        raise HTTPException(status_code=400, detail="缺少 直播间编号 字段")

    # 2. 确保所有 user_id 的浏览器实例已存在且唯一
    results = await browser_service.start_browsers([user_id])
    success_status = {"started", "already_running"}
    failed = [r for r in results if r["status"] not in success_status]
    if failed:
        raise HTTPException(status_code=500, detail=f"部分浏览器启动失败: {failed}")

    # 3. 执行业务逻辑
    try:
        result = await get_core_data_main(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"业务处理失败: {e}")

    # 4. 返回结果
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return {"code": 200, "status": "success", "data": result.get("data")}


@business_router.post("/live/eos/data")
async def get_eos_live_data(data: LivingRequest):
    """
    获取EOS直播间数据
    :param user_id: 用户ID
    :return: 直播间数据
    """
    # 确保所有用户浏览器实例已启动
    # 1. 解析 user_id 列表
    payload = data.model_dump()
    print("请求参数:", payload)

    user_ids = payload.get("deviceNoList")
    if not user_ids:
        raise HTTPException(status_code=400, detail="缺少 设备编号 字段")
    # 兼容字符串和列表
    if isinstance(user_ids, str):
        user_ids = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
    if not isinstance(user_ids, list) or not user_ids:
        raise HTTPException(
            status_code=400, detail="deviceNoList/user_ids 格式错误或为空"
        )

    # 2. 确保所有 user_id 的浏览器实例已存在且唯一
    results = await browser_service.start_browsers(user_ids)
    success_status = {"started", "already_running"}
    failed = [r for r in results if r["status"] not in success_status]
    if failed:
        raise HTTPException(status_code=500, detail=f"部分浏览器启动失败: {failed}")

    # 3. 执行业务逻辑
    try:
        result = await get_live_room_list_main(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"业务处理失败: {e}")

    # 4. 返回结果
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return {"code": 200, "status": "success", "data": result.get("data")}



@business_router.post("/live/eos/punish")
async def get_eos_punish_data(data: LivingRequest):
    """
    获取EOS直播间违规数据
    :param user_id: 用户ID
    :return: 直播间数据
    """
    # 确保所有用户浏览器实例已启动
    # 1. 解析 user_id 列表
    payload = data.model_dump()
    print("请求参数:", payload)

    user_ids = payload.get("deviceNoList")
    if not user_ids:
        raise HTTPException(status_code=400, detail="缺少 设备编号 字段")
    # 兼容字符串和列表
    if isinstance(user_ids, str):
        user_ids = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
    if not isinstance(user_ids, list) or not user_ids:
        raise HTTPException(
            status_code=400, detail="deviceNoList/user_ids 格式错误或为空"
        )

    # 2. 确保所有 user_id 的浏览器实例已存在且唯一
    results = await browser_service.start_browsers(user_ids)
    success_status = {"started", "already_running"}
    failed = [r for r in results if r["status"] not in success_status]
    if failed:
        raise HTTPException(status_code=500, detail=f"部分浏览器启动失败: {failed}")

    # 3. 执行业务逻辑
    try:
        result = await get_replay_punish_list_main(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"业务处理失败: {e}")

    # 4. 返回结果
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return {"code": 200, "status": "success", "data": result.get("data")}

