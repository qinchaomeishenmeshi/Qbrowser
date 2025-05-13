import requests


def fetch_jinritemai_csrf_headers():
    url = "https://buyin.jinritemai.com/selection/common/btm_mapping"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/15.0 Mobile/15E148 Safari/604.1 Chrome/135.0.0.0"
        ),
        "x-secsdk-csrf-request": "0"
    }

    try:
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)

        print("✅ HEAD 请求成功")
        print("状态码:", response.status_code)
        print("响应头:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies": response.cookies.get_dict()
        }

    except requests.RequestException as e:
        print("❌ 请求失败:", e)
        return {
            "status_code": None,
            "headers": {},
            "cookies": {},
            "error": str(e)
        }


# 示例调用
if __name__ == "__main__":
    fetch_jinritemai_csrf_headers()
