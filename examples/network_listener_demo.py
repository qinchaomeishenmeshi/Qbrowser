import asyncio
import time
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.network_listener import EnhancedNetworkListener
from service.browser_service import browser_service
from utils.common_logger import get_logger

logger = get_logger(__name__)


async def demo_specific_url_monitoring():
    """
    演示如何监听特定URL的网络请求
    """
    user_id = "demo_user"
    
    # 获取或创建浏览器实例
    manager = await browser_service.get_or_create_browser(user_id)
    if not manager or not manager.is_running:
        logger.error("浏览器实例创建或运行失败")
        return
        
    browser = manager.browser
    
    # 创建一个新标签页
    tab = browser.new_tab()
    
    try:
        # 创建增强版网络监听器
        network_listener = EnhancedNetworkListener(tab)
        
        # 示例1: 监听特定URL
        specific_url = "api/user/info"
        logger.info(f"开始监听特定URL: {specific_url}")
        
        # 启动监听特定URL
        network_listener.start_listening(specific_url)
        
        # 访问目标页面
        tab.get("https://example.com")
        
        # 等待并捕获匹配的数据包
        packet = network_listener.wait_for_packet(timeout=5)
        if packet:
            logger.info(f"捕获到匹配的数据包: {packet.url}")
            logger.info(f"请求头: {network_listener.get_request_headers(packet)}")
        else:
            logger.info(f"未捕获到匹配 {specific_url} 的数据包")
            
        # 停止监听
        network_listener.stop_listening()
        
        # 示例2: 使用正则表达式监听多个URL
        url_patterns = [
            r"api/.*",  # 匹配所有api路径
            r".*\.json$"  # 匹配所有.json结尾的请求
        ]
        logger.info(f"开始监听多个URL模式: {url_patterns}")
        
        # 启动监听多个URL模式
        network_listener.start_listening(url_patterns)
        
        # 访问目标页面
        tab.get("https://example.com/api/data")
        
        # 实时捕获10秒内的网络请求
        captured_packets = network_listener.start_realtime_capture(duration=10)
        
        logger.info(f"共捕获 {len(captured_packets)} 个匹配的数据包")
        for i, packet in enumerate(captured_packets[:5]):  # 只显示前5个
            logger.info(f"数据包 {i+1}: {packet.url}")
            
        # 示例3: 过滤特定URL的数据包
        filtered_packets = network_listener.filter_by_url("api/user")
        logger.info(f"过滤后的数据包数量: {len(filtered_packets)}")
        
        # 导出捕获的数据包到JSON文件
        export_path = "captured_packets.json"
        if network_listener.export_to_json(export_path):
            logger.info(f"数据包已导出到: {export_path}")
            
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
    finally:
        # 关闭标签页
        tab.close()


async def demo_callback_monitoring():
    """
    演示如何使用回调函数处理捕获的数据包
    """
    user_id = "demo_user"
    
    # 获取或创建浏览器实例
    manager = await browser_service.get_or_create_browser(user_id)
    if not manager or not manager.is_running:
        logger.error("浏览器实例创建或运行失败")
        return
        
    browser = manager.browser
    
    # 创建一个新标签页
    tab = browser.new_tab()
    
    # 定义回调函数
    def packet_callback(packet):
        logger.info(f"实时捕获数据包: {packet.url}")
        if hasattr(packet, 'response') and packet.response:
            logger.info(f"状态码: {packet.response.status_code}")
    
    try:
        # 创建增强版网络监听器
        network_listener = EnhancedNetworkListener(tab)
        
        # 启动监听所有请求，并设置回调函数
        network_listener.start_listening(callback=packet_callback)
        
        # 访问目标页面
        tab.get("https://example.com")
        
        # 等待10秒
        logger.info("等待10秒，观察回调函数处理...")
        time.sleep(10)
            
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
    finally:
        # 停止监听
        network_listener.stop_listening()
        # 关闭标签页
        tab.close()


async def main():
    """
    主函数
    """
    logger.info("=== 增强版网络监听器演示 ===")
    
    # 演示特定URL监听
    logger.info("\n1. 演示特定URL监听")
    await demo_specific_url_monitoring()
    
    # 演示回调函数监听
    logger.info("\n2. 演示回调函数监听")
    await demo_callback_monitoring()
    
    logger.info("\n演示完成")
    

if __name__ == "__main__":
    asyncio.run(main())