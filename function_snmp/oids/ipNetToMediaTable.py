"""
arp表解析器

"""
import logging
from function_snmp.oids.base_parsers import CommonIndexParser
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ipNetToMediaPhysAddress(CommonIndexParser):
    """
    ip和mac对应关系
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.4.22.1.2", default_ttl, bulk_size, coding="byte")  # ifDescr

    def parse_data(self, raw_data: Dict[str, Any], ip: str, community: str) -> List[Dict[str, Any]]:
        """
        解析mac地址的数据，返回列表形式

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
            byte_data = bytes.fromhex(value)
            # 获取实例索引
            oid_parts = oid.split('.')
            if len(oid_parts) < 1:
                continue

            try:
                # 最后一部分是索引
                index = ".".join(oid_parts[-5:])
                ip_parts = ".".join(oid_parts[-4:])
                port_parts = int(oid_parts[-5])
                result.append({
                    'index': index,
                    'arp_ip': ip_parts,
                    "port_id": port_parts,
                    'value': ':'.join(f"{b:02x}" for b in byte_data),
                    'oid': oid
                })
            except ValueError:
                continue

        # 按索引排序
        result.sort(key=lambda x: x['index'])
        return result