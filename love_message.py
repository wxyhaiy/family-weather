"""Role-aware Gemini weather briefing with a safe local fallback."""
import re

from config import GEMINI_API_KEY, GEMINI_MODEL

ROLE_PROMPTS = {
    "parent": "对象是父母。语气温暖稳重、事无巨细。重点分析体感温度、早晚温差、AQI、空气质量、紫外线，并给出开窗、穿衣和出行建议。",
    "sibling": "对象是兄弟姐妹。语气像朋友，轻松幽默但实用。重点关注通勤、下班时段降雨、洗车和运动建议。",
    "spouse": "对象是老婆。语气甜蜜浪漫、贴心但自然。重点给出穿衣搭配、防晒护肤、遮阳伞和专属温柔情话。",
    "child": "对象是小孩。语气童趣、鼓励、安全。重点关注户外玩耍、出汗补水减衣、上下学道路和雨天安全。",
}


def _has_rain(weather: dict) -> bool:
    rain_hours = weather.get("rain_hours") or []
    return bool(rain_hours and rain_hours != ["未来12小时暂无明显降雨"])


def _number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fallback(role: str, weather: dict) -> str:
    rain_hours = weather.get("rain_hours") or []
    rain = "、".join(rain_hours[:3])
    temp = weather.get("temp", "--")
    feels = weather.get("feels_like", "--")
    high = weather.get("temp_max", "--")
    low = weather.get("temp_min", "--")
    wind = f"{weather.get('wind_dir', '--')}{weather.get('wind_scale', '--')}级"
    advice = [f"今天{weather.get('text', '天气未知')}，{low}-{high}℃，当前{temp}℃、体感{feels}℃，{wind}。"]

    if _has_rain(weather):
        advice.append(f"预计{rain}，出门带伞，尽量避开降雨较强时段，驾车减速并留意积水。")
    else:
        advice.append("未来12小时暂无明显降雨，出门前仍可再看一次临近预报。")

    high_value = _number(high)
    low_value = _number(low)
    feels_value = _number(feels)
    uv_value = _number(weather.get("uv_index"))
    wind_value = _number(weather.get("wind_scale"))
    if (high_value is not None and high_value >= 30) or (feels_value is not None and feels_value >= 30):
        advice.append("午后体感偏热，穿透气衣物、及时补水，减少长时间户外停留。")
    elif high_value is not None and low_value is not None and high_value - low_value >= 8:
        advice.append("昼夜温差较大，建议分层穿衣，早出晚归备一件薄外套。")
    if uv_value is not None and uv_value >= 5:
        advice.append("紫外线较强，外出涂防晒并使用遮阳用品。")
    if wind_value is not None and wind_value >= 5:
        advice.append("风力较大，远离临时搭建物和易坠物区域，骑行注意侧风。")

    if role == "parent":
        advice.append("早晚出行放慢脚步，随身带水；空气质量不佳时减少开窗和户外活动。")
    elif role == "child":
        advice.append("上下学走人行道，湿滑路面慢走；户外玩耍及时补水，出汗后不要立刻吹冷风。")
    elif role == "spouse":
        advice.append("通勤时注意防晒和补水，空调环境可备薄外套，照顾好自己。")
    else:
        advice.append("通勤预留机动时间，户外运动避开高温和降雨时段，今天不建议洗车。")
    return "".join(advice)


def _usable_note(note: str) -> bool:
    """Reject tool traces, English fragments, and malformed short model output."""
    if not note or len(note) < 12 or len(note) > 500:
        return False
    if re.search(r"[A-Za-z]{3,}", note):
        return False
    if any(marker in note.lower() for marker in ("text talks", "function call", "tool call", "json", "markdown")):
        return False
    return True


def _note_rejection_reason(note: str) -> str:
    if not note:
        return "empty"
    if len(note) < 12:
        return f"too_short:{len(note)}"
    if len(note) > 500:
        return f"too_long:{len(note)}"
    if re.search(r"[A-Za-z]{3,}", note):
        return "contains_english"
    if any(marker in note.lower() for marker in ("text talks", "function call", "tool call", "json", "markdown")):
        return "contains_forbidden_marker"
    return "ok"


def _clean_note(note: str) -> str:
    note = re.sub(r"^[一二三四五六七八九十\s、.。:：-]*(?:父母|孩子|兄弟姐妹|兄弟|专属|角色)?(?:提醒|注意事项|出行提醒)\s*[:：-]?\s*", "", note)
    return note.strip().strip("#*")


def generate_note(recipient: dict, weather: dict, mode: str) -> str:
    if not GEMINI_API_KEY:
        return _fallback(recipient["role"], weather)
    facts = {"姓名": recipient["name"], "角色": recipient["role"], "地点": recipient["city_name"], "天气": weather["text"], "实时温度": weather["temp"], "最低温": weather["temp_min"], "最高温": weather["temp_max"], "体感": weather["feels_like"], "湿度": weather["humidity"], "风向风力": f"{weather['wind_dir']}{weather['wind_scale']}级", "AQI": weather["aqi"], "空气质量": weather["air_category"], "紫外线指数": weather["uv_index"], "穿衣指数": weather.get("dressing_index", "--"), "运动指数": weather.get("sport_index", "--"), "舒适度指数": weather.get("comfort_index", "--"), "未来降雨": "；".join(weather["rain_hours"]), "时段": mode}
    prompt = f"""你是家庭天气 AI 秘书。{ROLE_PROMPTS[recipient['role']]}
天气事实（只能使用这些事实，不要编造）：{facts}
请生成一段 80-180 字的中文注意事项，直接写给{recipient['name']}。必须根据未来降雨的具体时间、气温范围、体感、风力和角色场景给出 2-4 条明确建议；有降雨就指出需要避开的时段和是否带伞，有高温或紫外线就说明补水、防晒或减少户外活动，有大风就提醒交通和户外安全。缺失或为 -- 的数据不要提及。只输出正文，不要出现“孩子提醒”“兄弟提醒”“角色提醒”“注意事项”等标题或前缀，不要 Markdown、JSON 或解释。"""
    try:
        from google import genai
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"temperature": 0.75, "max_output_tokens": 300},
            )
        note = _clean_note((response.text or "").strip())
        if not _usable_note(note):
            print(f"⚠️ Gemini 返回内容不可用，原因={_note_rejection_reason(note)}，长度={len(note)}，使用本地出行建议")
            note = _fallback(recipient["role"], weather)
        return note
    except Exception as exc:
        print(f"⚠️ Gemini 失败，使用本地出行建议: {exc}")
        return _fallback(recipient["role"], weather)
