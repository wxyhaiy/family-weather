"""Optional Gemini weather note; empty API key uses role defaults."""
from config import GEMINI_API_KEY, GEMINI_MODEL


def generate_note(recipient: dict, weather: dict, mode: str) -> str:
    if not GEMINI_API_KEY:
        return ""
    prompt = f"为{recipient['name']}写一句简短中文天气提醒。角色：{recipient['role']}；地点：{recipient['city_name']}；天气：{weather['text']}；温度：{weather['temp_min']}到{weather['temp_max']}摄氏度；时段：{mode}。只输出提醒，不要解释。"
    try:
        from google import genai
        response = genai.Client(api_key=GEMINI_API_KEY).models.generate_content(model=GEMINI_MODEL, contents=prompt, config={"max_output_tokens": 128})
        return response.text.strip()
    except Exception as exc:
        print(f"⚠️ Gemini 失败，使用内置提醒: {exc}")
        return ""
