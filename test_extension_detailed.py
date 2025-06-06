#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的插件加载测试脚本
包含开发者模式和更全面的检查
"""

import asyncio
import json
from pathlib import Path
from DrissionPage import ChromiumOptions, Chromium
from conf import BASE_DIR


def get_extension_path(extension_name: str) -> str:
    """获取插件绝对路径"""
    extension_path = Path(BASE_DIR) / "extensions" / extension_name
    return str(extension_path)


def check_manifest_validity(manifest_path: Path) -> bool:
    """检查manifest.json文件的有效性"""
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        # 检查必要字段
        required_fields = ['manifest_version', 'name', 'version']
        for field in required_fields:
            if field not in manifest_data:
                print(f"❌ manifest.json缺少必要字段: {field}")
                return False
        
        print(f"✅ manifest.json有效 - 名称: {manifest_data.get('name')}, 版本: {manifest_data.get('version')}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ manifest.json格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取manifest.json失败: {e}")
        return False


async def test_extension_loading_detailed():
    """详细测试插件加载功能"""
    print("=== 详细插件加载测试 ===")
    
    # 获取插件路径
    live_room_path = get_extension_path("live_room")
    block_videos_path = get_extension_path("block_videos")
    
    print(f"Live Room 插件路径: {live_room_path}")
    print(f"Block Videos 插件路径: {block_videos_path}")
    
    # 检查插件目录和文件
    extensions_to_test = [
        ("Live Room", live_room_path),
        ("Block Videos", block_videos_path)
    ]
    
    valid_extensions = []
    
    for name, path in extensions_to_test:
        print(f"\n=== 检查 {name} 插件 ===")
        
        extension_dir = Path(path)
        if not extension_dir.exists():
            print(f"❌ {name} 插件目录不存在: {path}")
            continue
        
        print(f"✅ {name} 插件目录存在")
        
        # 检查manifest.json
        manifest_path = extension_dir / "manifest.json"
        if not manifest_path.exists():
            print(f"❌ {name} 插件缺少manifest.json")
            continue
        
        if not check_manifest_validity(manifest_path):
            continue
        
        # 检查其他重要文件
        important_files = ['background.js', 'content.js']
        for file_name in important_files:
            file_path = extension_dir / file_name
            if file_path.exists():
                print(f"✅ {name} 包含 {file_name}")
            else:
                print(f"⚠️ {name} 缺少 {file_name}")
        
        valid_extensions.append((name, path))
    
    if not valid_extensions:
        print("\n❌ 没有有效的插件可以测试")
        return False
    
    # 配置Chromium选项（开发者模式）
    user_data_dir = Path(BASE_DIR) / "data" / "user_static" / "test_browser_dev"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== 配置浏览器选项 ===")
    print(f"用户数据目录: {user_data_dir}")
    
    options = (
        ChromiumOptions()
        .set_user_data_path(str(user_data_dir))
        .set_argument("--enable-extensions")
        .set_argument("--load-extension=" + ",".join([path for _, path in valid_extensions]))
        .set_argument("--disable-extensions-except=" + ",".join([path for _, path in valid_extensions]))
        .set_argument("--window-size", "1400,900")
        .set_argument("--disable-web-security")
        .set_argument("--disable-features=VizDisplayCompositor")
    )
    
    print(f"加载的插件: {[name for name, _ in valid_extensions]}")
    
    # 启动浏览器
    print("\n=== 启动浏览器 ===")
    try:
        browser = Chromium(options)
        print("✅ 浏览器启动成功")
        
        # 等待插件加载
        print("等待插件加载...")
        await asyncio.sleep(5)
        
        # 打开扩展管理页面
        tab = browser.latest_tab
        print("\n=== 检查扩展管理页面 ===")
        tab.get('chrome://extensions/')
        await asyncio.sleep(3)
        
        # 启用开发者模式
        try:
            # 查找开发者模式切换按钮
            dev_mode_toggle = tab.ele('css:#devMode')
            if dev_mode_toggle and not dev_mode_toggle.property('checked'):
                dev_mode_toggle.click()
                print("✅ 已启用开发者模式")
                await asyncio.sleep(2)
            else:
                print("✅ 开发者模式已启用")
        except Exception as e:
            print(f"⚠️ 无法切换开发者模式: {e}")
        
        # 检查页面内容
        page_html = tab.html
        
        print("\n=== 检查插件加载状态 ===")
        for name, path in valid_extensions:
            # 检查插件名称
            if name.lower() in page_html.lower():
                print(f"✅ {name} 插件已检测到")
            else:
                print(f"❌ {name} 插件未检测到")
        
        # 尝试获取扩展信息
        try:
            # 执行JavaScript获取扩展信息
            js_code = """
            return new Promise((resolve) => {
                chrome.management.getAll((extensions) => {
                    resolve(extensions.map(ext => ({
                        name: ext.name,
                        id: ext.id,
                        enabled: ext.enabled,
                        type: ext.type
                    })));
                });
            });
            """
            
            extensions_info = tab.run_js(js_code)
            if extensions_info:
                print("\n=== 已安装的扩展 ===")
                for ext in extensions_info:
                    if ext.get('type') == 'extension':
                        status = "启用" if ext.get('enabled') else "禁用"
                        print(f"- {ext.get('name')} (ID: {ext.get('id')}) - {status}")
            
        except Exception as e:
            print(f"⚠️ 无法获取扩展信息: {e}")
        
        # 保持浏览器打开供手动检查
        print("\n浏览器将保持打开60秒，请手动检查插件状态...")
        print("请在扩展管理页面查看插件是否正确加载")
        await asyncio.sleep(60)
        
        # 关闭浏览器
        browser.quit()
        print("✅ 浏览器已关闭")
        
        return True
        
    except Exception as e:
        print(f"❌ 浏览器操作失败: {e}")
        return False


if __name__ == "__main__":
    print("Chrome插件详细加载测试工具")
    print("=" * 60)
    
    # 运行测试
    result = asyncio.run(test_extension_loading_detailed())
    
    if result:
        print("\n🎉 详细测试完成")
    else:
        print("\n❌ 详细测试失败")