"""
采集器缓存管理器模块

提供通用数据采集的缓存管理功能，支持不同采集类型的TTL设置和线程安全操作
适用于多线程环境下的采集器共享缓存管理
支持定期自动清理过期缓存数据
"""
import logging
import time
import threading
from typing import Dict, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class CollectorCacheManager:
    """
    采集器缓存管理器（单例模式）
    
    负责管理所有数据采集器共享的缓存数据，支持多线程环境下的安全操作
    自动定期清理过期的缓存数据
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CollectorCacheManager, cls).__new__(cls)
                cls._instance._init_cache()
            return cls._instance
    
    def _init_cache(self):
        """
        初始化缓存相关数据结构
        """
        # 缓存结构: {cache_key: (value, timestamp, ttl)}  
        # cache_key格式为: "{ip}:{collector_type}:{metric_name}"
        # ttl为该缓存的存活时间（秒）
        self._cache: Dict[str, Tuple[Any, float, int]] = {}
        
        # 采集类型特定的TTL映射: {collector_type: ttl_seconds}
        self.collector_ttl_map: Dict[str, int] = {}
        
        # 指标特定的TTL映射: {f"{collector_type}:{metric_pattern}": ttl_seconds}
        self.metric_ttl_map: Dict[str, int] = {}
        
        # 默认缓存过期时间（秒）
        self.default_cache_ttl = 600
        
        # 线程锁，用于保护缓存操作的线程安全
        self._cache_lock = threading.RLock()
        
        # 清理间隔（秒）
        self.cleanup_interval = 60
        
        # 启动定期清理线程
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """
        启动后台定期清理线程
        """
        self._stop_cleanup = False
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_task,
            daemon=True,
            name="CollectorCacheCleanup"
        )
        self._cleanup_thread.start()
        logger.debug("已启动缓存定期清理线程")
    
    def _cleanup_task(self):
        """
        定期清理过期缓存的后台任务
        """
        while not self._stop_cleanup:
            try:
                # 执行清理操作
                self._cleanup_expired_cache()
                
                # 等待下一次清理
                for _ in range(self.cleanup_interval):
                    if self._stop_cleanup:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"缓存清理任务执行出错: {str(e)}", exc_info=True)
                # 出错后等待10秒再继续，避免频繁报错
                time.sleep(10)
    
    def _cleanup_expired_cache(self):
        """
        清理所有过期的缓存项（线程安全）
        """
        current_time = time.time()
        expired_keys = []
        
        with self._cache_lock:
            # 找出所有过期的缓存键
            for cache_key, (_, timestamp, ttl) in self._cache.items():
                if current_time - timestamp > ttl:
                    expired_keys.append(cache_key)
            
            # 删除过期的缓存项
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"已清理 {len(expired_keys)} 个过期缓存项")
    
    def stop_cleanup(self):
        """
        停止清理线程（用于优雅关闭）
        """
        self._stop_cleanup = True
        if hasattr(self, '_cleanup_thread') and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2.0)
            logger.debug("已停止缓存定期清理线程")
    
    def _get_cache_key(self, ip: str, collector_type: str, metric_name: str) -> str:
        """
        生成缓存键
        
        Args:
            ip: 设备IP地址
            collector_type: 采集器类型（如'snmp', 'ssh', 'api'等）
            metric_name: 指标名称或标识符
        
        Returns:
            str: 缓存键，格式为"{ip}:{collector_type}:{metric_name}"
        """
        return f"{ip}:{collector_type}:{metric_name}"
    
    def get_from_cache(self, ip: str, collector_type: str, metric_name: str) -> Optional[Any]:
        """
        从缓存获取指标值（线程安全）
        
        Args:
            ip: 设备IP地址
            collector_type: 采集器类型
            metric_name: 指标名称
        
        Returns:
            Optional[Any]: 缓存的值，如果缓存不存在或已过期则返回None
        """
        cache_key = self._get_cache_key(ip, collector_type, metric_name)
        current_time = time.time()
        
        with self._cache_lock:
            if cache_key in self._cache:
                value, timestamp, ttl = self._cache[cache_key]
                
                # 检查缓存是否过期（使用存储时的TTL）
                if current_time - timestamp < ttl:
                    logger.debug(f"从缓存获取设备 {ip} 的{collector_type}类型指标 {metric_name} 值")
                    return value
                else:
                    # 缓存过期，删除
                    del self._cache[cache_key]
                    logger.debug(f"设备 {ip} 的{collector_type}类型指标 {metric_name} 缓存已过期并删除")
        return None
    
    def set_to_cache(self, ip: str, collector_type: str, metric_name: str, value: Any, 
                    ttl: Optional[int] = None):
        """
        将指标值存入缓存（线程安全）
        
        Args:
            ip: 设备IP地址
            collector_type: 采集器类型
            metric_name: 指标名称
            value: 获取到的值
            ttl: 可选，指定缓存存活时间（秒），如果为None则使用自动计算的TTL
        """
        cache_key = self._get_cache_key(ip, collector_type, metric_name)
        current_time = time.time()
        
        # 如果没有指定TTL，则自动计算
        if ttl is None:
            ttl = self._get_appropriate_ttl(collector_type, metric_name, self.default_cache_ttl)
        
        with self._cache_lock:
            self._cache[cache_key] = (value, current_time, ttl)
            logger.debug(f"将设备 {ip} 的{collector_type}类型指标 {metric_name} 值存入缓存，TTL={ttl}秒")
    
    def _get_appropriate_ttl(self, collector_type: str, metric_name: str, 
                            default_ttl: int) -> int:
        """
        获取适用于特定采集器类型和指标名称的TTL值（线程安全）
        
        Args:
            collector_type: 采集器类型
            metric_name: 指标名称
            default_ttl: 默认TTL值（秒）
        
        Returns:
            int: TTL值（秒）
        """
        with self._cache_lock:
            # 1. 首先查找是否有完全匹配的指标TTL设置
            exact_metric_key = f"{collector_type}:{metric_name}"
            if exact_metric_key in self.metric_ttl_map:
                return self.metric_ttl_map[exact_metric_key]
            
            # 2. 查找是否有匹配的指标模式（模糊匹配）
            for metric_pattern, ttl in sorted(self.metric_ttl_map.items(), 
                                            key=lambda x: len(x[0]), reverse=True):
                # 检查是否是以相同采集器类型开头，并且指标名称包含模式部分
                if metric_pattern.startswith(f"{collector_type}:"):
                    pattern_part = metric_pattern.split(":", 1)[1]
                    if pattern_part in metric_name:
                        return ttl
            
            # 3. 查找是否有采集器类型特定的TTL设置
            if collector_type in self.collector_ttl_map:
                return self.collector_ttl_map[collector_type]
        
        # 如果以上都没有匹配的，返回默认TTL
        return default_ttl
    
    def set_collector_ttl(self, collector_type: str, ttl: int):
        """
        为特定采集器类型设置TTL（线程安全）
        
        Args:
            collector_type: 采集器类型
            ttl: TTL值（秒）
        """
        if ttl <= 0:
            logger.warning(f"TTL值必须大于0，当前值: {ttl}")
            return
        
        with self._cache_lock:
            self.collector_ttl_map[collector_type] = ttl
            logger.debug(f"为采集器类型 {collector_type} 设置TTL: {ttl}秒")
    
    def set_metric_ttl(self, collector_type: str, metric_pattern: str, ttl: int):
        """
        为特定采集器类型的指标模式设置TTL（线程安全）
        
        Args:
            collector_type: 采集器类型
            metric_pattern: 指标模式（可以是精确指标名称或部分模式）
            ttl: TTL值（秒）
        """
        if ttl <= 0:
            logger.warning(f"TTL值必须大于0，当前值: {ttl}")
            return
        
        with self._cache_lock:
            metric_key = f"{collector_type}:{metric_pattern}"
            self.metric_ttl_map[metric_key] = ttl
            logger.debug(f"为采集器类型 {collector_type} 的指标模式 {metric_pattern} 设置TTL: {ttl}秒")
    
    def clear_specific_metric(self, ip: Optional[str], collector_type: str, metric_name: str):
        """
        清除特定指标的缓存（线程安全）
        
        Args:
            ip: 可选，指定IP地址，为None时清除所有IP的该指标缓存
            collector_type: 采集器类型
            metric_name: 要清除的指标名称
        """
        with self._cache_lock:
            if ip is None:
                # 清除所有IP的特定指标缓存
                keys_to_remove = [k for k in self._cache.keys() 
                                if k.endswith(f":{collector_type}:{metric_name}")]
            else:
                # 清除特定IP的特定指标缓存
                specific_key = self._get_cache_key(ip, collector_type, metric_name)
                keys_to_remove = [specific_key] if specific_key in self._cache else []
            
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"已清除{collector_type}类型指标 {metric_name} 的缓存，共 {len(keys_to_remove)} 条记录")
    
    def clear_collector_cache(self, ip: Optional[str], collector_type: str):
        """
        清除特定采集器类型的缓存（线程安全）
        
        Args:
            ip: 可选，指定IP地址，为None时清除所有IP的该采集器类型缓存
            collector_type: 采集器类型
        """
        with self._cache_lock:
            if ip is None:
                # 清除所有IP的特定采集器类型缓存
                keys_to_remove = [k for k in self._cache.keys() 
                                if f":{collector_type}:" in k]
            else:
                # 清除特定IP的特定采集器类型缓存
                prefix = f"{ip}:{collector_type}:"
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"已清除采集器类型 {collector_type} 的缓存，共 {len(keys_to_remove)} 条记录")
    
    def clear_cache(self, ip: Optional[str] = None):
        """
        清除缓存（线程安全）
        
        Args:
            ip: 可选，指定IP地址，为None时清除所有IP的缓存
        """
        with self._cache_lock:
            if ip is None:
                # 清除所有缓存
                self._cache.clear()
                logger.debug("已清除所有缓存")
            else:
                # 清除指定IP的所有缓存
                prefix = f"{ip}:"
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
                
                for key in keys_to_remove:
                    del self._cache[key]
                logger.debug(f"已清除设备 {ip} 的缓存，共 {len(keys_to_remove)} 条记录")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息（线程安全）
        
        Returns:
            Dict[str, Any]: 缓存统计信息，包含：
                - total_entries: 缓存条目总数
                - collector_types: 不同采集器类型的缓存条目数
                - oldest_entry: 最早的缓存条目时间戳
                - newest_entry: 最新的缓存条目时间戳
                - expired_entries: 当前过期但未清理的条目数
                - avg_ttl: 平均TTL值（秒）
        """
        current_time = time.time()
        
        with self._cache_lock:
            stats = {
                'total_entries': len(self._cache),
                'collector_types': {},
                'oldest_entry': None,
                'newest_entry': None,
                'expired_entries': 0,
                'avg_ttl': 0.0
            }
            
            if self._cache:
                timestamps = []
                ttl_values = []
                expired_count = 0
                
                # 统计不同采集器类型的条目数
                for key, (_, timestamp, ttl) in self._cache.items():
                    _, collector_type, _ = key.split(':', 2)
                    stats['collector_types'][collector_type] = \
                        stats['collector_types'].get(collector_type, 0) + 1
                    
                    timestamps.append(timestamp)
                    ttl_values.append(ttl)
                    
                    # 计算过期条目数
                    if current_time - timestamp > ttl:
                        expired_count += 1
                
                # 找出最早和最新的缓存条目
                stats['oldest_entry'] = min(timestamps)
                stats['newest_entry'] = max(timestamps)
                stats['expired_entries'] = expired_count
                stats['avg_ttl'] = sum(ttl_values) / len(ttl_values) if ttl_values else 0.0
            
            return stats
    
    def set_cleanup_interval(self, interval_seconds: int):
        """
        设置缓存清理间隔
        
        Args:
            interval_seconds: 清理间隔（秒），最小为5秒
        """
        if interval_seconds < 5:
            logger.warning(f"清理间隔不能小于5秒，当前值: {interval_seconds}，已调整为5秒")
            interval_seconds = 5
        
        with self._cache_lock:
            self.cleanup_interval = interval_seconds
            logger.debug(f"已设置缓存清理间隔为 {interval_seconds} 秒")
    
    def force_cleanup(self):
        """
        强制立即执行一次缓存清理（线程安全）
        """
        logger.debug("执行强制缓存清理")
        self._cleanup_expired_cache()
        return self.get_cache_stats()


# 创建全局缓存管理器实例
_collector_cache_manager = CollectorCacheManager()

def get_cache_manager() -> CollectorCacheManager:
    """
    获取全局采集器缓存管理器实例
    
    Returns:
        CollectorCacheManager: 全局缓存管理器实例
    """
    return _collector_cache_manager