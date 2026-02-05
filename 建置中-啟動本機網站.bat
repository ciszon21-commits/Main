
@echo off
:: [關鍵修正] 強制切換為 UTF-8 編碼，解決亂碼問題
chcp 65001 >nul
title Django Server Launcher
:: 切換到 batch 檔所在的目錄，確保路徑正確
cd /d "%~dp0"

echo ==========================================
echo       正在準備啟動網站環境...
echo ==========================================

:: 1. 檢查並啟動虛擬環境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo.
    echo [錯誤] 找不到虛擬環境啟動檔！
    echo 請確認目錄下是否有 "venv" 資料夾，以及 "Scripts" 資料夾。
    echo.
    pause
    exit /b
)

:: 2. 檢查 manage.py 是否存在
if not exist "manage.py" (
    echo.
    echo [錯誤] 找不到 manage.py！
    echo 請確認此 .bat 檔是否放在 Django 專案的根目錄。
    echo.
    pause
    exit /b
)

echo 環境啟動成功 (venv activated)
echo.
echo ==========================================
echo       正在啟動 Django Server...
echo       請稍候，伺服器啟動後通常位於: http://127.0.0.1:8000
echo       (若要停止伺服器，請按 Ctrl+C)
echo ==========================================
echo.

:: 3. 執行 runserver
:: 注意：啟動 venv 後，直接用 python 指令通常比 py 更能確保用到 venv 裡的解釋器
python manage.py runserver

:: 4. 如果伺服器意外崩潰或關閉，暫停視窗讓使用者看錯誤訊息
echo.
echo Server 已停止。
pause