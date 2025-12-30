#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面重定向API接口
提供基于Playwright的浏览器页面重定向功能
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from utils.page_redirect_manager import redirect_manager, RedirectRule
from browser.playwright_operator import playwright_operator
from utils.common_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["页面重定向"])


class RedirectRequest(BaseModel):
    """重定向请求模型"""

    user_id: str
    target_url: str
    wait_time: float = 1.0


class BatchRedirectRequest(BaseModel):
    """批量重定向请求模型"""

    redirects: List[Dict[str, str]]  # [{"user_id": "xxx", "target_url": "xxx"}, ...]
    wait_time: float = 1.0


class RedirectRuleRequest(BaseModel):
    """重定向规则请求模型"""

    name: str
    source_pattern: str
    target_url: str
    condition: Optional[str] = None
    enabled: bool = True


class ApplyRuleRequest(BaseModel):
    """应用规则请求模型"""

    user_id: str
    rule_name: str
    wait_time: float = 1.0


@router.post("/redirect/single", summary="单页面重定向")
async def redirect_single_page(request: RedirectRequest):
    """重定向单个页面到指定URL"""
    try:
        success = await playwright_operator.redirect_user_page(
            request.user_id, request.target_url, request.wait_time
        )

        return {
            "success": success,
            "user_id": request.user_id,
            "target_url": request.target_url,
            "message": "重定向成功" if success else "重定向失败(可能是浏览器未启动)",
        }

    except Exception as e:
        logger.error(f"单页面重定向失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重定向失败: {str(e)}")


@router.post("/redirect/batch", summary="批量重定向")
async def redirect_batch_pages(request: BatchRedirectRequest):
    """批量重定向多个页面"""
    try:
        results = await playwright_operator.batch_redirect_users(
            request.redirects, request.wait_time
        )

        success_count = sum(1 for success in results.values() if success)
        total_count = len(request.redirects)

        return {
            "success": success_count > 0,
            "total_count": total_count,
            "success_count": success_count,
            "failed_count": total_count - success_count,
            "results": results,
            "message": f"批量重定向完成，成功: {success_count}/{total_count}",
        }

    except Exception as e:
        logger.error(f"批量重定向失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量重定向失败: {str(e)}")


@router.post("/redirect/rules", summary="添加重定向规则")
async def add_redirect_rule(request: RedirectRuleRequest):
    """添加重定向规则"""
    try:
        rule = RedirectRule(
            name=request.name,
            source_pattern=request.source_pattern,
            target_url=request.target_url,
            condition=request.condition,
            enabled=request.enabled,
        )

        success = await redirect_manager.add_rule(rule)

        return {
            "success": success,
            "rule_name": request.name,
            "message": "规则添加成功" if success else "规则添加失败",
        }

    except Exception as e:
        logger.error(f"添加重定向规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加规则失败: {str(e)}")


@router.get("/redirect/rules", summary="获取所有重定向规则")
async def get_redirect_rules():
    """获取所有重定向规则"""
    try:
        rules = await redirect_manager.list_rules()

        return {
            "success": True,
            "total_count": len(rules),
            "rules": [
                {
                    "name": rule.name,
                    "source_pattern": rule.source_pattern,
                    "target_url": rule.target_url,
                    "condition": rule.condition,
                    "enabled": rule.enabled,
                    "created_at": rule.created_at,
                }
                for rule in rules
            ],
            "message": f"获取到 {len(rules)} 条规则",
        }

    except Exception as e:
        logger.error(f"获取重定向规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取规则失败: {str(e)}")


@router.get("/redirect/rules/{rule_name}", summary="获取指定重定向规则")
async def get_redirect_rule(rule_name: str):
    """获取指定重定向规则"""
    try:
        rule = await redirect_manager.get_rule(rule_name)

        if not rule:
            raise HTTPException(status_code=404, detail=f"规则 {rule_name} 不存在")

        return {
            "success": True,
            "rule": {
                "name": rule.name,
                "source_pattern": rule.source_pattern,
                "target_url": rule.target_url,
                "condition": rule.condition,
                "enabled": rule.enabled,
                "created_at": rule.created_at,
            },
            "message": "规则获取成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取重定向规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取规则失败: {str(e)}")


@router.delete("/redirect/rules/{rule_name}", summary="删除重定向规则")
async def delete_redirect_rule(rule_name: str):
    """删除重定向规则"""
    try:
        success = await redirect_manager.remove_rule(rule_name)

        if not success:
            raise HTTPException(status_code=404, detail=f"规则 {rule_name} 不存在")

        return {"success": success, "rule_name": rule_name, "message": "规则删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除重定向规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除规则失败: {str(e)}")


@router.post("/redirect/apply-rule", summary="应用重定向规则")
async def apply_redirect_rule(request: ApplyRuleRequest):
    """应用重定向规则到指定页面"""
    try:
        success = await playwright_operator.apply_redirect_rule_to_user(
            request.user_id, request.rule_name, request.wait_time
        )

        return {
            "success": success,
            "user_id": request.user_id,
            "rule_name": request.rule_name,
            "message": "规则应用成功" if success else "规则应用失败",
        }

    except Exception as e:
        logger.error(f"应用重定向规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"应用规则失败: {str(e)}")


@router.get("/redirect/stats", summary="获取重定向统计信息")
async def get_redirect_stats():
    """获取重定向管理器统计信息"""
    try:
        stats = await redirect_manager.get_stats()

        return {"success": True, "stats": stats, "message": "统计信息获取成功"}

    except Exception as e:
        logger.error(f"获取重定向统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
