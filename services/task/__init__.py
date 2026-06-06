"""
任务处理器注册中心

提供统一的任务类型注册机制，各子模块通过装饰器注册任务处理函数。
"""
import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)

# 任务类型 -> 处理函数的映射
TASK_HANDLERS: Dict[str, Callable] = {}


def register_task_handler(task_type: str):
    """
    任务处理器装饰器，注册任务类型到对应的处理函数

    Usage:
        from services.task import register_task_handler

        @register_task_handler("snmp_collect")
        def handle_snmp_collect(task_config: dict):
            ...
    """
    def decorator(func: Callable):
        TASK_HANDLERS[task_type] = func
        logger.debug(f"注册任务处理器: {task_type} -> {func.__name__}")
        return func
    return decorator


# 自动导入所有任务子模块，触发装饰器注册
from services.task import snmp_collect