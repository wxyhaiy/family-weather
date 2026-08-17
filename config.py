"""Load all personal settings from environment variables."""
import json
import os

from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID", "")
APP_SECRET = os.getenv("APP_SECRET", "")
TEMPLATE_ID = os.getenv("TEMPLATE_ID", "")
USER_IDS_RAW = os.getenv("USER_IDS", "")
RECIPIENTS_RAW = os.getenv("RECIPIENTS_JSON", "")
QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY", "")
QWEATHER_API_HOST = os.getenv("QWEATHER_API_HOST", "https://devapi.qweather.com")
QWEATHER_JWT = os.getenv("QWEATHER_JWT", "")
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
    for name, value in (("APP_ID", APP_ID), ("APP_SECRET", APP_SECRET), ("RECIPIENTS_JSON", RECIPIENTS_RAW), ("QWEATHER_API_KEY", QWEATHER_API_KEY)):
        if not value:
            errors.append(name)
    if not TEMPLATE_ID:
        errors.append("TEMPLATE_ID")
    try:
        recipients_value = json.loads(RECIPIENTS_RAW)
        if isinstance(recipients_value, dict):
            recipients = recipients_value.get("recipients", [])
        elif isinstance(recipients_value, list):
            recipients = recipients_value
        else:
            recipients = []
            raise ValueError("RECIPIENTS_JSON 必须是对象或数组")
        user_ids = _json_object(USER_IDS_RAW, "USER_IDS") if USER_IDS_RAW.strip() else {}
    except ValueError as exc:
        errors.append(str(exc))
        recipients, user_ids = [], {}
    if not isinstance(recipients, list) or not recipients:
        errors.append("RECIPIENTS_JSON.recipients 必须是非空数组")
        recipients = []
    active_recipients = []
    skipped_recipients = []
    for item in recipients:
        for field in ("key", "name", "city_id", "city_name", "role"):
            if not item.get(field):
                errors.append(f"RECIPIENTS_JSON 缺少 {field}")
        if item.get("role") not in {"parent", "child", "spouse", "sibling"}:
            errors.append(f"无效角色: {item.get('role')}")
        open_id = str(user_ids.get(item.get("key", ""), "")).strip()
        if open_id:
            active_recipients.append(item)
        else:
            skipped_recipients.append(item.get("name") or item.get("key") or "未命名收件人")
    if errors:
        raise ValueError("配置不完整：" + "; ".join(dict.fromkeys(errors)))
    if skipped_recipients:
        print(f"跳过 OpenID 为空的收件人：{'、'.join(skipped_recipients)}")
    print(f"配置加载成功，实际发送 {len(active_recipients)} 人")
    return active_recipients
