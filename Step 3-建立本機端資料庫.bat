@echo off
:: [重要] 第一行留空避免 BOM 問題
:: 設定編碼為 UTF-8
chcp 65001 >nul

title Python Environment Installer
:: 切換到 batch 檔所在的目錄
cd /d "%~dp0"

echo ==========================================
echo     正在啟動虛擬環境並建立本機端資料庫
echo ==========================================

:: 1. 啟動虛擬環境
:: [安全修正] 這裡的 echo 文字移除了小括號 () 改用中括號 []
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo.
    echo [錯誤] 找不到虛擬環境 [venv]
    echo 請確認目錄下是否有 "venv" 資料夾
    echo.
    pause
    exit /b
)

python manage.py migrate

:: 5. 結果判斷
if %errorlevel% neq 0 (
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo        安裝失敗！請檢查上方紅字錯誤
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
) else (
    echo.
    echo ==========================================
    echo        恭喜！所有資料庫建立成功。
    echo ==========================================
)

pause