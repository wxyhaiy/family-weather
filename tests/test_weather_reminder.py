import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import love_message
import push
import time_utils


WEATHER = {
    "emoji": "☁️",
    "text": "阴",
    "temp": "27",
    "temp_min": "25",
    "temp_max": "31",
    "feels_like": "29",
    "humidity": "89",
    "wind_dir": "东北风",
    "wind_scale": "2",
    "uv_index": "2",
    "rain_hours": ["06:00 阴 51%", "08:00 雷阵雨 70%"],
}
RECIPIENT = {"name": "兄弟姐妹", "city_name": "深圳南山区", "role": "sibling"}


class WeatherReminderTests(unittest.TestCase):
    def test_travel_is_populated_for_every_role(self):
        for role in ("parent", "child", "spouse", "sibling"):
            recipient = {**RECIPIENT, "role": role}
            data = push._template_data(recipient, WEATHER, "morning", "详细天气出行建议")
            self.assertEqual(data["travel"]["value"], "详细天气出行建议")
            self.assertEqual(data["note"]["value"], "详细天气出行建议")

    def test_fallback_uses_weather_details(self):
        advice = love_message._fallback("sibling", WEATHER)
        self.assertIn("08:00 雷阵雨 70%", advice)
        self.assertIn("25-31℃", advice)
        self.assertIn("东北风2级", advice)
        self.assertIn("通勤", advice)

    def test_message_date_uses_utc_plus_eight(self):
        fixed_utc = datetime(2026, 8, 17, 17, 30, tzinfo=timezone.utc)
        with patch.object(time_utils, "datetime", wraps=datetime) as mocked_datetime:
            mocked_datetime.now.return_value = fixed_utc.astimezone(time_utils.SHANGHAI_TZ)
            self.assertEqual(time_utils.now_shanghai().strftime("%Y年%m月%d日"), "2026年08月18日")

        with patch.object(push, "now_shanghai", return_value=fixed_utc.astimezone(time_utils.SHANGHAI_TZ)):
            data = push._template_data(RECIPIENT, WEATHER, "morning", "建议")
            self.assertEqual(data["date"]["value"], "2026年08月18日")


if __name__ == "__main__":
    unittest.main()
