"""
api/overview.py — 所有航線最低票價概覽
GET /api/overview
"""
import os, json, requests, time
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

ROUTES = {
    "TYO": {"name": "東京",   "arrival_id": "TYO", "avg": 9800,  "emoji": "🗼"},
    "OSA": {"name": "大阪",   "arrival_id": "KIX", "avg": 8200,  "emoji": "🏯"},
    "SEL": {"name": "首爾",   "arrival_id": "ICN", "avg": 7500,  "emoji": "🇰🇷"},
    "BKK": {"name": "曼谷",   "arrival_id": "BKK", "avg": 8900,  "emoji": "🛕"},
    "SIN": {"name": "新加坡", "arrival_id": "SIN", "avg": 10500, "emoji": "🦁"},
    "HKG": {"name": "香港",   "arrival_id": "HKG", "avg": 5200,  "emoji": "🌃"},
    "KUL": {"name": "吉隆坡", "arrival_id": "KUL", "avg": 9000,  "emoji": "🏙️"},
    "MNL": {"name": "馬尼拉", "arrival_id": "MNL", "avg": 6200,  "emoji": "🌺"},
    "SGN": {"name": "胡志明", "arrival_id": "SGN", "avg": 8100,  "emoji": "🛵"},
    "CNX": {"name": "清邁",   "arrival_id": "CNX", "avg": 9500,  "emoji": "🌸"},
    "HKT": {"name": "普吉島", "arrival_id": "HKT", "avg": 10500, "emoji": "🏖️"},
    "DPS": {"name": "峇里島", "arrival_id": "DPS", "avg": 12000, "emoji": "🌴"},
    "DAD": {"name": "峴港",   "arrival_id": "DAD", "avg": 8500,  "emoji": "🌊"},
    "HAN": {"name": "河內",   "arrival_id": "HAN", "avg": 7800,  "emoji": "🏛️"},
    "CEB": {"name": "宿霧",   "arrival_id": "CEB", "avg": 7200,  "emoji": "🐠"},
    "RGN": {"name": "仰光",   "arrival_id": "RGN", "avg": 11000, "emoji": "🙏"},
}

def fetch_lowest(dest_code, dep_date, ret_date):
    info = ROUTES[dest_code]
    params = {
        "engine": "google_flights", "departure_id": "TPE",
        "arrival_id": info["arrival_id"], "outbound_date": dep_date,
        "return_date": ret_date, "currency": "TWD", "hl": "zh-tw",
        "type": "1", "api_key": SERPAPI_KEY,
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
        data = resp.json()
        all_f = data.get("best_flights", []) + data.get("other_flights", [])
        prices = [f.get("price") for f in all_f if f.get("price")]
        if not prices: return None
        best = min(all_f, key=lambda x: x.get("price", 999999))
        fl = best.get("flights", [{}])
        return {
            "dest": dest_code, "destName": info["name"], "emoji": info["emoji"],
            "avg": info["avg"], "lowest": min(prices),
            "airline": fl[0].get("airline", ""),
            "dep": dep_date, "ret": ret_date,
        }
    except:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not SERPAPI_KEY:
            body = json.dumps({"error": "未設定 SERPAPI_KEY"}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return
        today = datetime.now()
        dep = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        ret = (today + timedelta(days=19)).strftime("%Y-%m-%d")
        results = []
        for code in ROUTES:
            r = fetch_lowest(code, dep, ret)
            if r: results.append(r)
            time.sleep(0.5)
        body = json.dumps(results, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass
