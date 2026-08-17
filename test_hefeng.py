import os
import requests

def test_qweather_custom_host():
    print("\n=== 测试和风天气 (专属 API Host) ===")
    key = os.getenv("QWEATHER_API_KEY")
    host = os.getenv("QWEATHER_API_HOST")
    if not key or not host:
        raise RuntimeError("请先设置 QWEATHER_API_KEY 和 QWEATHER_API_HOST 环境变量")
    
    # 重点在这里：把 devapi.qweather.com 换成你的专属 apihost
    url = f"{host.rstrip('/')}/v7/weather/now"
    
    headers = {"X-QW-Api-Key": key}
    params = {"location": "101010100"} # 101010100 是北京的城市代码，你可以换成目标城市
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"  Status: {r.status_code}")
        
        # 将返回的 JSON 字符串解析为字典并美化打印
        import json
        print(f"  Response:\n{json.dumps(r.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"  ERROR: {e}")

test_qweather_custom_host()
