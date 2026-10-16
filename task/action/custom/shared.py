from urllib.parse import quote
from conf.config import settings
from infrastructure import http_client


def _base_url() -> str:
    return settings.COMMERCE_API_BASE_URL.rstrip("/")


def _extract_data(result: dict | None) -> dict | None:
    data = result.get("data") if isinstance(result, dict) else None
    return data if isinstance(data, dict) else None

# 1.获取订单信息"
async def fetch_order(order_id: str) -> dict | None:
    """获取订单信息"""
    try:
        # 注意此处：
        # 文件头部 from atguigu.infrastructure import http_client
        # 此处使用 http_client.http_client.get(url) 调用

        # 不要这样做：
        # 文件头部 from atguigu.infrastructure.http_client import http_client
        # 此处使用 http_client.get(url) 调用
        # 会使拿到的 http_client 是 None
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id, safe='')}")
        return _extract_data(r.json())
    except Exception:
        return None

# 2.获取物流信息
async def fetch_logistics(order_id: str) -> dict | None:
    """获取物流信息"""
    try:
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id, safe='')}/logistics")
        return _extract_data(r.json())
    except Exception:
        return None

# 3.获取推荐商品信息
async def fetch_product(product_id: str) -> dict | None:
    """获取推荐商品信息"""
    try:
        r = await http_client.http_client.get(f"{_base_url()}/products/{quote(product_id, safe='')}")
        return _extract_data(r.json())
    except Exception:
        return None

if __name__ == '__main__':

    # HTTP URL 里面不能直接放中文、空格、# & : = 等字符，必须编码。
    s = "你好 python & test 2026/09/08"
    # 默认safe="/"，斜杠保留，不编码
    # safe="" 所有特殊字符全部编码
    res = quote(s, safe='')
    print(res)
    # %E4%BD%A0%E5%A5%BD%20python%20%26%20test