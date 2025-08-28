@echo off
echo 设置环境变量跳过单例检查...
echo （现在使用QLocalServer机制，更加稳定可靠）
set QW_BROWSER_SKIP_SINGLETON_CHECK=1

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo 启动应用程序...
python app.py

pause