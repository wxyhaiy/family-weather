"""Load all personal settings from environment variables."""
import json
import os

from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID", "")
APP_SECRET = os.getenv("APP_SECRET", "")
TEMPLATE_IDS = {
    "parent": os.getenv("TEMPLATE_ID_PARENT", ""),
    "child": os.getenv("TEMPLATE_ID_CHILD", ""),
    "spouse": os.getenv("TEMPLATE_ID_SPOUSE", ""),
    "sibling": os.getenv("TEMPLATE_ID_SIBLING", ""),
}
USER_IDS_RAW = os.getenv("USER_IDS", "")
RECIPIENTS_RAW = os.getenv("RECIPIENTS_JSON", "")
QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY", "")
QWEATHER_API_HOST = os.getenv("QWEATHER_API_HOST", "https://devapi.qweather.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _json_object(raw: str, name: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} 必须是合法 JSON 对象") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name} 必须是 JSON 对象")
    return value


def check_config() -> list[dict]:
    errors = []
    for name, value in (("APP_ID", APP_ID), ("APP_SECRET", APP_SECRET), ("USER_IDS", USER_IDS_RAW), ("RECIPIENTS_JSON", RECIPIENTS_RAW), ("QWEATHER_API_KEY", QWEATHER_API_KEY)):
        if not value:
            errors.append(name)
    for role, template_id in TEMPLATE_IDS.items():
        if not template_id:
            errors.append(f"TEMPLATE_ID_{role.upper()}")
    try:
        recipients = _json_object(RECIPIENTS_RAW, "RECIPIENTS_JSON").get("recipients", [])
        user_ids = _json_object(USER_IDS_RAW, "USER_IDS")
    except ValueError as exc:
        errors.append(str(exc))
        recipients, user_ids = [], {}
    if not isinstance(recipients, list) or not recipients:
        errors.append("RECIPIENTS_JSON.recipients 必须是非空数组")
        recipients = []
    for item in recipients:
        for field in ("key", "name", "city_id", "city_name", "role"):
            if not item.get(field):
                errors.append(f"RECIPIENTS_JSON 缺少 {field}")
        if item.get("role") not in TEMPLATE_IDS:
            errors.append(f"无效角色: {item.get('role')}")
        if item.get("key") not in user_ids:
            errors.append(f"USER_IDS 缺少: {item.get('key')}")
    if errors:
        raise ValueError("配置不完整：" + "; ".join(dict.fromkeys(errors)))
    print(f"✅ 配置加载成功，收件人 {len(recipients)} 人")
    return recipients
