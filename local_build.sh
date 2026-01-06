#!/bin/bash
set -e  # 遇到错误立即停止

echo "🚀 开始本地构建流程..."

# 0. 检查环境
if ! command -v pyinstaller &> /dev/null; then
    echo "⚠️  未检测到 PyInstaller，正在安装..."
    pip install pyinstaller
fi

# 1. 清理旧构建
echo "🧹 清理旧构建产物..."
rm -rf build dist
rm -rf frontend/src-tauri/binaries
rm -rf frontend/src-tauri/target
mkdir -p frontend/src-tauri/binaries

# 2. 编译 Python Sidecar
echo "🐍 正在编译 Python 后端 (这可能需要几分钟)..."
# 注意：这里使用 --onefile 打包成单文件
python -m PyInstaller --clean --noconfirm --onefile --name api-server --collect-all playwright_stealth main.py

# 3. 移动并重命名 Sidecar
# 获取当前机器架构 (arm64 或 x86_64)
ARCH=$(uname -m)
if [ "$ARCH" == "arm64" ]; then
  TARGET="aarch64-apple-darwin"
else
  TARGET="x86_64-apple-darwin"
fi

echo "📦 适配系统架构: $TARGET"
cp dist/api-server "frontend/src-tauri/binaries/api-server-$TARGET"
chmod +x "frontend/src-tauri/binaries/api-server-$TARGET"

# 调试：显示详细的文件列表
echo "🔍 验证二进制文件位置:"
ls -lR frontend/src-tauri/binaries

verify_path="frontend/src-tauri/binaries/api-server-$TARGET"
if [ -f "$verify_path" ]; then
    echo "✅ Sidecar 准备就绪: $verify_path"
else
    echo "❌ Sidecar 文件移动失败！"
    exit 1
fi

# 4. 构建 Tauri 应用
echo "🦀 开始构建 Tauri 应用..."
cd frontend
# 确保前端依赖已安装
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 执行构建 (增加 verbose 模式以便排查)
npm run tauri build -- --verbose

echo "--------------------------------------------------------"
echo "🎉 构建完成！"
echo "生成的 .dmg / .app 文件位于: frontend/src-tauri/target/release/bundle/macos/"
echo "提示: 请直接运行 .app 文件来验证 Sidecar 是否能正常启动。"
echo "--------------------------------------------------------"
