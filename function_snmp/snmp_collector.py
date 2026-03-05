"""
SNMP请求封装模块

提供统一的SNMP请求接口，简化SNMP操作的调用方式
"""
import logging
from typing import Optional, Any
from function_snmp.snmpAgent import snmpget
from function_snmp.oid_parser_factory import global_oid_parser_factory

logger = logging.getLogger(__name__)


def snmp_request(ip: str, community: str, oid: str, request_type: str = 'walk', ttl: int = 300) -> Optional[Any]:
    """
    统一的SNMP请求封装函数
    
    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        oid: OID或OID前缀
        request_type: 请求类型，'get'或'walk'
        ttl: 当request_type为'walk'时的缓存有效期（秒）
            设置为0表示不使用缓存
    
    Returns:
        Optional[Any]: 
            - 当request_type为'get'时，返回SNMP GET的原始结果
            - 当request_type为'walk'时，返回通过工厂模式解析后的数据
    
    Raises:
        ValueError: 当request_type无效或OID未注册时抛出
    """
    if request_type == 'get':
        # SNMP GET直接调用snmpAgent的snmpget方法
        logger.debug(f"执行SNMP GET: IP={ip}, OID={oid}")
        return snmpget(ip, community, oid)
    elif request_type == 'walk':
        # SNMP WALK通过工厂模式返回数据
        logger.debug(f"执行SNMP WALK (工厂模式): IP={ip}, OID={oid}, TTL={ttl}秒")
        parser = global_oid_parser_factory.get_parser(oid)
        if not parser:
            error_msg = f"OID {oid} 未注册对应的解析器"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 调用解析器的collect_and_parse方法，传入ttl参数
        return parser.collect_and_parse(ip, community, ttl)
    else:
        raise ValueError(f"无效的request_type: {request_type}，必须为'get'或'walk'")


def snmp_get(ip: str, community: str, oid: str) -> Optional[Any]:
    """
    直接调用SNMP GET操作
    
    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        oid: 完整的OID
    
    Returns:
        Optional[Any]: SNMP GET的原始结果
    """
    return snmp_request(ip, community, oid, request_type='get')


def snmp_walk(ip: str, community: str, oid: str, ttl: int = 300) -> Optional[Any]:
    """
    通过工厂模式执行SNMP WALK操作
    
    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        oid: OID或OID前缀
        ttl: 缓存有效期（秒）
            设置为0表示不使用缓存
    
    Returns:
        Optional[Any]: 解析后的数据
    
    Raises:
        ValueError: 当OID未注册时抛出
    """
    return snmp_request(ip, community, oid, request_type='walk', ttl=ttl)


# 厂商标识符映射，用于自动识别厂商
VENDOR_IDENTIFIERS = {
    'cisco': ['cisco', 'ios', 'catos'],
    'huawei': ['huawei', 'vrp', 'quidway', 'huarong', 'futurematrix'],
    'h3c': ['h3c', '3com', ''],
    'juniper': ['juniper', 'junos'],
    'arista': ['arista', 'eos']
}

def identify_device_vendor(sys_descr: str) -> str:
    """
    根据系统描述自动识别设备厂商

    Args:
        sys_descr: 系统描述字符串

    Returns:
        str: 识别出的厂商名称，默认为'unknown'
    """
    sys_descr_lower = sys_descr.lower() if sys_descr else ''

    for vendor, identifiers in VENDOR_IDENTIFIERS.items():
        for identifier in identifiers:
            if identifier.lower() in sys_descr_lower:
                return vendor

    return 'unknown'

def common_identify_vendor(ip: str, community: str):
    sys_descr = snmp_get(ip, community, "1.3.6.1.2.1.1.1.0")
    if not sys_descr:
        logger.warning("设备{} 采集设备描述失败".format(ip))
        return None
    else:
        vendor = identify_device_vendor(sys_descr)
        return vendor

if __name__ == '__main__':
    import time
    for i in range(2):
        a = snmp_walk("10.10.0.1", "mmmm", "1.3.6.1.2.1.2.2.1.2", ttl=10)
        print(a)