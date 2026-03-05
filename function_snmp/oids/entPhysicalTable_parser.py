"""
设备物理实体表解析器

处理ENTITY-MIB中的entPhysicalTable相关节点
"""
import logging
from function_snmp.oids.base_parsers import CommonIndexParser
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class entPhysicalDescrParser(CommonIndexParser):
    """
    物理实体的详细文本描述
    
    OID: 1.3.6.1.2.1.47.1.1.1.1.2
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.47.1.1.1.1.2", default_ttl, bulk_size)  # entPhysicalDescr


class entPhysicalClassParser(CommonIndexParser):
    """
    物理实体的厂商特定类型
    
    OID: 1.3.6.1.2.1.47.1.1.1.1.5
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.47.1.1.1.1.5", default_ttl, bulk_size)  # entPhysicalClass


class entPhysicalNameParser(CommonIndexParser):
    """
    物理实体的文本名称。
    
    OID: 1.3.6.1.2.1.47.1.1.1.1.7
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.47.1.1.1.1.7", default_ttl, bulk_size)  # entPhysicalName


class entPhysicalSoftwareRevParser(CommonIndexParser):
    """
    物理实体的供应商特定的软件修订字符串。
    
    OID: 1.3.6.1.2.1.47.1.1.1.1.10
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.47.1.1.1.1.10", default_ttl, bulk_size)  # entPhysicalSoftwareRev


class entPhysicalSerialNumParser(CommonIndexParser):
    """
    物理实体的供应商特定序列号字符串。
    
    OID: 1.3.6.1.2.1.47.1.1.1.1.11
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.47.1.1.1.1.11", default_ttl, bulk_size)  # entPhysicalSerialNum


class entPhysicalModelNameParser(CommonIndexParser):
    """
    与该物理组件相关联的供应商特定的型号名称标识符字符串。
    
    OID: 1.3.6.1.2.1.47.1.1.1.1.13
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.47.1.1.1.1.13", default_ttl, bulk_size)  # entPhysicalModelName


# 导出所有解析器类
__all__ = [
    'entPhysicalDescrParser',
    'entPhysicalClassParser',
    'entPhysicalNameParser',
    'entPhysicalSoftwareRevParser',
    'entPhysicalSerialNumParser',
    'entPhysicalModelNameParser'
]