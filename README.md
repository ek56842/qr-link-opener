# QR Link Opener

[English](README.en.md) | 繁體中文

一個離線運作的 Windows 小工具：按下 `Ctrl + Shift + Q`，框選螢幕上的一個 QR Code，確認內容後開啟連結或複製文字。

## 功能

- 只在本機擷取與解碼 QR Code，不會上傳螢幕畫面或 QR 內容。
- 網址必須先由使用者確認，才會交給 Windows 的預設程式開啟。
- 支援一般 `http`／`https` 網址與 `line://` 連結；LINE 是否接手由 Windows 與已安裝的 LINE 決定。
- 純文字、Wi-Fi 設定等非網址內容只可複製，不會自動執行。
- 通知區常駐、全域快捷鍵、多螢幕框選與可切換的開機自動啟動。

## 安裝與使用

請從專案的 **Releases** 頁面下載：

- `QR-Link-Opener-Setup-x.y.z.exe`：建議一般使用者使用的安裝版。
- `QR-Link-Opener-x.y.z-portable.exe`：免安裝版，可放在任意資料夾執行。

安裝或啟動後：

1. 在右下角通知區找到 QR 圖示。
2. 按下 `Ctrl + Shift + Q`，或右鍵圖示後選擇「立即掃描 QR Code」。
3. 拖曳框選一個 QR Code；按 `Esc` 可取消。
4. 閱讀結果後選擇「開啟連結」或「複製」。

如果快捷鍵被其他軟體佔用，請從通知區選單手動開始掃描。

## 安全性與 SmartScreen

首版尚未附加 Windows 程式碼簽章。Windows SmartScreen 可能顯示下載或執行警告。請只從本專案官方 GitHub Releases 下載，並以 Release 附帶的 `SHA256SUMS.txt` 驗證檔案校驗值：

```powershell
Get-FileHash .\QR-Link-Opener-1.0.0-portable.exe -Algorithm SHA256
```

本工具不會自動開啟網址；只有你在結果視窗點選「開啟連結」後，Windows 才會處理該連結。

## 從原始碼執行

需求：Windows、Python 3.12 或更新版本。

```powershell
python -m venv build-venv
.\build-venv\Scripts\python.exe -m pip install -r requirements.txt
.\build-venv\Scripts\python.exe app.py
```

執行測試：

```powershell
.\build-venv\Scripts\python.exe -m unittest discover -s tests -v
```

建立免安裝 EXE：

```powershell
.\build.ps1
```

## 支援範圍

目前僅支援 Windows。請只掃描你有權讀取的畫面與 QR Code。

## 貢獻與授權

歡迎閱讀 [CONTRIBUTING.md](CONTRIBUTING.md) 並提出 Issue 或 Pull Request。本專案以 [MIT License](LICENSE) 授權。
