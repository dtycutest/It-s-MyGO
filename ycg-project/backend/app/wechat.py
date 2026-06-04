"""微信小程序登录服务 —— 调用微信 jscode2session 接口换取 openid 和 session_key。"""

from __future__ import annotations

import httpx

from .config import settings


async def jscode2session(code: str) -> dict:
    """用临时 code 换取微信用户的 openid 和 session_key。

    Returns:
        dict: 微信返回的 JSON，成功时含 openid / session_key / unionid(可选)，
              失败时含 errcode / errmsg。
    """
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()