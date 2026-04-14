#!/usr/bin/env python3
"""check_flights.py — SerpApi 真實票價 + Telegram 通知（16 條航線版）"""
import os, requests, time
from datetime import datetime, timedelta

BOT_TOKEN        = os.environ.get("TELEGRAM_BOT_TOKEN","")
CHAT_ID          = os.environ.get("TELEGRAM_CHAT_ID","")
SERPAPI_KEY      = os.environ.get("SERPAPI_KEY","")
ALERT_ROUTES_RAW = os.environ.get("ALERT_ROUTES",
    "TYO:9000,OSA:7500,SEL:6500,BKK:7000,CNX:8500,HKT:9000,SIN:9000,HKG:4500,KUL:8000,MNL:5500,SGN:7000,HAN:7000,DAD:7500,DPS:11000,CEB:6500,RGN:10000")

ROUTES = {
    "TYO":{"name":"東京",   "arrival_id":"TYO","avg":9800},
    "OSA":{"name":"大阪",   "arrival_id":"KIX","avg":8200},
    "SEL":{"name":"首爾",   "arrival_id":"ICN","avg":7500},
    "BKK":{"name":"曼谷",   "arrival_id":"BKK","avg":8900},
    "CNX":{"name":"清邁",   "arrival_id":"CNX","avg":9500},
    "HKT":{"name":"普吉島", "arrival_id":"HKT","avg":10500},
    "SIN":{"name":"新加坡", "arrival_id":"SIN","avg":10500},
    "HKG":{"name":"香港",   "arrival_id":"HKG","avg":5200},
    "KUL":{"name":"吉隆坡", "arrival_id":"KUL","avg":9000},
    "MNL":{"name":"馬尼拉", "arrival_id":"MNL","avg":6200},
    "SGN":{"name":"胡志明", "arrival_id":"SGN","avg":8100},
    "HAN":{"name":"河內",   "arrival_id":"HAN","avg":7800},
    "DAD":{"name":"峴港",   "arrival_id":"DAD","avg":8500},
    "DPS":{"name":"峇里島", "arrival_id":"DPS","avg":12000},
    "CEB":{"name":"宿霧",   "arrival_id":"CEB","avg":7200},
    "RGN":{"name":"仰光",   "arrival_id":"RGN","avg":11000},
}

def fetch_price(dest_code, dep, ret):
    info = ROUTES[dest_code]
    params = {"engine":"google_flights","departure_id":"TPE","arrival_id":info["arrival_id"],
              "outbound_date":dep,"return_date":ret,"currency":"TWD","hl":"zh-tw","type":"1","api_key":SERPAPI_KEY}
    try:
        data = requests.get("https://serpapi.com/search",params=params,timeout=25).json()
        all_f = data.get("best_flights",[]) + data.get("other_flights",[])
        prices = [f.get("price") for f in all_f if f.get("price")]
        if not prices: return None
        best = min(all_f,key=lambda x:x.get("price",999999))
        fl = best.get("flights",[{}])
        return {"price":min(prices),"airline":fl[0].get("airline","")}
    except Exception as e:
        print(f"  ⚠ {dest_code} 失敗：{e}"); return None

def check_alerts():
    alert_map = {}
    for item in ALERT_ROUTES_RAW.split(","):
        p = item.strip().split(":")
        if len(p)==2: alert_map[p[0].strip()]=int(p[1].strip())
    today = datetime.now()
    triggered = []
    for code, target in alert_map.items():
        if code not in ROUTES: continue
        info = ROUTES[code]
        print(f"🔍 台北→{info['name']} (目標 ${target:,})...")
        best = None
        for days in [7,14,30]:
            dep=(today+timedelta(days=days)).strftime("%Y-%m-%d")
            ret=(today+timedelta(days=days+5)).strftime("%Y-%m-%d")
            r=fetch_price(code,dep,ret)
            if r and r["price"]: print(f"   {dep}：${r['price']:,}")
            if r and r["price"] and (best is None or r["price"]<best["price"]):
                best={"price":r["price"],"airline":r["airline"],"dep":dep,"ret":ret}
            time.sleep(1.5)
        if best and best["price"]<=target:
            avg=info["avg"]; saving=avg-best["price"]
            triggered.append({**best,"dest_name":info["name"],"target":target,"avg":avg,
                               "saving":saving,"saving_pct":round(saving/avg*100)})
            print(f"   ✅ 特惠！")
    return triggered

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID: print("⚠ 未設定 Telegram 環境變數"); return False
    r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"},timeout=10)
    return r.status_code==200

def build_message(triggered):
    now=datetime.now().strftime("%Y/%m/%d %H:%M")
    if not triggered:
        return f"✈ <b>TPE 機票追蹤報告</b>\n🕐 {now}\n\n今日查詢完畢，目前無低於目標價的航班。"
    lines=[f"🎉 <b>TPE 機票特惠通知！</b>",f"🕐 {now}",f"找到 <b>{len(triggered)}</b> 條特惠！\n","─────────────────"]
    for t in triggered:
        lines+=[f"\n✈ <b>台北桃園 → {t['dest_name']}</b>",
                f"💰 TWD <b>${t['price']:,}</b>（來回含稅）",
                f"📉 比均價便宜 <b>{t['saving_pct']}%</b>（省 ${t['saving']:,}）",
                f"🛫 出發 {t['dep']} → 回程 {t['ret']}",
                f"🏢 {t['airline']}  🎯 目標 ${t['target']:,}"]
    lines+=["\n─────────────────",'👉 <a href="https://www.google.com/travel/flights?hl=zh-TW">前往 Google Flights 訂票</a>']
    return "\n".join(lines)

def main():
    if not SERPAPI_KEY: print("❌ 未設定 SERPAPI_KEY"); return
    print("="*40+"\n✈  TPE 機票追蹤（16 條航線）\n"+"="*40)
    triggered=check_alerts()
    msg=build_message(triggered)
    print("\n─── 訊息預覽 ───\n"+msg)
    if triggered:
        ok=send_telegram(msg)
        print("✅ Telegram 傳送成功！" if ok else "❌ 傳送失敗")
    else: print("（無特惠，不傳送）")

if __name__=="__main__": main()
