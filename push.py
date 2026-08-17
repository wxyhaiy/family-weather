"""Send role-specific template messages through WeChat directly."""
import json
from urllib.parse import quote

import requests

from config import APP_ID, APP_SECRET, TEMPLATE_ID, USER_IDS_RAW
from time_utils import now_shanghai

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"
DETAIL_PAGE_BASE_URL = "https://wxyhaiy.github.io/family-weather/"


def _access_token() -> str:
    response = requests.get(TOKEN_URL, params={"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET}, timeout=15)
    response.raise_for_status()
    result = response.json()
    if result.get("errcode"):
        raise RuntimeError(f"微信 access_token 失败: {result}")
    return result["access_token"]


def _default_note(role: str) -> str:
    return {
        "parent": "早晚注意增减衣物，外出注意防滑和安全。",
        "child": "孩子提醒：出门带好水和雨具，上下学走人行道，遇到湿滑路面慢慢走。",
        "spouse": "今天也要照顾好自己，外出记得做好防护。",
        "sibling": "出行提醒：外出前查看降雨，建议带伞，通勤路上注意安全。",
    }.get(role, "请根据天气变化增减衣物，外出做好防护。")


def _travel_note(weather: dict) -> str:
    rain = "、".join(weather.get("rain_hours", [])[:2])
    return f"{rain}；" if rain else "暂时没有明显降雨；"


def _child_note(weather: dict) -> str:
    rain = "有降雨时带好雨具，" if weather.get("rain_hours") and weather["rain_hours"] != ["未来12小时暂无明显降雨"] else ""
    return f"{rain}上下学走人行道，遇到湿滑路面慢慢走，记得喝水，玩耍时注意安全。"


def _guaranteed_travel_note(weather: dict) -> str:
    """Build a non-empty message for the template's note field."""
    rain_hours = weather.get("rain_hours") or []
    rain = "、".join(rain_hours[:3]) if rain_hours and rain_hours != ["未来12小时暂无明显降雨"] else "未来12小时暂无明显降雨"
    return (
        f"当前{weather.get('temp', '--')}℃，体感{weather.get('feels_like', '--')}℃，"
        f"今日{weather.get('temp_min', '--')}-{weather.get('temp_max', '--')}℃，"
        f"{weather.get('wind_dir', '--')}{weather.get('wind_scale', '--')}级；"
        f"{rain}。外出前查看临近预报，建议携带雨具，通勤和驾车注意路面安全。"
    )


def _template_data(recipient: dict, weather: dict, mode: str, note: str) -> dict:
    greeting = "早安" if mode == "morning" else "晚安"
    role = recipient["role"]
    travel = note.strip() if isinstance(note, str) else ""
    if not travel:
        travel = _guaranteed_travel_note(weather)
        print("出行提醒为空，已使用发送前兜底")
    child = _child_note(weather)
    return {
        "first": {"value": f"{greeting}，{recipient['name']}，今日天气提醒"},
        "date": {"value": now_shanghai().strftime("%Y年%m月%d日")},
        "name": {"value": recipient["name"]},
        "city": {"value": recipient["city_name"]},
        "weather": {"value": f"{weather['emoji']} {weather['text']}"},
        "min_temperature": {"value": str(weather.get("temp_min", "--"))},
        "max_temperature": {"value": str(weather.get("temp_max", "--"))},
        "wind_direction": {"value": f"{weather.get('wind_dir', '--')}{weather.get('wind_scale', '--')}级"},
        # The current WeChat template displays {{note.DATA}} as 出行提醒.
        "note": {"value": travel},
        # Keep both template fields populated so existing and newer templates show the same advice.
        "travel": {"value": travel},
        "child": {"value": child if role == "child" else ""},
        "remark": {"value": note or "愿家人今天平安顺利。"},
    }


def _detail_url(recipient: dict, weather: dict, mode: str, note: str) -> str:
    detail = {"recipient": recipient, "weather": weather, "mode": mode, "travel": note, "note": note}
    encoded = quote(json.dumps(detail, ensure_ascii=False, separators=(",", ":")))
    return f"{DETAIL_PAGE_BASE_URL}?data={encoded}"


def send_message(recipient: dict, weather: dict, mode: str, note: str = "") -> None:
    user_ids = json.loads(USER_IDS_RAW)
    open_id = str(user_ids.get(recipient["key"], "")).strip()
    if not open_id:
        print(f"跳过 {recipient['name']}：OpenID 为空")
        return
    template_data = _template_data(recipient, weather, mode, note)
    payload = {"touser": open_id, "template_id": TEMPLATE_ID, "url": _detail_url(recipient, weather, mode, note), "data": template_data}
    print(f"   模板出行提醒长度：{len(template_data['note']['value'])}")
    response = requests.post(SEND_URL, params={"access_token": _access_token()}, json=payload, timeout=15)
    response.raise_for_status()
    result = response.json()
    if result.get("errcode") != 0:
        raise RuntimeError(f"微信模板消息失败（{recipient['key']}）: {result}")
    print(f"✅ 已发送给 {recipient['name']}")
