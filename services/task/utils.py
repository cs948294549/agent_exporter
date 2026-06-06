"""
任务工具函数

提供任务执行过程中通用的工具方法，如结果上报、job ID构建、调度解析等。
"""
import time
import logging
import requests
from core.singleton_config import ConfigLoader

logger = logging.getLogger(__name__)


def report_result(task_id: str, result):
    """将任务执行结果上报给控制中心"""
    center_url = ConfigLoader.get("center.url", "")
    if not center_url:
        return
    try:
        requests.post(
            f"{center_url}/agent/task_report",
            json={"task_id": task_id, "result": result, "timestamp": int(time.time())},
            timeout=10
        )
    except Exception as e:
        logger.error(f"结果上报失败: task_id={task_id}, error={e}")


def build_job_id(task_id: str) -> str:
    """构建scheduler job的唯一ID"""
    return f"task_{task_id}"


def parse_schedule(schedule: dict) -> tuple:
    """
    解析调度配置，返回(trigger_kwargs, trigger_type)

    支持的调度类型:
    - interval: {"type": "interval", "seconds": 60} / "minutes": 5 / "hours": 1
    - cron: {"type": "cron", "hour": 8, "minute": 30}
    - date: {"type": "date", "run_date": "2025-01-01 08:00:00"}
    """
    schedule_type = schedule.get("type", "interval")

    if schedule_type == "interval":
        trigger_kwargs = {}
        for key in ("seconds", "minutes", "hours", "days"):
            if key in schedule:
                trigger_kwargs[key] = schedule[key]
        if not trigger_kwargs:
            trigger_kwargs = {"seconds": 60}  # 默认每分钟
        return trigger_kwargs, "interval"

    elif schedule_type == "cron":
        trigger_kwargs = {}
        for key in ("year", "month", "day", "week", "day_of_week", "hour", "minute", "second"):
            if key in schedule:
                trigger_kwargs[key] = schedule[key]
        return trigger_kwargs, "cron"

    elif schedule_type == "date":
        trigger_kwargs = {"run_date": schedule.get("run_date", "")}
        return trigger_kwargs, "date"

    else:
        logger.warning(f"未知的调度类型: {schedule_type}，使用默认interval(60s)")
        return {"seconds": 60}, "interval"
