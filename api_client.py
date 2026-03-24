#!/usr/bin/env python3
"""
智能 API 客户端
支持多端点降级、缓存、重试和监控
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
from dataclasses import dataclass, field
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIType(Enum):
    """API 类型"""
    HACKER_NEWS = "hacker_news"
    GITHUB_TRENDING = "github_trending"
    COMBINED_DAILY = "combined_daily"


@dataclass
class APIEndpoint:
    """API 端点配置"""
    url: str
    name: str
    priority: int = 1  # 优先级，数字越小优先级越高
    timeout: int = 10  # 超时时间（秒）
    retries: int = 2   # 重试次数
    enabled: bool = True
    last_success: Optional[datetime] = None
    failure_count: int = 0
    avg_response_time: float = 0.0
    
    def success_ratio(self) -> float:
        """计算成功率"""
        if self.failure_count == 0:
            return 1.0
        # 简单估算，实际需要更多统计
        return max(0.0, 1.0 - (self.failure_count / 100))
    
    def should_try(self) -> bool:
        """是否应该尝试此端点"""
        if not self.enabled:
            return False
        
        # 如果最近失败太多，暂时禁用
        if self.failure_count > 5:
            # 检查是否需要重新启用（冷却时间）
            if self.last_success:
                time_since_last_success = datetime.now() - self.last_success
                if time_since_last_success < timedelta(minutes=30):
                    return False
                else:
                    # 冷却时间结束，重置失败计数
                    self.failure_count = 0
                    self.enabled = True
                    logger.info(f"端点 {self.name} 冷却结束，重新启用")
        
        return True


class SmartAPIClient:
    """智能 API 客户端"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Clavis-SmartAPIClient/1.0",
            "Accept": "application/json"
        })
        
        # 缓存设置
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # API 端点配置
        self.endpoints: Dict[APIType, List[APIEndpoint]] = {
            APIType.HACKER_NEWS: self._get_hn_endpoints(),
            APIType.GITHUB_TRENDING: self._get_github_endpoints(),
            APIType.COMBINED_DAILY: self._get_daily_endpoints()
        }
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "fallback_used": 0
        }
    
    def _get_hn_endpoints(self) -> List[APIEndpoint]:
        """Hacker News API 端点"""
        return [
            APIEndpoint(
                url="https://hacker-news.firebaseio.com/v0",
                name="Hacker News Firebase API",
                priority=1,
                timeout=15
            ),
            APIEndpoint(
                url="https://clavis-hn-api.citriac.deno.net",
                name="Deno Deploy Hacker News API",
                priority=2,
                timeout=10
            ),
            APIEndpoint(
                url="https://api.hnpwa.com/v0",
                name="HNPWA API",
                priority=3,
                timeout=10
            ),
            APIEndpoint(
                url="https://hacker-news-api.herokuapp.com/api/v1",
                name="Hacker News HeroKu API",
                priority=4,
                timeout=15
            )
        ]
    
    def _get_github_endpoints(self) -> List[APIEndpoint]:
        """GitHub API 端点"""
        return [
            APIEndpoint(
                url="https://api.github.com",
                name="GitHub REST API",
                priority=1,
                timeout=20
            ),
            APIEndpoint(
                url="https://clavis-hn-api.citriac.deno.net",
                name="Deno Deploy GitHub API",
                priority=2,
                timeout=10
            )
        ]
    
    def _get_daily_endpoints(self) -> List[APIEndpoint]:
        """综合日报 API 端点"""
        return [
            APIEndpoint(
                url="https://clavis-hn-api.citriac.deno.net",
                name="Deno Deploy Daily API",
                priority=1,
                timeout=15
            ),
            APIEndpoint(
                url="https://hacker-news.firebaseio.com/v0",
                name="Hacker News Direct + GitHub",
                priority=2,
                timeout=20
            )
        ]
    
    def _get_cached_data(self, cache_key: str, max_age_minutes: int = 60) -> Optional[Dict]:
        """从缓存获取数据"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # 检查缓存是否过期
            file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = datetime.now() - file_mtime
            
            if age > timedelta(minutes=max_age_minutes):
                logger.debug(f"缓存 {cache_key} 已过期 ({age})")
                return None
            
            # 读取缓存数据
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.stats["cache_hits"] += 1
            logger.debug(f"缓存命中: {cache_key}")
            return data
            
        except Exception as e:
            logger.warning(f"读取缓存失败 {cache_key}: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """保存数据到缓存"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"缓存已保存: {cache_key}")
        except Exception as e:
            logger.warning(f"保存缓存失败 {cache_key}: {e}")
    
    def _make_request(self, endpoint: APIEndpoint, path: str = "", 
                     params: Optional[Dict] = None) -> Tuple[bool, Optional[Dict], float]:
        """发起单个请求"""
        url = f"{endpoint.url}/{path}" if path else endpoint.url
        
        try:
            start_time = time.time()
            
            # 构建请求
            request_params = {
                "timeout": endpoint.timeout,
                "params": params
            }
            
            # 移除空参数
            request_params = {k: v for k, v in request_params.items() if v is not None}
            
            response = self.session.get(url, **request_params)
            response_time = time.time() - start_time
            
            # 更新响应时间统计
            if endpoint.avg_response_time == 0:
                endpoint.avg_response_time = response_time
            else:
                endpoint.avg_response_time = (endpoint.avg_response_time * 0.7 + 
                                             response_time * 0.3)
            
            if response.status_code == 200:
                endpoint.last_success = datetime.now()
                endpoint.failure_count = 0
                
                try:
                    data = response.json()
                    return True, data, response_time
                except json.JSONDecodeError:
                    logger.error(f"响应 JSON 解析失败: {url}")
                    return False, None, response_time
            else:
                logger.warning(f"请求失败 {url}: HTTP {response.status_code}")
                endpoint.failure_count += 1
                return False, None, response_time
                
        except requests.exceptions.Timeout:
            logger.warning(f"请求超时: {url}")
            endpoint.failure_count += 1
            return False, None, endpoint.timeout
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求异常 {url}: {e}")
            endpoint.failure_count += 1
            return False, None, 0.0
    
    def fetch_with_fallback(self, api_type: APIType, path: str = "",
                           params: Optional[Dict] = None, use_cache: bool = True,
                           cache_key: Optional[str] = None, 
                           cache_max_age: int = 60) -> Optional[Dict]:
        """使用降级机制获取数据"""
        self.stats["total_requests"] += 1
        
        # 生成缓存键
        if cache_key is None:
            cache_parts = [api_type.value, path or "root"]
            if params:
                cache_parts.append(json.dumps(params, sort_keys=True))
            cache_key = "_".join(cache_parts).replace("/", "_").replace(":", "_")
        
        # 尝试缓存
        if use_cache:
            cached_data = self._get_cached_data(cache_key, cache_max_age)
            if cached_data is not None:
                # 添加缓存标记
                cached_data["_cache"] = {
                    "hit": True,
                    "timestamp": datetime.now().isoformat()
                }
                return cached_data
        
        # 获取端点列表（按优先级排序）
        endpoints = self.endpoints.get(api_type, [])
        endpoints.sort(key=lambda x: (x.priority, x.failure_count))
        
        successful_data = None
        used_fallback = False
        
        for i, endpoint in enumerate(endpoints):
            if not endpoint.should_try():
                continue
            
            logger.info(f"尝试端点 [{i+1}/{len(endpoints)}]: {endpoint.name}")
            
            success, data, response_time = self._make_request(endpoint, path, params)
            
            if success and data:
                self.stats["successful_requests"] += 1
                successful_data = data
                
                # 如果是降级端点，记录统计
                if i > 0:
                    self.stats["fallback_used"] += 1
                    used_fallback = True
                    logger.info(f"使用降级端点: {endpoint.name} (响应时间: {response_time:.2f}s)")
                else:
                    logger.info(f"主端点成功: {endpoint.name} (响应时间: {response_time:.2f}s)")
                
                break
            else:
                logger.warning(f"端点失败: {endpoint.name}")
        
        if successful_data is None:
            self.stats["failed_requests"] += 1
            logger.error(f"所有端点都失败: {api_type.value}")
            return None
        
        # 添加元数据（仅对字典类型）
        if isinstance(successful_data, dict):
            if "_metadata" not in successful_data:
                successful_data["_metadata"] = {}
            
            successful_data["_metadata"].update({
                "api_type": api_type.value,
                "timestamp": datetime.now().isoformat(),
                "used_fallback": used_fallback,
                "client": "SmartAPIClient/1.0"
            })
        
        # 保存到缓存
        if use_cache:
            self._save_to_cache(cache_key, successful_data)
        
        return successful_data
    
    def get_top_hn_stories(self, limit: int = 30) -> Optional[List[int]]:
        """获取 Hacker News 热门故事 ID 列表"""
        # 使用 Firebase API 的特定路径
        result = self.fetch_with_fallback(
            api_type=APIType.HACKER_NEWS,
            path="topstories.json",
            cache_key=f"hn_top_{limit}",
            cache_max_age=15  # HN 数据15分钟缓存
        )
        
        if result and isinstance(result, list):
            return result[:limit]
        return None
    
    def get_hn_item(self, item_id: int) -> Optional[Dict]:
        """获取 Hacker News 单个项目"""
        return self.fetch_with_fallback(
            api_type=APIType.HACKER_NEWS,
            path=f"item/{item_id}.json",
            cache_key=f"hn_item_{item_id}",
            cache_max_age=60  # 单个项目缓存1小时
        )
    
    def get_github_trending(self, days: int = 7, language: str = "", 
                           limit: int = 15) -> Optional[Dict]:
        """获取 GitHub 热门仓库"""
        params = {
            "q": f"created:>{(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')}",
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        if language:
            params["q"] += f" language:{language}"
        
        return self.fetch_with_fallback(
            api_type=APIType.GITHUB_TRENDING,
            path="search/repositories",
            params=params,
            cache_key=f"github_trending_{days}_{language}_{limit}",
            cache_max_age=120  # GitHub 数据2小时缓存
        )
    
    def get_daily_report(self) -> Optional[Dict]:
        """获取综合日报"""
        return self.fetch_with_fallback(
            api_type=APIType.COMBINED_DAILY,
            path="daily",
            cache_key=f"daily_{datetime.now().strftime('%Y-%m-%d')}",
            cache_max_age=360  # 日报缓存6小时
        )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        endpoint_stats = {}
        
        for api_type, endpoints in self.endpoints.items():
            endpoint_stats[api_type.value] = []
            for endpoint in endpoints:
                endpoint_stats[api_type.value].append({
                    "name": endpoint.name,
                    "enabled": endpoint.enabled,
                    "priority": endpoint.priority,
                    "failure_count": endpoint.failure_count,
                    "last_success": endpoint.last_success.isoformat() if endpoint.last_success else None,
                    "avg_response_time": endpoint.avg_response_time,
                    "success_ratio": endpoint.success_ratio()
                })
        
        return {
            "request_stats": self.stats.copy(),
            "endpoint_stats": endpoint_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_endpoint(self, api_type: APIType, endpoint_name: str):
        """重置端点状态"""
        endpoints = self.endpoints.get(api_type, [])
        for endpoint in endpoints:
            if endpoint.name == endpoint_name:
                endpoint.failure_count = 0
                endpoint.enabled = True
                logger.info(f"已重置端点: {endpoint_name}")
                return
        
        logger.warning(f"未找到端点: {endpoint_name}")


# 全局客户端实例
_client_instance: Optional[SmartAPIClient] = None

def get_client() -> SmartAPIClient:
    """获取全局客户端实例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = SmartAPIClient()
    return _client_instance


def main():
    """测试客户端"""
    client = SmartAPIClient()
    
    print("🔍 测试智能 API 客户端...")
    
    # 测试 Hacker News
    print("\n1. 测试 Hacker News API...")
    hn_data = client.get_top_hn_stories(limit=5)
    if hn_data:
        print(f"   ✅ 获取到 {len(hn_data) if isinstance(hn_data, list) else 'data'} 条数据")
    else:
        print("   ❌ 获取失败")
    
    # 测试 GitHub Trending
    print("\n2. 测试 GitHub Trending API...")
    gh_data = client.get_github_trending(days=3, limit=3)
    if gh_data and "items" in gh_data:
        print(f"   ✅ 获取到 {len(gh_data['items'])} 个仓库")
    else:
        print("   ❌ 获取失败")
    
    # 显示统计
    print("\n3. 客户端统计信息:")
    stats = client.get_stats()
    print(f"   总请求数: {stats['request_stats']['total_requests']}")
    print(f"   成功请求: {stats['request_stats']['successful_requests']}")
    print(f"   失败请求: {stats['request_stats']['failed_requests']}")
    print(f"   缓存命中: {stats['request_stats']['cache_hits']}")
    print(f"   降级使用: {stats['request_stats']['fallback_used']}")
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main()