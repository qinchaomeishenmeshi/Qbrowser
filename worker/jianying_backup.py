#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映特效搜索工具
支持输入关键词搜索剪映特效，并将结果保存为JSON文件
"""

import requests
import json
import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed


# 默认配置
DEFAULT_CONFIG = {
    "keywords": ["绿茶", "茶艺", "茶叶"],  # 默认搜索关键词列表
    "effect_type": 5,                   # 特效类型
    "count": 50,                        # 每个关键词返回的结果数量
    "save_full_result": True,           # 是否保存完整结果
    "save_video_urls": True,            # 是否保存视频URL
    "download_videos": False,           # 是否下载视频
    "max_workers": 5,                   # 最大并发下载数
    "save_dir": "data/results/jianying", # 结果保存目录
    "video_dir": "data/video",          # 视频保存目录
    "cookies": {                        # 默认cookies配置
        "store-region": "cn-hb",
        "store-region-src": "uid",
        "n_mh": "8KAIYd9nMFxwSVPpy4XEJKhGL0nyfw_35Nxkilxelck",
        "passport_csrf_token": "311c279e13e613ecc67ce486d0ba89fc",
        "passport_csrf_token_default": "311c279e13e613ecc67ce486d0ba89fc",
        "sid_guard": "fd9ebaee83632608f1ea217f78e4e558%7C1747967643%7C5184000%7CTue%2C+22-Jul-2025+02%3A34%3A03+GMT",
        "uid_tt": "10740e0db45c09735197a4ace7e23f20",
        "uid_tt_ss": "10740e0db45c09735197a4ace7e23f20",
        "sid_tt": "fd9ebaee83632608f1ea217f78e4e558",
        "sessionid": "fd9ebaee83632608f1ea217f78e4e558",
        "sessionid_ss": "fd9ebaee83632608f1ea217f78e4e558",
        "is_staff_user": "false",
        "sid_ucp_v1": "1.0.0-KDMxMTBlNmMzOTA5NjZlNDkzNzNjN2JjNmRiMTM2MmEyM2ZmMTgxZmYKHwiD99C91czNBBCbvb_BBhifrR8gDDCQ-NWyBjgIQCYaAmxmIiBmZDllYmFlZTgzNjMyNjA4ZjFlYTIxN2Y3OGU0ZTU1OA",
        "ssid_ucp_v1": "1.0.0-KDMxMTBlNmMzOTA5NjZlNDkzNzNjN2JjNmRiMTM2MmEyM2ZmMTgxZmYKHwiD99C91czNBBCbvb_BBhifrR8gDDCQ-NWyBjgIQCYaAmxmIiBmZDllYmFlZTgzNjMyNjA4ZjFlYTIxN2Y3OGU0ZTU1OA",
        "_uetvid": "27f18f50f8ac11efafd0f56303409b7b",
        "odin_tt": "fbfde72c09ee8e595b07dcb2ee27f68f31e09d7d61b840ff3a7bb4dd065e3689e9537ceca06b0ec148b103f9f9c5e454d1ae7de4f9b7c2aef70b43499d3a54bc",
        "_tea_web_id": "7397668772687349298",
        "s_v_web_id": "verify_mcburg40_nEP4SLZm_jTgg_4ePs_AD3M_38lbBBofbVEm",
        "COOKIE_CONSENT_PROMPT_CONFIG": "{%22status%22:1%2C%22settings%22:{%22firstPartyAnalytics%22:true%2C%22GoogleAnalytics%22:true}%2C%22updatedTime%22:1750849795438}",
        "ttwid": "1|hMs1clJXG22twhi8wRvpoUzyeaPmKoVyCJxSeR6RhvM|1750849800|7057d47a4f646231d5082ba5d30f95e04f0c2d70bcb96a5ee3f4383fdcd00dab"
    },
    "headers": {                        # 默认headers配置
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.jianying.com",
        "priority": "u=1, i",
        "referer": "https://www.jianying.com/ai-creator/storyboard/23608377858?workspaceId=7397267851037687849&spaceId=7373936382663721254&draftId=881FB5BA-F5DF-4C00-B28C-52E87BAFA205",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }
}


class JianyingEffectSearcher:
    """剪映特效搜索器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化剪映特效搜索器
        
        Args:
            config: 配置字典，默认为None，使用DEFAULT_CONFIG
        """
        # 使用提供的配置或默认配置
        self.config = config if config is not None else DEFAULT_CONFIG
        
        # 设置保存目录
        self.save_dir = self.config.get("save_dir", "data/results/jianying")
        self.video_dir = self.config.get("video_dir", "data/video")
        self.base_url = "https://www.jianying.com/artist/v1/effect/search"
        
        # 确保保存目录存在
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        
        # 从配置中获取cookies和headers
        self.cookies = self.config.get("cookies", DEFAULT_CONFIG["cookies"])
        self.headers = self.config.get("headers", DEFAULT_CONFIG["headers"])
        
        # 基本请求参数
        self.params = {
            "aid": "3704",
            "version_name": "18.1.0",
            "version_code": "11.0.0",
            "sdk_version": "18.1.0",
            "effect_sdk_version": "18.1.0",
            "device_platform": "web",
            "language": "zh-Hans",
            "device_type": "web",
            "channel": "online",
        }
        
    def update_cookies(self, new_cookies: Dict[str, str]) -> None:
        """
        更新cookies配置
        
        Args:
            new_cookies: 新的cookies字典
        """
        if not new_cookies:
            print("提供的cookies为空，不进行更新")
            return
            
        # 更新cookies
        self.cookies.update(new_cookies)
        print(f"已更新 {len(new_cookies)} 个cookies键值对")
        
        # 同时更新配置中的cookies
        self.config["cookies"] = self.cookies
        
    def update_headers(self, new_headers: Dict[str, str]) -> None:
        """
        更新headers配置
        
        Args:
            new_headers: 新的headers字典
        """
        if not new_headers:
            print("提供的headers为空，不进行更新")
            return
            
        # 更新headers
        self.headers.update(new_headers)
        print(f"已更新 {len(new_headers)} 个headers键值对")
        
        # 同时更新配置中的headers
        self.config["headers"] = self.headers
        
    def save_config(self, config_file: str = "config.json") -> bool:
        """
        保存当前配置到文件
        
        Args:
            config_file: 配置文件路径，默认为config.json
            
        Returns:
            保存是否成功
        """
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到 {config_file}")
            return True
        except Exception as e:
            print(f"保存配置文件异常: {e}")
            return False

    def search_single_page(self, 
               keyword: str, 
               effect_type: int = 5, 
               count: int = 50, 
               offset: int = 0, 
               need_recommend: bool = True) -> Dict[str, Any]:
        """
        搜索剪映特效（单页）
        
        Args:
            keyword: 搜索关键词
            effect_type: 特效类型，默认为5
            count: 返回结果数量，默认为50
            offset: 分页偏移量，默认为0
            need_recommend: 是否需要推荐，默认为True
            
        Returns:
            搜索结果字典
        
        Raises:
            requests.RequestException: 请求异常
            ValueError: 参数错误
            Exception: 其他异常
        """
        if not keyword:
            raise ValueError("搜索关键词不能为空")
        
        try:
            # 构建请求数据
            json_data = {
                "effect_type": effect_type,
                "query": keyword,
                "from": "normal_search",
                "need_recommend": need_recommend,
                "search_option": {
                    "cc_web_use_new_search": True
                },
                "pack_optional": {
                    "need_thumb": True,
                    "thumb_opt": '{"is_support_webp":1}'
                },
                "count": count,
                "offset": offset
            }

            # 发送请求
            response = requests.post(
                self.base_url,
                params=self.params,
                cookies=self.cookies,
                headers=self.headers,
                json=json_data,
                timeout=30
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应数据
            result = response.json()
            return result
            
        except requests.RequestException as e:
            print(f"请求异常: {e}")
            raise
        except ValueError as e:
            print(f"参数错误: {e}")
            raise
        except Exception as e:
            print(f"搜索特效时发生异常: {e}")
            raise
            
    def search(self, 
               keyword: str, 
               effect_type: int = 5, 
               count: int = 50, 
               need_recommend: bool = True) -> Dict[str, Any]:
        """
        搜索剪映特效（分页获取全部数据）
        
        Args:
            keyword: 搜索关键词
            effect_type: 特效类型，默认为5
            count: 每页返回结果数量，默认为50
            need_recommend: 是否需要推荐，默认为True
            
        Returns:
            合并后的搜索结果字典
        
        Raises:
            requests.RequestException: 请求异常
            ValueError: 参数错误
            Exception: 其他异常
        """
        import time
        import random
        
        if not keyword:
            raise ValueError("搜索关键词不能为空")
        
        # 初始化结果，用于合并所有页面的数据
        merged_result = None
        offset = 0
        has_more = True
        page_num = 1
        
        try:
            while has_more:
                print(f"获取第 {page_num} 页数据，关键词: {keyword}, offset: {offset}")
                
                # 获取当前页数据
                current_page = self.search_single_page(
                    keyword=keyword,
                    effect_type=effect_type,
                    count=count,
                    offset=offset,
                    need_recommend=need_recommend
                )
                
                # 第一页时初始化合并结果
                if merged_result is None:
                    merged_result = current_page.copy()
                    if 'data' not in merged_result or 'effect_item_list' not in merged_result['data']:
                        print(f"搜索结果数据格式异常")
                        break
                # 否则合并effect_item_list
                elif 'data' in current_page and 'effect_item_list' in current_page['data']:
                    merged_result['data']['effect_item_list'].extend(current_page['data']['effect_item_list'])
                
                # 检查是否有更多数据
                has_more = current_page.get('data', {}).get('has_more', False)
                next_offset = current_page.get('data', {}).get('next_offset', 0)
                
                if has_more and next_offset > offset:
                    offset = next_offset
                    page_num += 1
                    
                    # 添加随机延迟（1-2秒）
                    delay = 1.0 + random.random()
                    print(f"等待 {delay:.2f} 秒后获取下一页...")
                    time.sleep(delay)
                else:
                    # 没有更多数据或offset没有变化，结束循环
                    has_more = False
                    
            print(f"共获取 {page_num} 页数据，关键词: {keyword}")
            
            # 更新合并后的计数信息
            if merged_result and 'data' in merged_result:
                total_items = len(merged_result['data'].get('effect_item_list', []))
                print(f"共获取 {total_items} 条数据")
                
                # 更新数据统计信息
                merged_result['data']['total'] = total_items
                merged_result['data']['has_more'] = False
                merged_result['data']['next_offset'] = 0
            
            return merged_result
            
        except Exception as e:
            print(f"分页搜索特效时发生异常: {e}")
            # 如果已经获取了部分数据，返回已获取的数据
            if merged_result:
                print(f"返回已获取的 {page_num-1} 页数据")
                return merged_result
            raise

    def save_result(self, result: Dict[str, Any], keyword: str, file_name: Optional[str] = None) -> str:
        """
        保存搜索结果到JSON文件
        
        Args:
            result: 搜索结果
            keyword: 搜索关键词
            file_name: 文件名，默认为None，会自动生成
            
        Returns:
            保存的文件路径
            
        Raises:
            IOError: 文件操作异常
            Exception: 其他异常
        """
        try:
            # 如果没有提供文件名，则自动生成
            if not file_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"jianying_effect_{keyword}_{timestamp}.json"
            
            # 确保文件名有.json后缀
            if not file_name.endswith('.json'):
                file_name += '.json'
            
            # 构建完整的文件路径
            file_path = os.path.join(self.save_dir, file_name)
            
            # 保存结果到JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"搜索结果已保存到: {file_path}")
            return file_path
        
        except IOError as e:
            print(f"保存文件异常: {e}")
            raise
        except Exception as e:
            print(f"保存结果时发生异常: {e}")
            raise
    
    def extract_video_urls(self, result: Dict[str, Any], keyword: str, file_name: Optional[str] = None) -> str:
        """
        从搜索结果中提取origin_video的video_url并保存到单独的JSON文件
        
        Args:
            result: 搜索结果
            keyword: 搜索关键词
            file_name: 文件名，默认为None，会自动生成
            
        Returns:
            保存的文件路径
            
        Raises:
            IOError: 文件操作异常
            Exception: 其他异常
        """
        try:
            # 提取所有视频URL
            video_urls = []
            
            if 'data' in result and 'effect_item_list' in result['data']:
                for item in result['data']['effect_item_list']:
                    if 'video' in item and 'origin_video' in item['video']:
                        origin_video = item['video']['origin_video']
                        video_info = {
                            'title': item['common_attr']['title'],
                            'description': item['common_attr']['description'],
                            'video_url': origin_video.get('video_url', ''),
                            'format': origin_video.get('format', ''),
                            'definition': origin_video.get('definition', ''),
                            'height': origin_video.get('height', 0),
                            'width': origin_video.get('width', 0),
                            'size': origin_video.get('size', 0)
                        }
                        video_urls.append(video_info)
            
            # 如果没有提供文件名，则自动生成
            if not file_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"jianying_video_urls_{keyword}_{timestamp}.json"
            
            # 确保文件名有.json后缀
            if not file_name.endswith('.json'):
                file_name += '.json'
            
            # 构建完整的文件路径
            file_path = os.path.join(self.save_dir, file_name)
            
            # 保存视频URL到JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(video_urls, f, ensure_ascii=False, indent=2)
            
            print(f"视频URL已保存到: {file_path}")
            return file_path
        
        except IOError as e:
            print(f"保存视频URL异常: {e}")
            raise
        except Exception as e:
            print(f"提取视频URL时发生异常: {e}")
            raise

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不合法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除不合法字符
        sanitized = re.sub(r'[\\/*?:"<>|]', '', filename)
        # 替换空格为下划线
        sanitized = sanitized.replace(' ', '_')
        # 如果文件名为空，返回默认名称
        if not sanitized:
            return "unnamed_video"
        return sanitized.strip()

    def download_video(self, video_info: Dict[str, Any], keyword: str, index: int) -> str:
        """
        下载单个视频
        
        Args:
            video_info: 视频信息
            keyword: 搜索关键词
            index: 视频索引
            
        Returns:
            下载的文件路径
        
        Raises:
            requests.RequestException: 请求异常
            IOError: 文件操作异常
            Exception: 其他异常
        """
        try:
            # 获取视频URL
            video_url = video_info.get('video_url')
            if not video_url:
                print(f"视频 {index} 没有URL，跳过下载")
                return ""
            
            # 获取视频格式
            video_format = video_info.get('format', 'mp4')
            
            # 确定文件名
            title = video_info.get('title', '').strip()
            if title:
                filename = self.sanitize_filename(title)
            else:
                filename = f"{keyword}_{index}"
            
            # 确保文件名有正确的后缀
            if not filename.endswith(f'.{video_format}'):
                filename += f'.{video_format}'
            
            # 构建完整的文件路径
            # 按关键词创建子目录
            keyword_dir = os.path.join(self.video_dir, self.sanitize_filename(keyword))
            os.makedirs(keyword_dir, exist_ok=True)

            # 构建完整的文件路径
            file_path = os.path.join(keyword_dir, filename)
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                print(f"文件已存在: {file_path}，跳过下载")
                return file_path
            
            # 下载视频
            print(f"正在下载视频: {filename}")
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # 保存视频
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"视频下载完成: {file_path}")
            return file_path
        
        except requests.RequestException as e:
            print(f"下载视频异常: {e}")
            return ""
        except IOError as e:
            print(f"保存视频异常: {e}")
            return ""
        except Exception as e:
            print(f"下载视频时发生异常: {e}")
            return ""

    def download_videos(self, video_urls_file: str, max_workers: int = 5) -> List[str]:
        """
        下载JSON文件中的所有视频
        
        Args:
            video_urls_file: 视频URL文件路径
            max_workers: 最大并发下载数，默认为5
            
        Returns:
            下载的文件路径列表
        
        Raises:
            IOError: 文件操作异常
            Exception: 其他异常
        """
        try:
            # 读取视频URL文件
            with open(video_urls_file, 'r', encoding='utf-8') as f:
                video_urls = json.load(f)
            
            if not video_urls:
                print("没有找到视频URL，跳过下载")
                return []
            
            # 提取关键词
            filename = os.path.basename(video_urls_file)
            match = re.search(r'jianying_video_urls_(.+?)_\d+', filename)
            keyword = match.group(1) if match else "unknown"
            
            downloaded_files = []
            
            # 使用线程池并发下载
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有下载任务
                future_to_index = {
                    executor.submit(self.download_video, video_info, keyword, i): i 
                    for i, video_info in enumerate(video_urls)
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        file_path = future.result()
                        if file_path:
                            downloaded_files.append(file_path)
                    except Exception as e:
                        print(f"下载视频 {index} 失败: {e}")
            
            print(f"共下载 {len(downloaded_files)}/{len(video_urls)} 个视频")
            return downloaded_files
        
        except IOError as e:
            print(f"读取视频URL文件异常: {e}")
            raise
        except Exception as e:
            print(f"下载视频时发生异常: {e}")
            raise

    def search_and_save(self, 
                        keyword: str, 
                        effect_type: int = None, 
                        count: int = None, 
                        save_full_result: bool = None,
                        save_video_urls: bool = None,
                        download_videos: bool = None,
                        file_name: Optional[str] = None,
                        video_urls_file_name: Optional[str] = None,
                        max_workers: int = None) -> Dict[str, Any]:
        """
        搜索并保存结果的便捷方法
        
        Args:
            keyword: 搜索关键词
            effect_type: 特效类型，默认从配置中获取
            count: 每页返回结果数量，默认从配置中获取
            save_full_result: 是否保存完整结果，默认从配置中获取
            save_video_urls: 是否保存视频URL，默认从配置中获取
            download_videos: 是否下载视频，默认从配置中获取
            file_name: 完整结果文件名，默认为None，会自动生成
            video_urls_file_name: 视频URL文件名，默认为None，会自动生成
            max_workers: 最大并发下载数，默认从配置中获取
            
        Returns:
            保存的文件路径和下载的视频文件路径字典
            
        Raises:
            Exception: 任何异常
        """
        try:
            # 使用参数或配置值
            effect_type = effect_type if effect_type is not None else self.config.get("effect_type", 5)
            count = count if count is not None else self.config.get("count", 50)
            save_full_result = save_full_result if save_full_result is not None else self.config.get("save_full_result", True)
            save_video_urls = save_video_urls if save_video_urls is not None else self.config.get("save_video_urls", True)
            download_videos = download_videos if download_videos is not None else self.config.get("download_videos", False)
            max_workers = max_workers if max_workers is not None else self.config.get("max_workers", 5)
            
            print(f"开始搜索关键词 '{keyword}'，自动分页获取全部结果")
            
            # 搜索特效（自动分页获取全部结果）
            result = self.search(keyword, effect_type, count)
            
            # 获取总条数
            total_items = len(result.get('data', {}).get('effect_item_list', []))
            print(f"关键词 '{keyword}' 搜索完成，共获取 {total_items} 条数据")
            
            saved_paths = {}
            
            # 保存完整结果
            if save_full_result:
                full_result_path = self.save_result(result, keyword, file_name)
                saved_paths['full_result_path'] = full_result_path
            
            # 提取并保存视频URL
            if save_video_urls or download_videos:
                video_urls_path = self.extract_video_urls(result, keyword, video_urls_file_name)
                saved_paths['video_urls_path'] = video_urls_path
                
                # 下载视频
                if download_videos:
                    downloaded_files = self.download_videos(video_urls_path, max_workers)
                    saved_paths['downloaded_videos'] = downloaded_files
            
            return saved_paths
        
        except Exception as e:
            print(f"搜索并保存结果时发生异常: {e}")
            import traceback
            traceback.print_exc()
            raise

    def process_multiple_keywords(self) -> Dict[str, Any]:
        """
        处理多个关键词的搜索
        
        Returns:
            所有关键词的处理结果字典
        """
        all_results = {}
        keywords = self.config.get("keywords", ["绿茶"])
        
        for keyword in keywords:
            print(f"\n正在处理关键词: {keyword}")
            try:
                result = self.search_and_save(
                    keyword=keyword,
                    effect_type=self.config.get("effect_type"),
                    count=self.config.get("count"),
                    save_full_result=self.config.get("save_full_result"),
                    save_video_urls=self.config.get("save_video_urls"),
                    download_videos=self.config.get("download_videos"),
                    max_workers=self.config.get("max_workers")
                )
                all_results[keyword] = result
            except Exception as e:
                print(f"处理关键词 '{keyword}' 时发生异常: {e}")
                all_results[keyword] = {"error": str(e)}
        
        return all_results
    
    
    def save_results_only(self) -> Dict[str, str]:
        """
        只搜索并保存结果和视频URL，不下载视频。
        
        Returns:
            Dict[str, str]：关键词对应的 video_urls JSON 文件路径
        """
        all_video_url_paths = {}
        keywords = self.config.get("keywords", ["绿茶"])

        for keyword in keywords:
           print(f"\n🔍 正在处理关键词: {keyword}")
           try:
               result = self.search(keyword)
               self.save_result(result, keyword)
               video_urls_path = self.extract_video_urls(result, keyword)
               all_video_url_paths[keyword] = video_urls_path
           except Exception as e:
               print(f"关键词 '{keyword}' 处理异常: {e}")
               all_video_url_paths[keyword] = None
        return all_video_url_paths
        
    def download_all_videos_from_saved_urls(self, url_paths: Dict[str, str]):
        """
        批量从保存的视频URL JSON文件中下载视频。
    
        Args:
        url_paths: 每个关键词对应的视频URL文件路径
        """
        for keyword, path in url_paths.items():
            if path:
                try:
                    print(f"\n⬇️ 开始下载关键词 '{keyword}' 的视频")
                    self.download_videos(path, self.config.get("max_workers", 5))
                except Exception as e:
                    print(f"关键词 '{keyword}' 下载视频异常: {e}")






def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """
    从JSON文件加载配置
    
    Args:
        config_file: 配置文件路径，默认为config.json
        
    Returns:
        配置字典
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查并记录配置信息
            print(f"已从 {config_file} 加载配置")
            
            # 检查cookies配置
            if "cookies" in config:
                print(f"✓ 已加载cookies配置，包含 {len(config['cookies'])} 个键值对")
            else:
                print("⚠️ 未找到cookies配置，将使用默认cookies")
                config["cookies"] = DEFAULT_CONFIG["cookies"]
            
            # 检查headers配置
            if "headers" in config:
                print(f"✓ 已加载headers配置，包含 {len(config['headers'])} 个键值对")
            else:
                print("⚠️ 未找到headers配置，将使用默认headers")
                config["headers"] = DEFAULT_CONFIG["headers"]
                
            return config
        else:
            print(f"配置文件 {config_file} 不存在，使用默认配置")
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"加载配置文件异常: {e}，使用默认配置")
        return DEFAULT_CONFIG


# 替换原来的 main 函数
def main():
    """主函数：分阶段执行"""
    try:
        # 解析命令行参数
        import argparse
        
        parser = argparse.ArgumentParser(description='剪映特效搜索工具')
        parser.add_argument('-c', '--config', default='/Users/cherishxn/工作项目/2024/短视频生产系统/qw-browser/worker/config.json', help='配置文件路径')
        parser.add_argument('--search-only', action='store_true', help='只搜索并保存结果，不下载视频')
        parser.add_argument('--download-only', action='store_true', help='只从已保存的URL文件下载视频')
        parser.add_argument('--update-cookies', action='store_true', help='更新cookies并保存到配置文件')
        parser.add_argument('--cookies-file', help='从JSON文件加载cookies')
        parser.add_argument('--save-config', action='store_true', help='保存当前配置到文件')
        
        # 添加一个专门的参数来显示配置示例
        parser.add_argument('--show-config-example', action='store_true', help='显示配置文件格式示例')
        
        args = parser.parse_args()
        
        # 显示配置示例
        if args.show_config_example:
            print("配置文件格式示例:")
            print(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2))
            return

        # 加载配置
        config = load_config(args.config)
        searcher = JianyingEffectSearcher(config)
        
        # 更新cookies
        if args.update_cookies:
            if args.cookies_file:
                try:
                    with open(args.cookies_file, 'r', encoding='utf-8') as f:
                        new_cookies = json.load(f)
                    searcher.update_cookies(new_cookies)
                    if args.save_config:
                        searcher.save_config(args.config)
                except Exception as e:
                    print(f"从文件加载cookies异常: {e}")
                    return
            else:
                print("请使用 --cookies-file 参数指定cookies文件路径")
                return
        
        # 保存配置
        if args.save_config and not args.update_cookies:
            searcher.save_config(args.config)
            return
            
        # 只下载视频
        if args.download_only:
            # 查找所有视频URL文件
            import glob
            video_url_files = glob.glob(os.path.join(searcher.save_dir, "jianying_video_urls_*.json"))
            
            if not video_url_files:
                print("未找到视频URL文件，请先运行搜索")
                return
                
            print(f"找到 {len(video_url_files)} 个视频URL文件")
            
            # 构建URL文件路径字典
            url_paths = {}
            for file_path in video_url_files:
                filename = os.path.basename(file_path)
                match = re.search(r'jianying_video_urls_(.+?)_\d+', filename)
                keyword = match.group(1) if match else "unknown"
                url_paths[keyword] = file_path
                
            # 下载视频
            searcher.download_all_videos_from_saved_urls(url_paths)
            return
        
        # 默认行为：搜索并可选下载
        saved_url_paths = searcher.save_results_only()
        
        # 如果配置为下载视频且不是只搜索模式
        if config.get("download_videos", False) and not args.search_only:
            searcher.download_all_videos_from_saved_urls(saved_url_paths)

        # 打印总结
        print("\n处理摘要：")
        for keyword, path in saved_url_paths.items():
            if path:
                print(f"关键词 '{keyword}'：已保存视频 URL 文件 -> {path}")
            else:
                print(f"关键词 '{keyword}'：处理失败")

    except Exception as e:
        print(f"程序执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



if __name__ == "__main__":
    main()

