from typing import Optional, Dict, Any

import requests


class HeadRequester:
    @staticmethod
    def fetch_headers(
            url: str,
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Dict[str, str]] = None,
            timeout: int = 10,
            allow_redirects: bool = True
    ) -> Dict[str, Any]:
        """
        发起 HEAD 请求并返回响应头信息

        :param url: 请求的 URL
        :param headers: 可选的请求头字典
        :param cookies：可选cookies
        :param timeout: 请求超时时间（秒）
        :param allow_redirects: 是否跟随重定向
        :return: 包含状态码和响应头的字典
        """
        try:
            print(f"正在请求: {url}")
            print("请求头:", headers)
            print("Cookies:", cookies)
            response = requests.head(
                url,
                headers=headers or {},
                timeout=timeout,
                cookies=cookies,
                allow_redirects=allow_redirects
            )
            print("[OK] HEAD 请求成功")
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "ok": response.ok,
                "url": response.url
            }
        except requests.RequestException as e:
            return {
                "status_code": None,
                "headers": {},
                "ok": False,
                "error": str(e),
                "url": url
            }
