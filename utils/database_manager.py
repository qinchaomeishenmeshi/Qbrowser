# utils/database_manager.py
# 异步 SQLite 数据库管理器

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import aiosqlite
from datetime import datetime

from utils.common_logger import get_logger
from conf import DATA_DIR

logger = get_logger(__name__)


class DatabaseManager:
    """异步 SQLite 数据库管理器

    统一管理项目中的持久化数据，包括：
    - 用户 Cookies 和 Headers
    - 浏览器端口映射
    - 定时任务配置和结果
    - 应用设置
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path(DATA_DIR) / "app.db"
        else:
            self.db_path = db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None

    async def get_db(self) -> aiosqlite.Connection:
        """获取数据库连接（单例模式）"""
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = aiosqlite.Row
            # 启用 WAL 模式提高并发性能
            await self._conn.execute("PRAGMA journal_mode=WAL")
            await self._init_tables()
        return self._conn

    async def _init_tables(self):
        """初始化数据库表结构"""
        queries = [
            # 1. Cookies 和 Headers 表
            """
            CREATE TABLE IF NOT EXISTS browser_cookies (
                user_id TEXT,
                site_key TEXT,
                cookies_json TEXT,
                headers_json TEXT,
                updated_at DATETIME,
                expires_at DATETIME,
                PRIMARY KEY (user_id, site_key)
            )
            """,
            # 2. 浏览器端口映射表
            """
            CREATE TABLE IF NOT EXISTS browser_ports (
                user_id TEXT PRIMARY KEY,
                port INTEGER,
                updated_at DATETIME
            )
            """,
            # 3. 定时任务配置表
            """
            CREATE TABLE IF NOT EXISTS task_configs (
                task_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                trigger_type TEXT,
                trigger_config_json TEXT,
                target_function TEXT,
                function_params_json TEXT,
                enabled INTEGER DEFAULT 1,
                max_instances INTEGER DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME
            )
            """,
            # 4. 任务执行结果表
            """
            CREATE TABLE IF NOT EXISTS task_results (
                execution_id TEXT PRIMARY KEY,
                task_id TEXT,
                status TEXT,
                start_time DATETIME,
                end_time DATETIME,
                duration REAL,
                result_data_json TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES task_configs(task_id)
            )
            """,
            # 5. 通用键值对存储（替代散乱的 JSON 配置）
            """
            CREATE TABLE IF NOT EXISTS kv_storage (
                key TEXT PRIMARY KEY,
                value_json TEXT,
                updated_at DATETIME
            )
            """,
            # 6. 页面重定向规则表
            """
            CREATE TABLE IF NOT EXISTS redirect_rules (
                name TEXT PRIMARY KEY,
                source_pattern TEXT,
                target_url TEXT,
                condition TEXT,
                enabled INTEGER DEFAULT 1,
                created_at REAL
            )
            """,
        ]

        db = await self.get_db()
        for query in queries:
            await db.execute(query)
        await db.commit()
        logger.info("数据库表结构初始化完成")

    async def close(self):
        """关闭数据库连接"""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("数据库连接已关闭")

    # --- 通用 KV 存储接口 ---
    async def set_value(self, key: str, value: Any):
        """保存通用配置"""
        db = await self.get_db()
        value_json = json.dumps(value, ensure_ascii=False)
        updated_at = datetime.now().isoformat()
        await db.execute(
            "INSERT OR REPLACE INTO kv_storage (key, value_json, updated_at) VALUES (?, ?, ?)",
            (key, value_json, updated_at),
        )
        await db.commit()

    async def get_value(self, key: str, default: Any = None) -> Any:
        """读取通用配置"""
        db = await self.get_db()
        async with db.execute(
            "SELECT value_json FROM kv_storage WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return row[0]
        return default

    async def delete_value(self, key: str):
        """删除通用配置"""
        db = await self.get_db()
        await db.execute("DELETE FROM kv_storage WHERE key = ?", (key,))
        await db.commit()

    # --- 重定向规则管理接口 ---
    async def save_redirect_rule(self, rule_dict: Dict[str, Any]):
        """保存重定向规则"""
        db = await self.get_db()
        await db.execute(
            """
            INSERT OR REPLACE INTO redirect_rules 
            (name, source_pattern, target_url, condition, enabled, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rule_dict["name"],
                rule_dict["source_pattern"],
                rule_dict["target_url"],
                rule_dict.get("condition"),
                1 if rule_dict.get("enabled", True) else 0,
                rule_dict.get("created_at") or datetime.now().timestamp(),
            ),
        )
        await db.commit()

    async def get_all_redirect_rules(self) -> List[Dict[str, Any]]:
        """获取所有重定向规则"""
        db = await self.get_db()
        async with db.execute("SELECT * FROM redirect_rules") as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "name": row["name"],
                    "source_pattern": row["source_pattern"],
                    "target_url": row["target_url"],
                    "condition": row["condition"],
                    "enabled": bool(row["enabled"]),
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    async def delete_redirect_rule(self, name: str):
        """删除重定向规则"""
        db = await self.get_db()
        await db.execute("DELETE FROM redirect_rules WHERE name = ?", (name,))
        await db.commit()

    # --- Cookies 管理接口 ---
    async def save_cookies(
        self,
        user_id: str,
        site_key: str,
        cookies: dict,
        headers: dict = None,
        expires_in_days: int = 3,
    ):
        """保存用户 Cookies"""
        db = await self.get_db()
        now = datetime.now()
        expires_at = (now + sqlite3.timedelta(days=expires_in_days)).isoformat()

        await db.execute(
            """
            INSERT OR REPLACE INTO browser_cookies 
            (user_id, site_key, cookies_json, headers_json, updated_at, expires_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                site_key,
                json.dumps(cookies, ensure_ascii=False),
                json.dumps(headers or {}, ensure_ascii=False),
                now.isoformat(),
                expires_at,
            ),
        )
        await db.commit()

    async def get_cookies_and_headers(
        self, user_id: str, site_key: str
    ) -> Optional[Dict[str, Any]]:
        """同时获取 cookies 和 headers"""
        db = await self.get_db()
        now = datetime.now().isoformat()
        async with db.execute(
            "SELECT cookies_json, headers_json FROM browser_cookies WHERE user_id = ? AND site_key = ? AND expires_at > ?",
            (user_id, site_key, now),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"cookies": json.loads(row[0]), "headers": json.loads(row[1])}
        return None

    async def delete_cookies(self, user_id: str, site_key: str = None):
        """删除用户 Cookies"""
        db = await self.get_db()
        if site_key:
            await db.execute(
                "DELETE FROM browser_cookies WHERE user_id = ? AND site_key = ?",
                (user_id, site_key),
            )
        else:
            await db.execute(
                "DELETE FROM browser_cookies WHERE user_id = ?", (user_id,)
            )
        await db.commit()

    async def get_all_valid_cookies(self, site_key: str = None) -> List[Dict[str, Any]]:
        """获取所有有效的用户 Cookies"""
        db = await self.get_db()
        now = datetime.now().isoformat()
        query = "SELECT user_id, site_key, cookies_json, headers_json FROM browser_cookies WHERE expires_at > ?"
        params = [now]
        if site_key:
            query += " AND site_key = ?"
            params.append(site_key)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "user_id": row[0],
                    "site_key": row[1],
                    "cookies": json.loads(row[2]),
                    "headers": json.loads(row[3]),
                }
                for row in rows
            ]

    # --- 端口管理接口 ---
    async def save_port(self, user_id: str, port: int):
        """保存端口映射"""
        db = await self.get_db()
        await db.execute(
            "INSERT OR REPLACE INTO browser_ports (user_id, port, updated_at) VALUES (?, ?, ?)",
            (user_id, port, datetime.now().isoformat()),
        )
        await db.commit()

    async def get_all_ports(self) -> Dict[str, int]:
        """获取所有端口映射"""
        db = await self.get_db()
        async with db.execute("SELECT user_id, port FROM browser_ports") as cursor:
            rows = await cursor.fetchall()
            return {row["user_id"]: row["port"] for row in rows}

    async def delete_port(self, user_id: str):
        """删除端口映射"""
        db = await self.get_db()
        await db.execute("DELETE FROM browser_ports WHERE user_id = ?", (user_id,))
        await db.commit()

    async def clear_all_ports(self):
        """清空所有端口映射"""
        db = await self.get_db()
        await db.execute("DELETE FROM browser_ports")
        await db.commit()


# 全局单例
db_manager = DatabaseManager()
