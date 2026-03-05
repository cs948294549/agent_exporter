"""
OID解析器包

包含所有OID解析器类，可以直接通过import oids访问

该配置项用于对缓存时间进行设置，以及采集的bulk一次性返回条目数量
"""
from typing import Optional, Any, List

# 导入基础解析器类
from function_snmp.oids.base_parsers import OIDParser

# 静态导入ifTable相关的所有解析器类
from function_snmp.oids.ifTable_parser import (
    ifDescrParser,
    ifMtuParser,
    ifInErrorsParser,
    ifOutErrorsParser,
    ifOutDiscardsParser,
    ifInDiscardsParser,
    ifSpeedParser,
    ifOperStatusParser,
    ifAdminStatusParser,
    ifPhysAddressParser
)

# 静态导入ifXTable相关的所有解析器类
from function_snmp.oids.ifXTable_parser import (
    ifHCInOctetsParser,
    ifHCOutOctetsParser,
    ifHCInUcastPktsParser,
    ifHCOutUcastPktsParser,
    ifHCInBroadcastPktsParser,
    ifAliasParser,
    ifHCInMulticastPktsParser,
    ifHCOutMulticastPktsParser,
    ifHighSpeedParser
)

# 静态导入hwPatch相关的所有解析器类
from function_snmp.oids.hwPatchTable_parser import (
    hwPatchVersionParser,
)

# 静态导入entPhysicalTable相关的所有解析器类
from function_snmp.oids.entPhysicalTable_parser import (
    entPhysicalDescrParser,
    entPhysicalClassParser,
    entPhysicalNameParser,
    entPhysicalSoftwareRevParser,
    entPhysicalSerialNumParser,
    entPhysicalModelNameParser
)

# 定义__all__列表，指定可以被导入的公共接口
__all__ = [
    'OIDParser',
    # ifTable相关解析器
    'ifDescrParser',
    'ifMtuParser',
    'ifInErrorsParser',
    'ifOutErrorsParser',
    'ifOutDiscardsParser',
    'ifInDiscardsParser',
    'ifSpeedParser',
    'ifOperStatusParser',
    'ifAdminStatusParser',
    'ifPhysAddressParser',
    # ifXTable相关解析器
    'ifHCInOctetsParser',
    'ifHCOutOctetsParser',
    'ifHCInUcastPktsParser',
    'ifHCOutUcastPktsParser',
    'ifHCInBroadcastPktsParser',
    'ifAliasParser',
    'ifHCInMulticastPktsParser',
    'ifHCOutMulticastPktsParser',
    'ifHighSpeedParser',

    #hwPatch相关解析器
    'hwPatchVersionParser',

     # entPhysicalTable相关解析器
    'entPhysicalDescrParser',
    'entPhysicalClassParser',
    'entPhysicalNameParser',
    'entPhysicalSoftwareRevParser',
    'entPhysicalSerialNumParser',
    'entPhysicalModelNameParser'
]

# 创建解析器名称到解析器类的映射字典
_PARSER_CLASSES = {
    # ifTable相关解析器
    'ifDescrParser': ifDescrParser,
    'ifMtuParser': ifMtuParser,
    'ifInErrorsParser': ifInErrorsParser,
    'ifOutErrorsParser': ifOutErrorsParser,
    'ifOutDiscardsParser': ifOutDiscardsParser,
    'ifInDiscardsParser': ifInDiscardsParser,
    'ifSpeedParser': ifSpeedParser,
    'ifOperStatusParser': ifOperStatusParser,
    'ifAdminStatusParser': ifAdminStatusParser,
    'ifPhysAddressParser': ifPhysAddressParser,
    # ifXTable相关解析器
    'ifHCInOctetsParser': ifHCInOctetsParser,
    'ifHCOutOctetsParser': ifHCOutOctetsParser,
    'ifHCInUcastPktsParser': ifHCInUcastPktsParser,
    'ifHCOutUcastPktsParser': ifHCOutUcastPktsParser,
    'ifHCInBroadcastPktsParser': ifHCInBroadcastPktsParser,
    'ifAliasParser': ifAliasParser,
    'ifHCInMulticastPktsParser': ifHCInMulticastPktsParser,
    'ifHCOutMulticastPktsParser': ifHCOutMulticastPktsParser,
    'ifHighSpeedParser': ifHighSpeedParser,

    # hwPatch相关解析器
    'hwPatchVersionParser': hwPatchVersionParser,
    
    # entPhysicalTable相关解析器
    'entPhysicalDescrParser': entPhysicalDescrParser,
    'entPhysicalClassParser': entPhysicalClassParser,
    'entPhysicalNameParser': entPhysicalNameParser,
    'entPhysicalSoftwareRevParser': entPhysicalSoftwareRevParser,
    'entPhysicalSerialNumParser': entPhysicalSerialNumParser,
    'entPhysicalModelNameParser': entPhysicalModelNameParser

}

def get_parser_by_name(name: str) -> Optional[Any]:
    """
    根据名称获取解析器类
    
    Args:
        name: 解析器名称
        
    Returns:
        解析器类或None（如果不存在）
    """
    # 直接从预定义的映射字典中查找
    return _PARSER_CLASSES.get(name)

def get_all_parsers() -> List[str]:
    """
    获取所有可用的解析器名称
    
    Returns:
        解析器名称列表
    """
    # 直接返回映射字典中的所有键
    return list(_PARSER_CLASSES.keys())