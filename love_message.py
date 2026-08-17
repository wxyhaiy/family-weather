"""Role-aware Gemini weather briefing with a safe local fallback."""
from config import GEMINI_API_KEY, GEMINI_MODEL

ROLE_PROMPTS = {
    "parent": "对象是父母。语气温暖稳重、事无巨细。重点分析体感温度、早晚温差、AQI、空气质量、紫外线，并给出开窗、穿衣和出行建议。",
    "sibling": "对象是兄弟姐妹。语气像朋友，轻松幽默但实用。重点关注通勤、下班时段降雨、洗车和运动建议。",
    "spouse": "对象是老婆。语气甜蜜浪漫、贴心但自然。重点给出穿衣搭配、防晒护肤、遮阳伞和专属温柔情话。",
    "child": "对象是小孩。语气童趣、鼓励、安全。重点关注户外玩耍、出汗补水减衣、上下学道路和雨天安全。",
}

ROLE_LABELS = {"parent": "父母提醒", "child": "孩子提醒", "spouse": "专属提醒", "sibling": "兄弟姐妹提醒"}


def _fallback(role: str, weather: dict) -> str:
    if role == "parent":
        return f"体感 {weather.get('feels_like', '--')}℃，早晚注意增减衣物；空气质量{weather.get('air_category', '未知')}，外出注意防护。"
    if role == "sibling":
        return f"今天{weather['text']}，未来一段时间：{'、'.join(weather.get('rain_hours', [])[:2])}，出门记得看天气。"
    if role == "spouse":
        return f"今天最高 {weather.get('temp_max', '--')}℃，出门记得做好防晒，带上伞，愿你漂亮又舒心。"
    return f"今天是{weather['text']}，出门记得带水，走路看路，开心玩耍也要注意安全。"


def generate_note(recipient: dict, weather: dict, mode: str) -> str:
    if not GEMINI_API_KEY:
        return f"{ROLE_LABELS.get(recipient['role'], '天气提醒')}：{_fallback(recipient['role'], weather)}"
    facts = {"姓名": recipient["name"], "角色": recipient["role"], "地点": recipient["city_name"], "天气": weather["text"], "实时温度": weather["temp"], "最低温": weather["temp_min"], "最高温": weather["temp_max"], "体感": weather["feels_like"], "湿度": weather["humidity"], "风向风力": f"{weather['wind_dir']}{weather['wind_scale']}级", "AQI": weather["aqi"], "空气质量": weather["air_category"], "紫外线指数": weather["uv_index"], "穿衣指数": weather.get("dressing_index", "--"), "运动指数": weather.get("sport_index", "--"), "舒适度指数": weather.get("comfort_index", "--"), "未来降雨": "；".join(weather["rain_hours"]), "时段": mode}
    prompt = f"""你是家庭天气 AI 秘书。{ROLE_PROMPTS[recipient['role']]}
天气事实（只能使用这些事实，不要编造）：{facts}
请生成一段 80-180 字的中文专属天气通报，直接写给{recipient['name']}。必须具体、自然、有行动建议。缺失或为 -- 的数据不要提及。不要使用 Markdown、标题、JSON 或解释。"""
    try:
        from google import genai
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"temperature": 0.75, "max_output_tokens": 300},
            )
        note = (response.text or "").strip() or _fallback(recipient["role"], weather)
        return f"{ROLE_LABELS.get(recipient['role'], '天气提醒')}：{note}"
    except Exception as exc:
        print(f"⚠️ Gemini 失败，使用本地角色提醒: {exc}")
        return f"{ROLE_LABELS.get(recipient['role'], '天气提醒')}：{_fallback(recipient['role'], weather)}"
