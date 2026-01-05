@echo off
chcp 65001 >nul
title Git 簡易同步工具

echo ==========================================
echo       Git 自動同步工具 (Add/Commit/Pull/Push)
echo ==========================================
echo.

:: 1. 提示使用者輸入 Commit 訊息
set /p "CommitMsg=請輸入 Commit 訊息 (若不輸入直接 Enter，預設為 Update): "

:: 如果使用者沒輸入，設定預設值
if "%CommitMsg%"=="" set CommitMsg=Update

echo.
echo ------------------------------------------
echo [Step 1] 正在加入檔案 (git add .)...
git add .
if %errorlevel% neq 0 goto Error

echo.
echo [Step 2] 正在提交變更 (git commit)...
:: 檢查是否有東西需要 commit，避免空的 commit 報錯
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo 沒有需要提交的變更，跳過 Commit 步驟。
) else (
    git commit -m "%CommitMsg%"
)

echo.
echo [Step 3] 正在從遠端更新 (git pull)...
:: 這裡通常是拉取 origin 的更動，若有衝突會在此停住
git pull
if %errorlevel% neq 0 goto Error

echo.
echo [Step 4] 正在推送至您的 Fork (git push)...
git push
if %errorlevel% neq 0 goto Error

echo.
echo ==========================================
echo       恭喜！所有動作已成功完成。
echo ==========================================
goto End

:Error
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo        發生錯誤，請檢查上方的紅字訊息
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

:End
echo.
pause