#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化插件加载测试脚本
用于验证浏览器插件是否能够正确加载
"""

import asyncio
from pathlib import Path
from DrissionPage import ChromiumOptions, Chromium
from conf import BASE_DIR, resource_path


def get_extension_path(extension_name: str) -> str:
    """获取插件绝对路径"""
    extension_path = Path(resource_path(f"extensions/{extension_name}"))
    return str(extension_path)


async def test_extension_loading():
    """测试插件加载功能"""
    print("=== 开始测试插件加载 ===")
    
    # 获取插件路径
    live_room_path = get_extension_path("live_room")
    block_videos_path = get_extension_path("block_videos")
    
    print(f"Live Room 插件路径: {live_room_path}")
    print(f"Block Videos 插件路径: {block_videos_path}")
    
    # 检查插件目录是否存在
    live_room_exists = Path(live_room_path).exists()
    block_videos_exists = Path(block_videos_path).exists()
    
    print(f"Live Room 插件目录存在: {live_room_exists}")
    print(f"Block Videos 插件目录存在: {block_videos_exists}")
    
    if not live_room_exists:
        print(f"❌ Live Room 插件目录不存在: {live_room_path}")
        return False
        
    if not block_videos_exists:
        print(f"❌ Block Videos 插件目录不存在: {block_videos_path}")
        return False
    
    # 检查插件manifest文件
    live_room_manifest = Path(live_room_path) / "manifest.json"
    block_videos_manifest = Path(block_videos_path) / "manifest.json"
    
    print(f"Live Room manifest存在: {live_room_manifest.exists()}")
    print(f"Block Videos manifest存在: {block_videos_manifest.exists()}")
    
    # 配置Chromium选项
    user_data_dir = Path(resource_path("data/user_static/test_browser"))
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    options = (
        ChromiumOptions()
        .set_user_data_path(str(user_data_dir))
        .set_argument("--enable-extensions")
        .set_argument("--window-size", "1200,800")
    )
    
    # 添加插件
    print("\n=== 添加插件到浏览器 ===")
    try:
        options.add_extension(live_room_path)
        print(f"✅ 成功添加 Live Room 插件: {live_room_path}")
    except Exception as e:
        print(f"❌ 添加 Live Room 插件失败: {e}")
        return False
    
    try:
        options.add_extension(block_videos_path)
        print(f"✅ 成功添加 Block Videos 插件: {block_videos_path}")
    except Exception as e:
        print(f"❌ 添加 Block Videos 插件失败: {e}")
        return False
    
    # 启动浏览器
    print("\n=== 启动浏览器 ===")
    try:
        browser = Chromium(options)
        print("✅ 浏览器启动成功")
        
        # 等待一段时间让插件加载
        await asyncio.sleep(3)
        
        # 获取所有标签页
        tabs = browser.get_tabs()
        print(f"当前标签页数量: {len(tabs)}")
        
        # 打开chrome://extensions页面检查插件
        tab = browser.latest_tab
        tab.get('chrome://extensions/')
        await asyncio.sleep(2)
        
        print("\n=== 检查插件加载状态 ===")
        
        # 检查页面内容
        page_text = tab.html
        if 'live_room' in page_text.lower() or 'Live Room' in page_text:
            print("✅ Live Room 插件已加载")
        else:
            print("❌ Live Room 插件未检测到")
            
        if 'block_videos' in page_text.lower() or 'Block Videos' in page_text:
            print("✅ Block Videos 插件已加载")
        else:
            print("❌ Block Videos 插件未检测到")
        
        # 保持浏览器打开一段时间供手动检查
        print("\n浏览器将保持打开30秒，请手动检查插件状态...")
        await asyncio.sleep(30)
        
        # 关闭浏览器
        browser.quit()
        print("✅ 浏览器已关闭")
        
        return True
        
    except Exception as e:
        print(f"❌ 浏览器启动失败: {e}")
        return False


if __name__ == "__main__":
    print("Chrome插件加载测试工具")
    print("=" * 50)
    
    # 运行测试
    result = asyncio.run(test_extension_loading())
    
    if result:
        print("\n🎉 测试完成")
    else:
        print("\n❌ 测试失败")