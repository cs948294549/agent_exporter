"""
SNMP采集任务

通过SNMP协议采集设备信息，同一IP的采集任务串行执行，不同IP并行执行。
"""
import logging
from typing import Dict, Any
from services.task import register_task_handler
from services.task.utils import report_result
from services.task.ip_lock import ip_lock_manager
from core.singleton_config import ConfigLoader

from collectors.device_info_collector import collect_device_base_info
from collectors.device_interface_collector import (
    collect_interface_basic_info,
    collect_interface_status,
    collect_interface_metric
)
from collectors.device_physical_collector import collect_device_physical_info

logger = logging.getLogger(__name__)
COMMON_COMMUNITY = ConfigLoader.get("snmp.community")

# 指标名称到采集函数的映射
METRIC_COLLECTORS = {
    "device_base":      lambda ip, community, **kw: collect_device_base_info(ip=ip, community=community),
    "interface_basic":  lambda ip, community, **kw: collect_interface_basic_info(ip=ip, community=community),
    "interface_status": lambda ip, community, **kw: collect_interface_status(ip=ip, community=community),
    "interface_metric": lambda ip, community, **kw: collect_interface_metric(ip=ip, community=community, metric_type=kw["metric_type"]),
    "device_physical":  lambda ip, community, **kw: collect_device_physical_info(ip=ip, community=community),
}

# 默认采集指标
DEFAULT_METRICS = ["device_base"]


def _collect_with_lock(ip: str, community: str, metrics: list) -> Dict[str, Any]:
    """
    在 per-IP 锁保护下执行采集，确保同一 IP 的多项指标串行执行。

    Returns:
        {
            "ip": "10.0.0.1",
            "status": "ok" | "partial" | "error",
            "results": {
                "device_base": {...},
                "interface_basic": {...},
                ...
            },
            "errors": {"metric_name": "error_msg", ...},
            "timestamp": 1234567890
        }
    """
    results = {}
    errors = {}

    with ip_lock_manager.acquire(ip):
        logger.info(f"[{ip}] 开始串行采集 {len(metrics)} 项指标: {metrics}")

        for metric in metrics:
            collector = METRIC_COLLECTORS.get(metric)
            if not collector:
                errors[metric] = f"未知指标: {metric}"
                continue

            try:
                result = collector(ip=ip, community=community)
                results[metric] = result
                logger.debug(f"[{ip}] {metric} 采集完成")
            except Exception as e:
                errors[metric] = str(e)
                logger.error(f"[{ip}] {metric} 采集失败: {e}")

    # 综合状态判定
    if not errors:
        status = "ok"
    elif results:
        status = "partial"
    else:
        status = "error"

    return {
        "ip": ip,
        "status": status,
        "results": results,
        "errors": errors,
    }


@register_task_handler("device_info")
def handle_device_info(task_config: dict):
    """
    SNMP设备信息采集任务

    task_config 示例:
    {
        "ip": "10.0.0.1",
        "community": "public",        # 可选，不传则用全局默认
        "metrics": ["device_base", "interface_basic"]  # 可选，默认 ["device_base"]
        "task_id": "xxx"
    }
    """
    ip = task_config.get("ip", "")
    community = task_config.get("community", COMMON_COMMUNITY)
    metrics = task_config.get("metrics", DEFAULT_METRICS)

    if not ip:
        logger.warning("SNMP采集任务缺少ip参数")
        return

    result = _collect_with_lock(ip, community, metrics)
    logger.info(f"SNMP采集完成: {ip}, status={result['status']}")
    report_result(task_config.get("task_id", ""), result)


if __name__ == '__main__':
    aa = _collect_with_lock("10.92.42.64", COMMON_COMMUNITY, "interface_basic")
    print(aa)