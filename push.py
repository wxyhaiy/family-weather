"""Send role-specific template messages through WeChat directly."""
import json
from datetime import datetime

import requests

from config import APP_ID, APP_SECRET, TEMPLATE_ID, USER_IDS_RAW

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"


def _access_token() -> str:
    response = requests.get(TOKEN_URL, params={"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET}, timeout=15)
    response.raise_for_status()
    result = response.json()
    if result.get("errcode"):
        raise RuntimeError(f"微信 access_token 失败: {result}")
    return result["access_token"]


def _default_note(role: str) -> str:
    return {"parent": "早晚注意增减衣物，外出注意防滑和安全。", "child": "出门记得带好水和雨具，注意交通安全。", "spouse": "今天也要照顾好自己，外出记得做好防护。", "sibling": "出门注意天气变化，愿你今天顺利平安。"}.get(role, "请根据天气变化增减衣物，外出做好防护。")


def _template_data(recipient: dict, weather: dict, mode: str, note: str) -> dict:
    greeting = "早安" if mode == "morning" else "晚安"
    return {
        "first": {"value": f"{greeting}，{recipient['name']}，今日天气提醒"},
        "date": {"value": datetime.now().strftime("%Y年%m月%d日")},
        "name": {"value": recipient["name"]},
        "city": {"value": recipient["city_name"]},
        "weather": {"value": f"{weather['emoji']} {weather['text']}"},
        "min_temperature": {"value": str(weather.get("temp_min", "--"))},
        "max_temperature": {"value": str(weather.get("temp_max", "--"))},
        "wind_direction": {"value": f"{weather.get('wind_dir', '--')}{weather.get('wind_scale', '--')}级"},
        "note": {"value": note or _default_note(recipient["role"])},
        "remark": {"value": "愿家人今天平安顺利。"},
    }


def send_message(recipient: dict, weather: dict, mode: str, note: str = "") -> None:
    user_ids = json.loads(USER_IDS_RAW)
    payload = {"touser": user_ids[recipient["key"]], "template_id": TEMPLATE_ID, "data": _template_data(recipient, weather, mode, note)}
    response = requests.post(SEND_URL, params={"access_token": _access_token()}, json=payload, timeout=15)
    response.raise_for_status()
    result = response.json()
    if result.get("errcode") != 0:
        raise RuntimeError(f"微信模板消息失败（{recipient['key']}）: {result}")
    print(f"✅ 已发送给 {recipient['name']}")
