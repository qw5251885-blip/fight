// app.js — 真實票價前端邏輯（16 條航線版）

const ROUTE_GROUPS = {
  TH:  ["BKK","CNX","HKT"],
  VN:  ["SGN","HAN","DAD"],
  JP:  ["TYO","OSA"],
  SEA: ["SIN","KUL","DPS","MNL","CEB"],
};

let overviewData = [];

function priceLevel(price, avg) {
  const r = price / avg;
  if (r <= 0.85) return "deal";
  if (r >= 1.15) return "high";
  return "normal";
}
function formatDuration(min) {
  if (!min) return "";
  return `${Math.floor(min/60)}h ${min%60}m`;
}
function updateTime() {
  const el = document.getElementById("update-time");
  if (el) el.textContent = `更新 ${new Date().toLocaleTimeString("zh-TW",{hour12:false})}`;
}
setInterval(updateTime, 1000); updateTime();

window.addEventListener("DOMContentLoaded", () => {
  const today = new Date();
  const dep = new Date(today); dep.setDate(today.getDate()+14);
  const ret = new Date(today); ret.setDate(today.getDate()+19);
  document.getElementById("dep-date").value = dep.toISOString().slice(0,10);
  document.getElementById("ret-date").value = ret.toISOString().slice(0,10);
  loadOverview();
});

// ── 搜尋 ────────────────────────────────────────────────────────────────────
async function searchFlights() {
  const dest = document.getElementById("dest-select").value;
  const dep  = document.getElementById("dep-date").value;
  const ret  = document.getElementById("ret-date").value;
  const btn  = document.querySelector(".search-btn");
  const txt  = document.getElementById("search-btn-text");
  const destText = document.getElementById("dest-select").selectedOptions[0].text;

  if (!dep||!ret){alert("請選擇出發和回程日期");return;}
  if(new Date(ret)<=new Date(dep)){alert("回程日期必須晚於出發日期");return;}

  btn.disabled=true; txt.textContent="查詢中...";
  document.getElementById("result-section").style.display="none";
  document.getElementById("loading-section").style.display="block";
  document.getElementById("loading-text").textContent=`正在查詢 台北 → ${destText.split(" ")[0]} 的 Google Flights 票價...`;

  try {
    const res  = await fetch(`/api/flights?dest=${dest}&dep=${dep}&ret=${ret}`);
    const data = await res.json();
    if(data.error) throw new Error(data.error);
    renderResult(data);
  } catch(e) {
    alert("查詢失敗："+e.message+"\n請確認 SERPAPI_KEY 已設定");
  } finally {
    btn.disabled=false; txt.textContent="🔍 查詢真實票價";
    document.getElementById("loading-section").style.display="none";
  }
}

function renderResult(data) {
  document.getElementById("result-section").style.display="block";
  const emoji = data.emoji || "✈";
  document.getElementById("result-title").textContent=
    `${emoji} 台北桃園 → ${data.destName}　${data.dep} ⇄ ${data.ret}`;

  const lowest=data.lowest, avg=data.avg;
  const lv=lowest?priceLevel(lowest,avg):"normal";
  const save=lowest?Math.round((1-lowest/avg)*100):0;

  let ins=`均價參考：TWD $${avg.toLocaleString()}`;
  if(lowest&&lv==="deal") ins+=`　<span class="low">現在便宜 ${save}%！最低 $${lowest.toLocaleString()}</span>`;
  else if(lowest&&lv==="high") ins+=`　<span class="high">現在偏高 ${Math.abs(save)}%</span>`;
  document.getElementById("price-insight").innerHTML=ins;
  document.getElementById("stat-low").textContent=lowest?`$${lowest.toLocaleString()}`:"—";

  const grid=document.getElementById("flights-grid");
  if(!data.flights||!data.flights.length){
    grid.innerHTML=`<div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text3)">找不到此日期的航班，請嘗試其他日期</div>`;
    return;
  }
  grid.innerHTML=data.flights.map((f,i)=>{
    const lv=priceLevel(f.price,avg);
    const dep_t=f.dep_time?f.dep_time.slice(11,16):"";
    const arr_t=f.arr_time?f.arr_time.slice(11,16):"";
    const stops=f.stops===0?"直飛":`${f.stops} 次轉機`;
    const dur=formatDuration(f.duration);
    const save=Math.round((1-f.price/avg)*100);
    return `
<div class="flight-card ${lv==='deal'?'is-deal':''}" style="animation-delay:${i*50}ms">
  <div class="card-top">
    <div class="route-display">
      <span class="city-code">TPE</span>
      <div class="route-arrow"><span>✈</span><div class="route-line"></div></div>
      <span class="city-code">${data.dest}</span>
    </div>
    ${lv==='deal'?`<span class="deal-tag great">省 ${save}%</span>`:lv==='high'?`<span class="deal-tag high">偏高 ${Math.abs(save)}%</span>`:`<span class="deal-tag normal">一般</span>`}
  </div>
  <div class="card-meta">
    ${dep_t?`<span>✈ ${dep_t} → ${arr_t}</span>`:""}
    ${dur?`<span>⏱ ${dur}</span>`:""}
    <span>${stops}</span>
  </div>
  <div class="card-bottom">
    <div>
      <div class="price-currency">TWD 來回含稅</div>
      <div class="price-main ${lv==='deal'?'deal-price':''}">$${f.price.toLocaleString()}</div>
      <div class="price-avg">均價 $${avg.toLocaleString()}${lv==='deal'?`<span class="price-save"> 省 $${(avg-f.price).toLocaleString()}</span>`:""}</div>
    </div>
    <a class="book-btn" href="https://www.google.com/travel/flights?hl=zh-TW" target="_blank" rel="noopener">訂票 ↗</a>
  </div>
  <div class="airline-row"><span>${f.airline}</span><span>Google Flights 即時</span></div>
</div>`;
  }).join("");
  document.getElementById("result-section").scrollIntoView({behavior:"smooth",block:"start"});
}

// ── 概覽 ─────────────────────────────────────────────────────────────────────
async function loadOverview() {
  document.getElementById("overview-grid").innerHTML=`<div class="overview-loading">⏳ 正在從 Google Flights 抓取 16 條航線票價，約需 30 秒...</div>`;
  try {
    const res=await fetch("/api/overview");
    const data=await res.json();
    if(data.error) throw new Error(data.error);
    overviewData=data;
    renderOverview(data);
  } catch(e) {
    document.getElementById("overview-grid").innerHTML=`<div class="overview-loading">⚠ 載入失敗：${e.message}</div>`;
  }
}

function filterOverview(filter, btn) {
  document.querySelectorAll(".tab-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  let filtered=overviewData;
  if(filter==="deal") filtered=overviewData.filter(i=>i.lowest&&priceLevel(i.lowest,i.avg)==="deal");
  else if(ROUTE_GROUPS[filter]) filtered=overviewData.filter(i=>ROUTE_GROUPS[filter].includes(i.dest));
  renderOverview(filtered);
}

function renderOverview(items) {
  const grid=document.getElementById("overview-grid");
  if(!items.length){grid.innerHTML=`<div class="overview-loading">無符合條件的航線</div>`;return;}

  const deals=items.filter(i=>i.lowest&&priceLevel(i.lowest,i.avg)==="deal");
  const allLow=items.filter(i=>i.lowest).map(i=>i.lowest);
  document.getElementById("stat-deals").textContent=deals.length;
  if(allLow.length) document.getElementById("stat-low").textContent="$"+Math.min(...allLow).toLocaleString();

  grid.innerHTML=items.map((item,i)=>{
    const lv=item.lowest?priceLevel(item.lowest,item.avg):"normal";
    const save=item.lowest?Math.round((1-item.lowest/item.avg)*100):0;
    return `
<div class="overview-card ${lv==='deal'?'is-deal':''}"
     style="animation:fadeUp 0.4s ease ${i*40}ms both"
     onclick="selectRoute('${item.dest}')">
  <div class="ov-emoji">${item.emoji||"✈"}</div>
  <div class="ov-route">台北 → ${item.destName}</div>
  <div class="ov-airline">${item.airline||""}</div>
  <div class="ov-price ${lv==='deal'?'deal':lv==='high'?'high':''}">
    ${item.lowest?`$${item.lowest.toLocaleString()}`:"—"}
  </div>
  <div class="ov-avg">均價 $${item.avg.toLocaleString()}${lv==='deal'&&save>0?`<span class="ov-save"> 省 ${save}%</span>`:""}</div>
  <span class="ov-tag ${lv==='deal'?'deal':lv==='high'?'high':'normal'}">${lv==='deal'?'🔥 特惠':lv==='high'?'偏高':'一般'}</span>
</div>`;
  }).join("");
}

function selectRoute(dest) {
  document.getElementById("dest-select").value=dest;
  document.querySelector(".search-bar").scrollIntoView({behavior:"smooth"});
  searchFlights();
}
