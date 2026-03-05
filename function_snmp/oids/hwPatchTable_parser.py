"""
接口描述解析器模块

提供接口描述OID解析功能
"""
import logging
from function_snmp.oids.base_parsers import CommonIndexParser

logger = logging.getLogger(__name__)

class hwPatchVersionParser(CommonIndexParser):
    """
    华为补丁采集
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.4.1.2011.5.25.19.1.8.5.1.1.4", default_ttl, bulk_size)  # hwPatchVersion