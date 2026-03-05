"""
接口ifTable表解析器

"""
import logging
from function_snmp.oids.base_parsers import CommonIndexParser
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ifDescrParser(CommonIndexParser):
    """
    描述接口的字符串,一般为接口名称
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.2", default_ttl, bulk_size)  # ifDescr


class ifMtuParser(CommonIndexParser):
    """
    接口mtu最大传输单元。接口上可以传送的最大报文的大小，单位是octet。
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.4", default_ttl, bulk_size)  # ifMtu


class ifSpeedParser(CommonIndexParser):
    """
    接口该项为额定带宽值
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.5", default_ttl, bulk_size)  # ifSpeed


class ifPhysAddressParser(CommonIndexParser):
    """
    接口的协议子层对应的接口地址
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.6", default_ttl, bulk_size, coding="byte")  # ifPhysAddress

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
            # 获取实例索引
            oid_parts = oid.split('.')
            if len(oid_parts) < 1:
                continue

            try:
                # 最后一部分是索引
                index = int(oid_parts[-1])
                result.append({
                    'index': index,
                    'value': ':'.join(f"{b:02x}" for b in value),
                    'oid': oid
                })
            except ValueError:
                continue

        # 按索引排序
        result.sort(key=lambda x: x['index'])
        return result

class ifAdminStatusParser(CommonIndexParser):
    """
    接口的管理状态
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.7", default_ttl, bulk_size)  # ifAdminStatus

class ifOperStatusParser(CommonIndexParser):
    """
    接口的管理状态
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.8", default_ttl, bulk_size)  # ifOperStatus


class ifInDiscardsParser(CommonIndexParser):
    """
    接口入向丢包
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.13", default_ttl, bulk_size)  #ifInDiscards

class ifInErrorsParser(CommonIndexParser):
    """
    接口入向错包
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.14", default_ttl, bulk_size)  #ifInErrors


class ifOutDiscardsParser(CommonIndexParser):
    """
    接口出向丢包
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.19", default_ttl, bulk_size)  #ifOutDiscards

class ifOutErrorsParser(CommonIndexParser):
    """
    接口出向错包
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.2.2.1.20", default_ttl, bulk_size)  #ifOutErrors