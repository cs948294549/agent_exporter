"""
接口ifXTable表解析器

"""
import logging
from function_snmp.oids.base_parsers import CommonIndexParser

logger = logging.getLogger(__name__)

class ifHCInOctetsParser(CommonIndexParser):
    """
    接口入向流量大小
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.6", default_ttl, bulk_size)  # ifHCInOctets


class ifHCInUcastPktsParser(CommonIndexParser):
    """
    接口入向单播包个数
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.7", default_ttl, bulk_size)  # ifHCInUcastPkts


class ifHCInMulticastPktsParser(CommonIndexParser):
    """
    接口入向组播包个数
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.8", default_ttl, bulk_size)  # ifHCInMulticastPkts


class ifHCInBroadcastPktsParser(CommonIndexParser):
    """
    接口入向广播包个数
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.9", default_ttl, bulk_size)  # ifHCInBroadcastPkts


class ifHCOutOctetsParser(CommonIndexParser):
    """
    接口出向流量大小
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.10", default_ttl, bulk_size)  # ifHCOutOctets


class ifHCOutUcastPktsParser(CommonIndexParser):
    """
    接口出向单播包个数
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.11", default_ttl, bulk_size)  # ifHCOutUcastPkts


class ifHCOutMulticastPktsParser(CommonIndexParser):
    """
    接口出向组播包个数
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.12", default_ttl, bulk_size)  # ifHCOutMulticastPkts

class ifHCOutBroadcastPktsParser(CommonIndexParser):
    """
    接口出向广播包个数
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.13", default_ttl, bulk_size)  # ifHCOutBroadcastPkts

class ifHighSpeedParser(CommonIndexParser):
    """
    接口额定带宽
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.15", default_ttl, bulk_size)  # ifHighSpeed

class ifAliasParser(CommonIndexParser):
    """
    接口描述信息
    """
    def __init__(self, default_ttl: int = 300, bulk_size: int = 10):
        super().__init__("1.3.6.1.2.1.31.1.1.1.18", default_ttl, bulk_size)  # ifAlias

