@echo off
:: [重要] 第一行留空避免 BOM 問題
:: 設定編碼為 UTF-8
chcp 65001 >nul

title Python Environment Installer
:: 切換到 batch 檔所在的目錄
cd /d "%~dp0"

echo ==========================================
echo       正在啟動虛擬環境並安裝套件
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

:: 2. 檢查 requirements.txt 是否存在
if not exist "requirements.txt" (
    echo.
    echo [錯誤] 找不到 requirements.txt
    echo 請確認檔案是否在同一個目錄下
    echo.
    pause
    exit /b
)

:: 3. 偵測可用的 Python 指令 (用於升級 pip)
set "PYTHON_CMD="
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
    )
)

if "%PYTHON_CMD%"=="" (
    set "PYTHON_CMD=python"
)

echo.
echo [Step 1/2] 正在檢查 pip 版本...

%PYTHON_CMD% -m pip install --upgrade pip

:: 4. 安裝套件
echo.
echo [Step 2/2] 正在安裝 requirements.txt 中的套件...
echo 這可能需要一點時間，視網路速度而定...
echo ------------------------------------------
pip install -r requirements.txt

:: 5. 結果判斷
if %errorlevel% neq 0 (
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo        安裝失敗！請檢查上方紅字錯誤
    echo        常見原因：網路不通、權限不足
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
) else (
    echo.
    echo ==========================================
    echo        恭喜！所有套件安裝成功。
    echo ==========================================
)

pause