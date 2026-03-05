"""
OID解析器基类模块

提供OID解析器的基础实现
"""
import logging
import time
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from function_snmp.snmpAgent import snmpwalk
from function_snmp.snmp_cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

# 获取全局缓存管理器实例
_snmp_cache_manager = get_cache_manager()

MTU = 1500

class OIDParser(ABC):
    """
    OID解析器基类
    
    提供OID数据采集和解析功能的抽象基类
    子类需要实现parse_data方法来解析特定OID返回的数据
    """
    
    def __init__(self, oid_prefix: str, default_ttl: int = 300, bulk_size: int = 10, coding="utf-8"):
        """
        初始化OID解析器
        
        Args:
            oid_prefix: 要解析的OID前缀
            default_ttl: 默认缓存过期时间（秒）
        """
        self.oid_prefix = oid_prefix
        self.default_ttl = default_ttl
        self.bulk_size = bulk_size
        self.coding = coding

        # 设置该OID前缀的TTL
        _snmp_cache_manager.set_oid_ttl(oid_prefix, default_ttl)
    
    def collect_and_parse(self, ip: str, community: str, ttl: int = 300) -> Optional[Any]:
        """
        采集并解析OID数据
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            ttl: 缓存有效期（秒），直接判断当前时间与采集时间的差是否小于ttl
                若小于则使用缓存，大于则更新数据
                设置为0表示不使用缓存
            
        Returns:
            Optional[Any]: 解析后的数据
        """
        try:
            # 尝试从缓存获取解析后的数据和时间戳
            cache_key_suffix = f"_parsed"
            cache_key = f"{ip}:{community}:{self.oid_prefix}{cache_key_suffix}"
            
            # 直接访问缓存字典检查缓存
            use_cache = ttl > 0
            if use_cache:
                with _snmp_cache_manager._cache_lock:
                    if cache_key in _snmp_cache_manager._cache:
                        cached_parsed_data, timestamp = _snmp_cache_manager._cache[cache_key]
                        # 直接判断当前时间与缓存时间的差是否小于ttl
                        if time.time() - timestamp < ttl:
                            logger.debug(f"解析后数据命中缓存: IP={ip}, OID={self.oid_prefix}, TTL={ttl}秒")
                            return cached_parsed_data
                        else:
                            logger.debug(f"缓存过期，需要更新: IP={ip}, OID={self.oid_prefix}, 缓存时间={timestamp}, 当前时间={time.time()}")
            
            # 缓存未命中、过期或不使用缓存，直接执行SNMP WALK获取原始数据
            logger.debug(f"执行SNMP WALK: IP={ip}, OID={self.oid_prefix}")
            mtu_bulk_size = int(self.bulk_size/1500*MTU)

            raw_data = snmpwalk(ip, community, self.oid_prefix, bulk_size=mtu_bulk_size, coding=self.coding)
            
            if raw_data is None:
                logger.warning(f"设备 {ip} 的OID {self.oid_prefix} 数据采集失败")
                return None
            
            # 调用子类实现的解析方法
            parsed_data = self.parse_data(raw_data, ip, community)
            
            # 缓存解析后的数据
            if use_cache and parsed_data is not None:
                with _snmp_cache_manager._cache_lock:
                    _snmp_cache_manager._cache[cache_key] = (parsed_data, time.time())
                logger.debug(f"解析后数据已缓存: IP={ip}, OID={self.oid_prefix}, TTL={ttl}秒")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"处理设备 {ip} 的OID {self.oid_prefix} 数据时发生错误: {str(e)}", exc_info=True)
            return None
    
    @abstractmethod
    def parse_data(self, raw_data: Dict[str, Any], ip: str, community: str) -> Any:
        """
        解析OID返回的原始数据（虚函数，需要由子类实现）
        
        Args:
            raw_data: SNMP WALK返回的原始数据字典
            ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            Any: 解析后的数据
        """
        pass



class CommonIndexParser(OIDParser):
    """
    通用的OID解析器（单节点）
    解析单个属性节点（例如接口描述），返回列表形式的数据
    用于处理最后一位是index的列表，大部分都是该类型
    """

    def parse_data(self, raw_data: Dict[str, Any], ip: str, community: str) -> List[Dict[str, Any]]:
        """
        解析单个OID节点的数据，返回列表形式

        Args:
            raw_data: SNMP WALK返回的原始数据
            ip: 设备IP地址
            community: SNMP团体字符串

        Returns:
            List[Dict[str, Any]]: 解析后的列表数据，每个元素包含索引和值
        """
        result = []

        # 解析原始数据为列表形式
        for oid, value in raw_data.items():
            # 获取实例索引
            oid_parts = oid.split('.')
            if len(oid_parts) < 1:
                continue

            try:
                # 最后一部分是索引
                index = int(oid_parts[-1])
                result.append({
                    'index': index,
                    'value': value,
                    'oid': oid
                })
            except ValueError:
                continue

        # 按索引排序
        result.sort(key=lambda x: x['index'])
        return result