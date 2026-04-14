"""
api/flights.py — 查詢單一航線真實票價
GET /api/flights?dest=CNX&dep=2026-05-01&ret=2026-05-06
"""
import os, json, requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

ROUTES = {
    # 原有熱門航線
    "TYO": {"name": "東京",   "arrival_id": "TYO", "avg": 9800,  "emoji": "🗼"},
    "OSA": {"name": "大阪",   "arrival_id": "KIX", "avg": 8200,  "emoji": "🏯"},
    "SEL": {"name": "首爾",   "arrival_id": "ICN", "avg": 7500,  "emoji": "🇰🇷"},
    "BKK": {"name": "曼谷",   "arrival_id": "BKK", "avg": 8900,  "emoji": "🛕"},
    "SIN": {"name": "新加坡", "arrival_id": "SIN", "avg": 10500, "emoji": "🦁"},
    "HKG": {"name": "香港",   "arrival_id": "HKG", "avg": 5200,  "emoji": "🌃"},
    "KUL": {"name": "吉隆坡", "arrival_id": "KUL", "avg": 9000,  "emoji": "🏙️"},
    "MNL": {"name": "馬尼拉", "arrival_id": "MNL", "avg": 6200,  "emoji": "🌺"},
    "SGN": {"name": "胡志明", "arrival_id": "SGN", "avg": 8100,  "emoji": "🛵"},
    # 新增熱門小機場
    "CNX": {"name": "清邁",   "arrival_id": "CNX", "avg": 9500,  "emoji": "🌸"},
    "HKT": {"name": "普吉島", "arrival_id": "HKT", "avg": 10500, "emoji": "🏖️"},
    "DPS": {"name": "峇里島", "arrival_id": "DPS", "avg": 12000, "emoji": "🌴"},
    "DAD": {"name": "峴港",   "arrival_id": "DAD", "avg": 8500,  "emoji": "🌊"},
    "HAN": {"name": "河內",   "arrival_id": "HAN", "avg": 7800,  "emoji": "🏛️"},
    "CEB": {"name": "宿霧",   "arrival_id": "CEB", "avg": 7200,  "emoji": "🐠"},
    "RGN": {"name": "仰光",   "arrival_id": "RGN", "avg": 11000, "emoji": "🙏"},
}

def fetch_flights(dest_code, dep_date, ret_date):
    if dest_code not in ROUTES:
        return {"error": "無效的目的地代碼"}
    if not SERPAPI_KEY:
        return {"error": "未設定 SERPAPI_KEY"}
    info = ROUTES[dest_code]
    params = {
        "engine": "google_flights", "departure_id": "TPE",
        "arrival_id": info["arrival_id"], "outbound_date": dep_date,
        "return_date": ret_date, "currency": "TWD", "hl": "zh-tw",
        "type": "1", "api_key": SERPAPI_KEY,
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=25)
        data = resp.json()
        results = []
        for f in (data.get("best_flights", []) + data.get("other_flights", []))[:8]:
            fl = f.get("flights", [{}])
            results.append({
                "price":    f.get("price"),
                "airline":  fl[0].get("airline", ""),
                "duration": f.get("total_duration"),
                "stops":    len(fl) - 1,
                "dep_time": fl[0].get("departure_airport", {}).get("time", ""),
                "arr_time": fl[-1].get("arrival_airport", {}).get("time", ""),
            })
        return {
            "dest": dest_code, "destName": info["name"], "emoji": info["emoji"],
            "avg": info["avg"], "dep": dep_date, "ret": ret_date,
            "flights": results,
            "lowest": min((r["price"] for r in results if r["price"]), default=None),
        }
    except Exception as e:
        return {"error": str(e)}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        dest = qs.get("dest", ["TYO"])[0].upper()
        dep  = qs.get("dep",  [""])[0]
        ret  = qs.get("ret",  [""])[0]
        if not dep or not ret:
            from datetime import datetime, timedelta
            today = datetime.now()
            dep = (today + timedelta(days=14)).strftime("%Y-%m-%d")
            ret = (today + timedelta(days=19)).strftime("%Y-%m-%d")
        result = fetch_flights(dest, dep, ret)
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass
