@echo off
:: [重要] 第一行留空避免 BOM 問題
:: 設定編碼為 UTF-8
chcp 65001 >nul

title Python Venv Creator
:: [重要] 確保工作目錄正確 (避免找不到 venv)
cd /d "%~dp0"

echo ==========================================
echo       正在建立 Python 虛擬環境 (venv)
echo ==========================================

:: 1. 檢查電腦是否有安裝 Python
py --version
if %errorlevel% neq 0 (
    echo.
    echo [嚴重錯誤] 找不到 'py' 指令！
    echo ------------------------------------------
    echo 請確認：
    echo 1. 您已安裝 Python
    echo 2. 安裝時有勾選 "Add Python to PATH"
    echo.
    pause
    exit /b
)

:: 2. 檢查是否已經存在 venv 資料夾
if exist "venv\" (
    echo.
    echo [提示] 偵測到目錄下已存在 "venv" 資料夾
    echo ------------------------------------------
    echo 系統將「跳過」建立步驟，保留您現有的環境
    echo.
    echo [如果您想重新建立，請手動刪除 venv 資料夾後再執行此程式]
    goto End
)

:: 3. 開始建立
echo.
echo 正在執行建立指令 (py -m venv venv)...
echo 請稍候...

py -m venv venv

if %errorlevel% neq 0 (
    echo.
    echo [失敗] 建立失敗
    echo 可能原因：權限不足或 Python 安裝損毀
    pause
    exit /b
)

echo.
echo ==========================================
echo       成功！虛擬環境 'venv' 已建立。
echo ==========================================

:End
echo.
echo [下一步] 建議接著執行 Step 2-安裝所有套件.bat 來安裝套件
pause