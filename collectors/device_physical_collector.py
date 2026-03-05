"""
设备物理模块信息采集模块

负责通过SNMP协议采集网络设备的物理模块相关信息，包括模块名称、类型、描述、序号等。
"""
import logging
import time
from typing import Dict, List, Any
from function_snmp.snmp_collector import snmp_walk
from config import Config

logger = logging.getLogger(__name__)

# 定义物理模块相关的SNMP OID
PHYSICAL_MODULE_OIDS = {
    "sn_name": "1.3.6.1.2.1.47.1.1.1.1.2",  # 模块名称
    "sn_type": "1.3.6.1.2.1.47.1.1.1.1.5",  # 模块类型
    "sn_desc": "1.3.6.1.2.1.47.1.1.1.1.7",  # 模块描述
    "sn_number": "1.3.6.1.2.1.47.1.1.1.1.11",  # 模块序号
    "sn_ex": "1.3.6.1.2.1.47.1.1.1.1.13",  # 模块额外信息
}

def collect_physical_module_info(ip: str, community: str) -> Dict[str, Any]:
    """
    采集设备物理模块信息
    
    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        
    Returns:
        Dict[str, Any]: 物理模块信息，包含以下字段：
            - ip: 设备IP地址
            - metric_name: 指标名称
            - status: 采集状态（ok/error）
            - message: 状态消息
            - timestamp: 采集时间戳
            - data: 物理模块信息列表
    """
    try:
        logger.info(f"开始采集设备 {ip} 的物理模块信息")
        
        # 采集所有物理模块相关信息
        results = {}
        for key, oid in PHYSICAL_MODULE_OIDS.items():
            snmp_dat = snmp_walk(ip, community, oid, ttl=600)
            if snmp_dat is not None:
                results[key] = snmp_dat
        
        modules_dict = {}
        for key in results.keys():
            for item in results[key]:
                index = item['index']
                if index not in modules_dict.keys():
                    modules_dict[index] = {
                        "index": index,
                        "sn_name": "",
                        "sn_type": "",
                        "sn_desc": "",
                        "sn_number": "",
                        "sn_ex": ""
                    }

                if index in modules_dict:
                    modules_dict[index][key] = item['value']
                    
        # 转换为列表格式
        modules_list = list(modules_dict.values())
        if len(modules_list) > 0:
            logger.info(f"成功采集设备 {ip} 的 {len(modules_list)} 个物理模块信息")
            return {
                "ip": ip,
                "metric_name": "physical_module",
                "status": "ok",
                "message": "采集成功",
                "timestamp": int(time.time()),
                "data": modules_list
            }
        else:
            logger.info(f"采集设备 {ip} 的 {len(modules_list)} 个物理模块信息")
            return {
                "ip": ip,
                "metric_name": "physical_module",
                "status": "error",
                "message": "采集失败",
                "timestamp": int(time.time()),
                "data": []
            }
    
    except Exception as e:
        logger.error(f"采集设备 {ip} 物理模块信息时出错: {str(e)}", exc_info=True)
        return {
            "ip": ip,
            "metric_name": "physical_module",
            "status": "error",
            "message": str(e),
            "timestamp": time.time(),
            "data": []
        }

# 提供向后兼容的函数
def collect_device_physical_info(ip: str, community: str=Config.common_community) -> Dict[str, Any]:
    """
    采集设备物理信息（向后兼容函数）
    
    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        
    Returns:
        Dict[str, Any]: 物理模块信息
    """
    return collect_physical_module_info(ip, community)

if __name__ == "__main__":
    # 测试代码
    import json

    # 示例使用
    test_ip = "192.168.1.1"
    test_community = "public"

    # 采集接口基础信息
    basic_info = collect_device_physical_info(test_ip, test_community)
    print(json.dumps(basic_info, indent=4, ensure_ascii=False))