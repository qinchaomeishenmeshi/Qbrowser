@echo off
chcp 65001 >nul
title QW-Browser 锁文件清理工具

echo.
echo ====================================
echo QW-Browser 锁文件清理工具
echo ====================================
echo.

echo 正在查找和清理锁文件...
echo.

REM 清理系统临时目录中的锁文件
if exist "%TEMP%\qw_browser_app.lock" (
    echo 发现锁文件: %TEMP%\qw_browser_app.lock
    del "%TEMP%\qw_browser_app.lock" 2>nul
    if not exist "%TEMP%\qw_browser_app.lock" (
        echo ✓ 成功删除: %TEMP%\qw_browser_app.lock
    ) else (
        echo ✗ 删除失败: %TEMP%\qw_browser_app.lock （可能需要管理员权限）
    )
) else (
    echo 未发现系统临时目录锁文件
)

REM 清理用户目录中的锁文件
if exist "%USERPROFILE%\qw_browser_app.lock" (
    echo 发现锁文件: %USERPROFILE%\qw_browser_app.lock
    del "%USERPROFILE%\qw_browser_app.lock" 2>nul
    if not exist "%USERPROFILE%\qw_browser_app.lock" (
        echo ✓ 成功删除: %USERPROFILE%\qw_browser_app.lock
    ) else (
        echo ✗ 删除失败: %USERPROFILE%\qw_browser_app.lock （可能需要管理员权限）
    )
) else (
    echo 未发现用户目录锁文件
)

REM 清理当前目录中的锁文件
if exist "qw_browser_app.lock" (
    echo 发现锁文件: %CD%\qw_browser_app.lock
    del "qw_browser_app.lock" 2>nul
    if not exist "qw_browser_app.lock" (
        echo ✓ 成功删除: %CD%\qw_browser_app.lock
    ) else (
        echo ✗ 删除失败: %CD%\qw_browser_app.lock （可能需要管理员权限）
    )
) else (
    echo 未发现当前目录锁文件
)

echo.
echo ====================================
echo 清理完成！
echo ====================================
echo.
echo 如果仍然遇到问题，请尝试：
echo 1. 以管理员身份运行此脚本
echo 2. 关闭杀毒软件实时防护
echo 3. 检查任务管理器中是否有残留进程
echo 4. 运行: python cleanup_lock.py
echo.
echo 现在可以尝试重新启动应用程序
echo.

pause
