import urllib.request
import json
import sys

base_url = "http://127.0.0.1:5000"
endpoints = [
    "/",
    "/get_logs", 
    "/test_data?symbol=XAUUSD",
    "/get_config"
]

for endpoint in endpoints:
    url = base_url + endpoint
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        print(f"[OK] {endpoint}: HTTP {response.status}")
        if endpoint == "/":
            html = response.read().decode()[:100]
            print(f"  Preview: {html}...")
        elif endpoint == "/test_data?symbol=XAUUSD":
            data = json.loads(response.read().decode())
            print(f"  MT5 Connected: {data.get('mt5_connected')}")
            print(f"  Indicators: {len(data.get('indicators_calculated', {}))}")
    except Exception as e:
        print(f"[FAIL] {endpoint}: {e}")

print("\nFlask server appears to be running correctly.")