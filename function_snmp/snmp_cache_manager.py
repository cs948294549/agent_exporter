"""
SNMP缓存管理器模块

提供SNMP采集数据的缓存管理功能，支持不同OID的TTL设置和线程安全操作
"""
import logging
import time
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SNMPCacheManager:
    """
    SNMP缓存管理器（单例模式）
    
    负责管理所有SNMP采集器共享的缓存数据
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SNMPCacheManager, cls).__new__(cls)
                cls._instance._init_cache()
            return cls._instance
    
    def _init_cache(self):
        """
        初始化缓存相关数据结构
        """
        # 缓存结构: {f"{ip}:{oid}": (value, timestamp)}
        self._cache: Dict[str, tuple] = {}
        # OID特定的TTL映射: {oid_prefix: ttl_seconds}
        self.oid_ttl_map: Dict[str, int] = {}
        # 默认缓存过期时间（秒）
        self.default_cache_ttl = 300
        # 线程锁，用于保护缓存操作的线程安全
        self._cache_lock = threading.RLock()
    
    def _get_cache_key(self, ip: str, community: str, oid: str) -> str:
        """
        生成缓存键
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            oid: 要查询的OID
        
        Returns:
            str: 缓存键，格式为"{ip}:{oid}"
        """
        return f"{ip}:{oid}"
    
    def get_from_cache(self, ip: str, community: str, oid: str, default_ttl: int) -> Optional[Any]:
        """
        从缓存获取OID值（线程安全）
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            oid: 要查询的OID
            default_ttl: 默认TTL值（秒）
        
        Returns:
            Optional[Any]: 缓存的值，如果缓存不存在或已过期则返回None
        """
        cache_key = self._get_cache_key(ip, community, oid)
        with self._cache_lock:
            if cache_key in self._cache:
                value, timestamp = self._cache[cache_key]
                # 获取该OID对应的TTL，如果没有特定设置则使用默认值
                ttl = self._get_oid_ttl(oid, default_ttl)
                # 检查缓存是否过期
                if time.time() - timestamp < ttl:
                    logger.debug(f"从缓存获取设备 {ip} 的OID {oid} 值")
                    return value
                else:
                    # 缓存过期，删除
                    del self._cache[cache_key]
                    logger.debug(f"设备 {ip} 的OID {oid} 缓存已过期并删除")
        return None
    
    def set_to_cache(self, ip: str, community: str, oid: str, value: Any):
        """
        将OID值存入缓存（线程安全）
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            oid: 查询的OID
            value: 获取到的值
        """
        cache_key = self._get_cache_key(ip, community, oid)
        with self._cache_lock:
            self._cache[cache_key] = (value, time.time())
            logger.debug(f"将设备 {ip} 的OID {oid} 值存入缓存")
    
    def _get_oid_ttl(self, oid: str, default_ttl: int) -> int:
        """
        获取OID对应的TTL值（线程安全）
        
        Args:
            oid: 查询的OID
            default_ttl: 默认TTL值（秒）
        
        Returns:
            int: TTL值（秒）
        """
        with self._cache_lock:
            # 查找匹配的OID前缀
            for oid_prefix, ttl in sorted(self.oid_ttl_map.items(), key=lambda x: len(x[0]), reverse=True):
                if oid.startswith(oid_prefix):
                    return ttl
        # 如果没有匹配的特定OID前缀，返回默认TTL
        return default_ttl
    
    def set_oid_ttl(self, oid_prefix: str, ttl: int):
        """
        为特定OID前缀设置TTL（线程安全）
        
        Args:
            oid_prefix: OID前缀
            ttl: TTL值（秒）
        """
        if ttl <= 0:
            logger.warning(f"TTL值必须大于0，当前值: {ttl}")
            return
        
        with self._cache_lock:
            self.oid_ttl_map[oid_prefix] = ttl
            logger.debug(f"为OID前缀 {oid_prefix} 设置TTL: {ttl}秒")
    
    def clear_specific_oid(self, ip: Optional[str], community: Optional[str], oid: str):
        """
        清除特定OID的缓存（线程安全）
        
        Args:
            ip: 可选，指定IP地址，为None时清除所有IP的该OID缓存
            community: 可选，指定团体字符串（保留参数以保持API兼容性）
            oid: 要清除的OID
        """
        with self._cache_lock:
            if ip is None:
                # 清除所有IP的特定OID缓存
                keys_to_remove = [k for k in self._cache.keys() if k.endswith(f":{oid}")]
            else:
                # 清除特定IP的特定OID缓存
                specific_key = f"{ip}:{oid}"
                keys_to_remove = [specific_key] if specific_key in self._cache else []
            
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"已清除OID {oid} 的缓存，共 {len(keys_to_remove)} 条记录")
    
    def clear_cache(self, ip: Optional[str] = None, community: Optional[str] = None):
        """
        清除缓存（线程安全）
        
        Args:
            ip: 可选，指定IP地址，为None时清除所有IP的缓存
            community: 可选，指定团体字符串（保留参数以保持API兼容性）
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


# 创建全局缓存管理器实例
_snmp_cache_manager = SNMPCacheManager()


def get_cache_manager() -> SNMPCacheManager:
    """
    获取全局SNMP缓存管理器实例
    
    Returns:
        SNMPCacheManager: 全局缓存管理器实例
    """
    return _snmp_cache_manager