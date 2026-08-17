"""QWeather data needed for role-specific AI weather briefings."""
import time
from functools import lru_cache

import jwt
import requests

from config import (
    QWEATHER_API_HOST,
    QWEATHER_API_KEY,
    QWEATHER_KEY_ID,
    QWEATHER_PRIVATE_KEY,
    QWEATHER_PROJECT_ID,
)

EMOJI = {"晴": "☀️", "多云": "⛅", "阴": "☁️", "小雨": "🌧️", "中雨": "🌧️", "大雨": "🌧️", "暴雨": "🌊", "阵雨": "🌦️", "雷阵雨": "⛈️", "小雪": "❄️", "雾": "🌫️", "霾": "😷"}


def _get(path: str, city_id: str, extra_params: dict | None = None) -> dict:
    params = {"location": city_id, "key": QWEATHER_API_KEY}
    if extra_params:
        params.update(extra_params)
    response = requests.get(f"{QWEATHER_API_HOST.rstrip('/')}/v7/{path}", params=params, timeout=15)
    response.raise_for_status()
    result = response.json()
    if result.get("code") != "200":
        raise RuntimeError(f"和风天气 {path} code={result.get('code')}")
    return result


@lru_cache(maxsize=1)
def _qweather_jwt() -> str:
    """Sign a short-lived QWeather JWT from the project's private key."""
    now = int(time.time())
    payload = {"sub": QWEATHER_PROJECT_ID, "iat": now - 30, "exp": now + 23 * 60 * 60}
    headers = {"alg": "EdDSA", "kid": QWEATHER_KEY_ID}
    return jwt.encode(payload, QWEATHER_PRIVATE_KEY, algorithm="EdDSA", headers=headers)


def _get_air_quality(recipient: dict) -> dict:
    latitude = recipient.get("latitude")
    longitude = recipient.get("longitude")
    if latitude in (None, "") or longitude in (None, ""):
        print(f"   空气质量跳过：{recipient.get('name', '收件人')} 未配置坐标")
        return {}
    if not all((QWEATHER_PROJECT_ID, QWEATHER_KEY_ID, QWEATHER_PRIVATE_KEY)):
        print("   空气质量跳过：未配置 QWEATHER_PROJECT_ID、QWEATHER_KEY_ID 或 QWEATHER_PRIVATE_KEY")
        return {}
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        print(f"   空气质量跳过：{recipient.get('name', '收件人')} 坐标不是数字")
        return {}
    url = f"{QWEATHER_API_HOST.rstrip('/')}/airquality/v1/current/{latitude}/{longitude}"
    response = requests.get(url, headers={"Authorization": f"Bearer {_qweather_jwt()}"}, timeout=15)
    response.raise_for_status()
    return response.json()


def get_weather(city_id: str, recipient: dict | None = None) -> dict:
    now = _get("weather/now", city_id)["now"]
    daily = _get("weather/3d", city_id).get("daily", [{}])[0]
    hourly = _get("weather/24h", city_id).get("hourly", [])
    indices = {}
    try:
        index_items = _get("indices/1d", city_id, {"type": "1,3,5,9"}).get("daily", [])
        indices = {str(item.get("type")): item for item in index_items}
    except Exception as exc:
        print(f"   生活指数获取失败，AI 将忽略生活指数: {exc}")
    aqi = {}
    try:
        aqi = _get_air_quality(recipient or {})
    except Exception as exc:
        print(f"   ⚠️ AQI 获取失败，AI 将忽略 AQI: {exc}")
    uv = indices.get("5", {}).get("level", "--")
    rain_hours = [f"{item.get('fxTime', '')[11:16]} {item.get('text', '')} {item.get('pop', '')}%" for item in hourly[:12] if int(item.get("pop", 0) or 0) >= 30]
    text = now.get("text", "未知")
    return {
        "text": text, "emoji": EMOJI.get(text, "🌈"), "temp": now.get("temp", "--"),
        "temp_min": daily.get("tempMin", "--"), "temp_max": daily.get("tempMax", "--"),
        "feels_like": now.get("feelsLike", "--"), "humidity": now.get("humidity", "--"),
        "wind_dir": now.get("windDir", "--"), "wind_scale": now.get("windScale", "--"),
        "uv_index": uv, "aqi": aqi.get("aqi", "--"), "air_category": aqi.get("category", aqi.get("level", "未知")),
        "dressing_index": indices.get("1", {}).get("text", "--"),
        "sport_index": indices.get("3", {}).get("text", "--"),
        "comfort_index": indices.get("9", {}).get("text", "--"),
        "rain_hours": rain_hours or ["未来12小时暂无明显降雨"], "sunrise": daily.get("sunrise", "--"), "sunset": daily.get("sunset", "--"),
    }
