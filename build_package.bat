@echo off
chcp 65001 >nul
echo ==========================================
echo 清简浏览器 Windows 打包工具
echo ==========================================
echo.

echo 1. 激活虚拟环境...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
) else (
    echo ❌ 虚拟环境不存在，请先创建虚拟环境
    echo 运行: python -m venv .venv
    pause
    exit /b 1
)

echo.
echo 2. 运行打包检查和构建...
python build_windows.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo ✅ 打包完成成功！
    echo ==========================================
    echo 可执行文件位置: dist\全网直播浏览器\全网直播浏览器.exe
    echo.
    echo 是否现在测试运行？(y/n)
    set /p choice=
    if /i "%choice%"=="y" (
        echo 启动测试...
        start "" "dist\全网直播浏览器\全网直播浏览器.exe"
    )
) else (
    echo.
    echo ==========================================
    echo ❌ 打包失败！
    echo ==========================================
    echo 请检查上述错误信息并解决问题
)

echo.
pause