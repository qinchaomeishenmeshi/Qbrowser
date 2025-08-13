#!/usr/bin/env python3
# chrome_config_tool.py
# Chrome浏览器路径配置命令行工具

import argparse
import sys
from pathlib import Path
from conf.browser_config import chrome_path_manager
from utils.common_logger import get_logger

logger = get_logger(__name__)

def show_current_config():
    """显示当前Chrome配置"""
    print("\n=== 当前Chrome配置 ===")
    config = chrome_path_manager.get_current_config()
    
    print(f"自定义路径: {config['custom_path'] or '未设置'}")
    print(f"有效路径: {config['effective_path'] or '未找到'}")
    print(f"配置文件: {config['config_file']}")
    print(f"操作系统: {config['platform']}")
    print()

def detect_chrome_browsers():
    """检测系统中可用的Chrome浏览器"""
    print("\n=== 检测Chrome浏览器 ===")
    available_paths = chrome_path_manager.auto_detect_chrome()
    
    if available_paths:
        print(f"找到 {len(available_paths)} 个可用的Chrome浏览器:")
        for i, path in enumerate(available_paths, 1):
            print(f"  {i}. {path}")
    else:
        print("未找到可用的Chrome浏览器")
    print()

def set_chrome_path(path: str):
    """设置Chrome路径"""
    print(f"\n=== 设置Chrome路径 ===")
    
    if not path or path.lower() in ['none', 'null', 'clear', '清除']:
        # 清除自定义路径
        success = chrome_path_manager.set_chrome_path(None)
        if success:
            print("✅ 已清除自定义Chrome路径，将使用系统默认路径")
        else:
            print("❌ 清除Chrome路径失败")
        return
    
    # 设置自定义路径
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"❌ 路径不存在: {path}")
        return
    
    if not path_obj.is_file():
        print(f"❌ 路径不是文件: {path}")
        return
    
    success = chrome_path_manager.set_chrome_path(str(path_obj.resolve()))
    if success:
        print(f"✅ Chrome路径设置成功: {path}")
    else:
        print(f"❌ Chrome路径设置失败: {path}")
    print()

def interactive_setup():
    """交互式设置Chrome路径"""
    print("\n=== Chrome路径交互式配置 ===")
    
    # 显示当前配置
    show_current_config()
    
    # 检测可用浏览器
    available_paths = chrome_path_manager.auto_detect_chrome()
    
    if available_paths:
        print("检测到以下可用的Chrome浏览器:")
        for i, path in enumerate(available_paths, 1):
            print(f"  {i}. {path}")
        print(f"  {len(available_paths) + 1}. 手动输入路径")
        print(f"  {len(available_paths) + 2}. 清除自定义路径")
        print(f"  0. 退出")
        
        while True:
            try:
                choice = input("\n请选择 (输入数字): ").strip()
                
                if choice == '0':
                    print("退出配置")
                    return
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(available_paths):
                    # 选择检测到的路径
                    selected_path = available_paths[choice_num - 1]
                    set_chrome_path(selected_path)
                    break
                elif choice_num == len(available_paths) + 1:
                    # 手动输入路径
                    manual_path = input("请输入Chrome可执行文件的完整路径: ").strip()
                    if manual_path:
                        set_chrome_path(manual_path)
                    break
                elif choice_num == len(available_paths) + 2:
                    # 清除自定义路径
                    set_chrome_path(None)
                    break
                else:
                    print("无效选择，请重新输入")
                    
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n退出配置")
                return
    else:
        print("未检测到可用的Chrome浏览器")
        manual_path = input("请手动输入Chrome可执行文件的完整路径 (回车跳过): ").strip()
        if manual_path:
            set_chrome_path(manual_path)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Chrome浏览器路径配置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python chrome_config_tool.py --show                    # 显示当前配置
  python chrome_config_tool.py --detect                  # 检测可用浏览器
  python chrome_config_tool.py --set "/path/to/chrome"    # 设置Chrome路径
  python chrome_config_tool.py --clear                   # 清除自定义路径
  python chrome_config_tool.py --interactive             # 交互式配置
        """
    )
    
    parser.add_argument('--show', '-s', action='store_true', help='显示当前Chrome配置')
    parser.add_argument('--detect', '-d', action='store_true', help='检测系统中可用的Chrome浏览器')
    parser.add_argument('--set', '-p', metavar='PATH', help='设置Chrome可执行文件路径')
    parser.add_argument('--clear', '-c', action='store_true', help='清除自定义Chrome路径')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互式配置Chrome路径')
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:
        if args.show:
            show_current_config()
        
        if args.detect:
            detect_chrome_browsers()
        
        if args.set:
            set_chrome_path(args.set)
        
        if args.clear:
            set_chrome_path(None)
        
        if args.interactive:
            interactive_setup()
            
    except Exception as e:
        logger.error(f"执行失败: {e}")
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()