#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设备信息采集模块

负责通过SNMP协议采集网络设备的基础信息，支持多种设备型号的适配
采用可扩展的策略模式设计，便于添加新的厂商支持
"""
import logging
import re
import time
from typing import Dict, List, Any, Optional, Protocol
from function_snmp.snmp_collector import snmp_get, snmp_walk, identify_device_vendor

logger = logging.getLogger(__name__)

# 设备基础信息OID映射（标准MIB）
STANDARD_OIDS = {
    # 系统描述
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    # 系统名称
    'sysName': '1.3.6.1.2.1.1.5.0',
    # 系统位置
    'sysLocation': '1.3.6.1.2.1.1.6.0',
    # 系统联系信息
    'sysContact': '1.3.6.1.2.1.1.4.0',
    # 系统对象ID（厂商信息）
    'sysObjectID': '1.3.6.1.2.1.1.2.0',
    # 系统启动时间
    'sysUpTime': '1.3.6.1.2.1.1.3.0'
}

# 厂商特定OID映射
VENDOR_OIDS = {
    # Cisco特定OID
    'cisco': {
    },
    # Huawei特定OID
    'huawei': {
        'hwPatchInstall': '1.3.6.1.4.1.2011.5.25.19.1.8.5.1.1.4',
    },
    # H3C特定OID
    'h3c': {
    },
    # Juniper特定OID
    'juniper': {
    }
}

class DeviceInfoCollectorStrategy(Protocol):
    """
    设备信息采集策略接口
    所有厂商特定的采集策略需要实现这个接口
    """
    
    def collect_vendor_specific_info(self, ip: str, community: str) -> Dict[str, str]:
        """
        采集厂商特定的设备信息（model、version、patch）
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            Dict[str, str]: 包含model、version、patch字段的字典
        """
        ...
    
    def extract_model(self, sys_descr: str) -> Dict[str, str]:
        """
        从系统描述中提取设备型号
        
        Args:
            sys_descr: 系统描述字符串
            
        Returns:
            str: 提取的设备型号
        """
        ...


class DefaultDeviceInfoCollector:
    """
    默认设备信息采集策略
    用于处理未知厂商或不需要特殊处理的情况
    """
    
    def __init__(self, vendor: str = 'unknown'):
        self.vendor = vendor
    
    def collect_vendor_specific_info(self, ip: str, community: str) -> Dict[str, str]:
        """
        采集默认的厂商特定信息（model、version、patch）
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            Dict[str, str]: 默认返回空的model、version、patch
        """
        return {
            'hardware': '',
            'version': '',
            'patch': ''
        }
    
    def extract_model(self, sys_descr: str) -> Dict[str, str]:
        """
        从系统描述中提取设备型号（默认实现）
        
        Args:
            sys_descr: 系统描述字符串
            
        Returns:
            str: 默认返回'Unknown'
        """
        return {
            'hardware': '',
            'version': '',
            'patch': ''
        }


class CiscoDeviceInfoCollector:
    """
    Cisco设备信息采集策略
    """
    
    def collect_vendor_specific_info(self, ip: str, community: str) -> Dict[str, str]:
        """
        采集Cisco特定的设备信息（model、version、patch）
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            Dict[str, str]: 包含model、version、patch字段的字典
        """
        return {
            'hardware': '',
            'version': '',
            'patch': ''
        }

    
    def extract_model(self, sys_descr: str) -> Dict[str, str]:
        """
        从系统描述中提取Cisco设备型号
        
        Args:
            sys_descr: 系统描述字符串
            
        Returns:
            str: 提取的设备型号
        """
        # 尝试从描述中匹配Cisco设备型号
        model_patterns = [
            r'Cisco\s+(\w+\d+\w*(-\w+)?(\s+\w+)?(\s+\w+)?)\s+software',
            r'cisco\s+(\w+\d+\w*(-\w+)?(\s+\w+)?(\s+\w+)?)\s+software',
            r'Cisco\s+(\w+\d+\w*(-\w+)?(\s+\w+)?(\s+\w+)?)\s+\(\w+\)',
            r'cisco\s+(\w+\d+\w*(-\w+)?(\s+\w+)?(\s+\w+)?)\s+\(\w+\)',
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, sys_descr, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return {
            'hardware': '',
            'version': '',
            'patch': ''
        }


class HuaweiDeviceInfoCollector:
    """
    Huawei设备信息采集策略
    """
    
    def collect_vendor_specific_info(self, ip: str, community: str) -> Dict[str, str]:
        """
        采集Huawei特定的设备信息（model、version、patch）
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            Dict[str, str]: 包含model、version、patch字段的字典
        """
        hardware = ''
        version = ''
        patch = ''
        
        huawei_oids = VENDOR_OIDS.get('huawei', {})
        
        # 采集华为设备型号
        patch_array = snmp_walk(ip, community, huawei_oids.get('hwPatchInstall'))
        if patch_array:
            patch = list(patch_array.values())[0]
            if patch is not None:
                patch = patch.decode("utf-8", "ignore")
                if patch.strip() == "None":
                    patch = ""
            else:
                patch = ""
        return {
            'hardware': hardware,
            'version': version,
            'patch': patch
        }
    
    def extract_model(self, sys_descr: str) -> Dict[str, str]:
        """
        从系统描述中提取Huawei设备型号
        
        Args:
            sys_descr: 系统描述字符串
            
        Returns:
            str: 提取的设备型号
        """
        # 尝试从描述中匹配华为设备型号
        reg_patch = re.compile(r'Version\s+(?:\S+)\s+\(?([^)]+)\)?')
        reg_model = re.compile(r'(?:(?:HUAWEI)|(?:Huarong)|(?:FUTUREMATRIX))\s*((?:\S+-)+\S+)', re.I)
        desc_array = sys_descr.split("\n")
        if "\n" in sys_descr:
            hardware = desc_array[0].strip()
            if "HUAWEI" in hardware.upper() or "HUARONG" in hardware.upper() or "FUTUREMATRIX" in hardware.upper():
                hardware = ""
        else:
            hardware = ""

        version_array = reg_patch.findall(sys_descr)
        version = ""
        if len(version_array) > 0:
            version_str = version_array[0]
            version = version_str.split()[1]
            if version_str.split()[0].upper() not in hardware.upper():
                mode_array = reg_model.findall(sys_descr)
                if len(mode_array) > 0:
                    hardware = mode_array[0]
                else:
                    hardware = version_str.split()[0]

        return {
            'hardware': hardware,
            'version': version,
            'patch': ""
        }


class H3CDeviceInfoCollector:
    """
    H3C设备信息采集策略
    """
    
    def collect_vendor_specific_info(self, ip: str, community: str) -> Dict[str, str]:
        """
        采集H3C特定的设备信息（model、version、patch）
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            Dict[str, str]: 包含model、version、patch字段的字典
        """
        return {'hardware': '','version': '','patch': ''}
    
    def extract_model(self, sys_descr: str) -> Dict[str, str]:
        """
        从系统描述中提取H3C设备型号
        
        Args:
            sys_descr: 系统描述字符串
            
        Returns:
            str: 提取的设备型号
        """
        # 尝试从描述中匹配H3C设备型号

        hardware = ''
        version = ''
        patch = ''

        reg_model = re.compile(r'Version\s+\S+.+((?:Release)|(?:Feature)\s+\S+)[\s\S]+H3C\s+(\S+)[\s\S]+Copyright', re.I)
        hardware_array = reg_model.findall(sys_descr)
        if len(hardware_array) > 0:
            hardware_info = hardware_array[0]
            version = hardware_info[0]
            hardware = hardware_info[1]
        return {
            'hardware': hardware,
            'version': version,
            'patch': patch
        }


class DeviceInfoCollectorFactory:
    """
    设备信息采集策略工厂类
    根据厂商名称创建对应的采集策略实例
    """
    
    @staticmethod
    def create_collector(vendor: str) -> DeviceInfoCollectorStrategy:
        """
        创建设备信息采集策略实例
        
        Args:
            vendor: 厂商名称
            
        Returns:
            DeviceInfoCollectorStrategy: 对应的采集策略实例
        """
        vendor = vendor.lower()
        
        if vendor == 'cisco':
            return CiscoDeviceInfoCollector()
        elif vendor == 'huawei':
            return HuaweiDeviceInfoCollector()
        elif vendor == 'h3c':
            return H3CDeviceInfoCollector()
        else:
            # 对于未知厂商，返回默认采集策略
            return DefaultDeviceInfoCollector(vendor)


def _collect_vendor_specific_info(ip: str, community: str, vendor: str, sys_descr: str) -> Dict[str, str]:
    """
    采集厂商特定的设备信息（model、version、patch）

    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        vendor: 设备厂商

    Returns:
        Dict[str, str]: 包含model、version、patch字段的字典
    """
    try:
        # 创建对应的厂商采集策略
        collector = DeviceInfoCollectorFactory.create_collector(vendor)

        # 采集厂商特定信息
        vendor_specific_info = collector.collect_vendor_specific_info(ip, community)
        vendor_descr_info = collector.extract_model(sys_descr)

        hardware = vendor_descr_info.get('hardware', '') + vendor_specific_info.get('hardware', '')
        version = vendor_descr_info.get('version', '') + vendor_specific_info.get('version', '')
        patch = vendor_descr_info.get('patch', '') + vendor_specific_info.get('patch', '')


        return {
            'hardware': hardware,
            'version': version,
            'patch': patch
        }

    except Exception as e:
        logger.error(f"采集设备 {ip} 厂商特定信息时发生错误: {str(e)}", exc_info=True)
        # 发生错误时返回空值
        return {
            'hardware': "",
            'version': "",
            'patch': ""
        }


class DeviceBaseInfoCollector:
    """
    设备基础信息采集器
    使用策略模式支持不同厂商设备的信息采集
    """
    
    def __init__(self):
        """
        初始化设备基础信息采集器
        """

    def collect_data(self, ip: str, community: str = "public", vendor: str = None) -> Dict[str, Any]:
        """
        采集单个设备的基础信息
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            vendor: 设备厂商，可选，如果不提供则自动识别
            
        Returns:
            Dict[str, Any]: 设备基础信息字典
        """
        try:
            # 采集标准OID信息
            standard_data = {}
            for key, oid in STANDARD_OIDS.items():
                value = snmp_get(ip, community, oid)
                if value is not None:
                    standard_data[key] = value
            
            # 获取系统描述
            sys_descr = standard_data.get('sysDescr', '')
            
            # 如果没有提供厂商信息，则自动识别
            if not vendor:
                vendor = identify_device_vendor(sys_descr)
                logger.debug(f"自动识别设备 {ip} 厂商为: {vendor}")

            # 采集厂商特定信息，从特定的采集提取（hardware、version、patch）
            vendor_specific_info = _collect_vendor_specific_info(ip, community, vendor, sys_descr)

            hardware = vendor_specific_info.get('hardware', '')
            version = vendor_specific_info.get('version', '')
            patch = vendor_specific_info.get('patch', '')
            
            # 构建固定格式的设备信息
            device_info = {
                'ip': ip,
                'vendor': vendor,
                'hardware': hardware,
                'version': version,
                'patch': patch,
                'sysname': standard_data.get('sysName', ''),
                'sysdescr': sys_descr,
                'syslocation': standard_data.get('sysLocation', ''),
                'syscontact': standard_data.get('sysContact', ''),
                'sysobjectid': standard_data.get('sysObjectID', ''),
                'sysuptime': standard_data.get('sysUpTime', 0)
            }
            
            logger.info(f"成功采集设备 {ip} 基础信息: 厂商={vendor}, 型号={hardware}")

            return {
                "ip": ip,
                "metric_name": "device_info",
                "status": "ok",
                "message": "采集成功",
                "timestamp": int(time.time()),
                "data": device_info,
            }
            
        except Exception as e:
            logger.error(f"采集设备 {ip} 信息时发生错误: {str(e)}", exc_info=True)
            # 发生异常时返回固定格式，所有字段都有默认值
            return {
                "ip": ip,
                "metric_name": "device_info",
                "status": "error",
                "message": "采集失败"+str(e),
                "timestamp": int(time.time()),
                "data": {},
            }
    


# 创建全局实例，用于向后兼容
global_collector = DeviceBaseInfoCollector()


def collect_device_base_info(ip: str, community: str = "public") -> Dict[str, Any]:
    """
    采集单个设备的基础信息（向后兼容接口）
    
    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        version: SNMP版本（当前版本未使用）
        
    Returns:
        Dict[str, Any]: 设备基础信息
    """
    return global_collector.collect_data(ip, community)



if __name__ == '__main__':
    # aa = global_collector.collect_data(ip='10.162.0.14', community='public')
    # print(aa)
    #
    # aa = global_collector.collect_data(ip='10.80.163.98', community='public')
    # print(aa)
    #
    # aa = global_collector.collect_data(ip='10.162.0.16', community='public')
    # print(aa)
    pass