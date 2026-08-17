"""Fetch weather and send one run to all configured recipients."""
import argparse
from datetime import date, datetime

from config import check_config
from love_message import generate_note
from push import send_message
from weather import get_weather


def push_once(mode: str) -> None:
    recipients = check_config()
    weather_by_city = {}
    for recipient in recipients:
        city_id = str(recipient["city_id"])
        if city_id not in weather_by_city:
            print(f"📍 获取 {recipient['city_name']} 天气...")
            weather_by_city[city_id] = get_weather(city_id)
    for recipient in recipients:
        weather = weather_by_city[str(recipient["city_id"])]
        print(f"💌 发送给 {recipient['name']}（{recipient['city_name']}）")
        send_message(recipient, weather, mode, generate_note(recipient, weather, mode))
    print(f"完成：{date.today().isoformat()} {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="家庭天气微信模板推送")
    parser.add_argument("--mode", choices=["morning", "evening"], default="morning")
    push_once(parser.parse_args().mode)
