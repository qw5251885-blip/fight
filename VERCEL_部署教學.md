# Vercel 部署教學（真實票價網站）

## 為什麼需要 Vercel？

GitHub Pages 是靜態網站，無法隱藏 API Key 或直接呼叫外部 API。
Vercel 提供免費的後端伺服器，幫你安全地串接 SerpApi 抓取真實票價。

---

## 步驟一：把程式碼放到 GitHub（新的 Repository）

1. 去 GitHub 建立一個**新的 Repository**，名稱例如 `tpe-fares-real`
2. 把這包 zip 裡的所有檔案上傳（全選拖曳）
3. Commit

---

## 步驟二：註冊 Vercel

1. 去 [https://vercel.com](https://vercel.com) 點 **Sign Up**
2. 選 **Continue with GitHub**（用 GitHub 帳號登入最方便）
3. 授權 Vercel 存取你的 GitHub

---

## 步驟三：部署專案

1. 登入 Vercel 後，點 **Add New → Project**
2. 找到你剛建立的 `tpe-fares-real` Repository，點 **Import**
3. 設定頁面：
   - Framework Preset 選 **Other**
   - Root Directory 保持空白
4. 點 **Deploy**（先不用設定環境變數，等部署完再設）
5. 等約 1 分鐘，看到 🎉 就部署成功

---

## 步驟四：設定 SERPAPI_KEY 環境變數

1. 在 Vercel 專案頁面，點上方 **Settings**
2. 左側點 **Environment Variables**
3. 點 **Add New**：
   - Key：`SERPAPI_KEY`
   - Value：貼上你的 SerpApi API Key
   - Environment 三個都勾（Production、Preview、Development）
4. 點 **Save**

---

## 步驟五：重新部署

設定環境變數後要重新部署才會生效：

1. 點上方 **Deployments**
2. 最新那筆右邊點 **⋯** → **Redeploy**
3. 等部署完成

---

## 完成！

Vercel 會給你一個網址，格式像：
```
https://tpe-fares-real.vercel.app
```

這就是你的真實票價網站！每次打開都會從 Google Flights 抓最新資料。

---

## 常見問題

**Q：網站打開後顯示「載入失敗」？**
確認 SERPAPI_KEY 有設定，且重新部署過。

**Q：每月 100 次免費夠用嗎？**
概覽頁每次載入消耗 9 次（9 條航線），搜尋每次 1 次。
每天看 2–3 次概覽 + 幾次搜尋，大約夠用。
需要更多可升級 SerpApi 方案（每月約 $50）。

**Q：原本的 GitHub Pages 網站還能用嗎？**
可以！那個繼續放著沒問題，兩個網站互不影響。
Vercel 的才是真實票價版本。

**Q：Telegram 通知還有效嗎？**
有效！GitHub Actions 的通知是獨立的，繼續每天早上跑。
