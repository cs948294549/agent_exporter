"""
任务主服务模块

定时从控制中心拉取任务列表，与本地scheduler进行同步：
- 新增任务：添加到scheduler执行
- 删除任务：从scheduler移除
- 更新任务：更新scheduler中的任务配置
"""
import time
import logging
import threading
import requests
from typing import Dict, Any, List
from core.scheduler import scheduler
from core.singleton_config import ConfigLoader

# 导入task子包，触发所有任务处理器的注册
from services.task import TASK_HANDLERS
from services.task.utils import build_job_id, parse_schedule

logger = logging.getLogger(__name__)


# ==================== 核心同步逻辑 ====================

def fetch_tasks() -> List[Dict[str, Any]]:
    """
    从控制中心拉取任务列表

    期望的响应格式:
    {
        "code": 200,
        "data": {
            "tasks": [
                {
                    "task_id": "xxx",
                    "task_type": "snmp_collect",
                    "config": {"ip": "...", "community": "..."},
                    "schedule": {"type": "interval", "seconds": 300},
                    "enabled": true
                }
            ]
        }
    }
    """
    center_url = ConfigLoader.get("center.url", "")
    agent_id = ConfigLoader.get("center.agent_id", "")

    if not center_url:
        logger.warning("控制中心地址未配置(center.url)，跳过任务拉取")
        return []

    try:
        resp = requests.get(
            f"{center_url}/agent/tasks",
            params={"agent_id": agent_id},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") == 200:
            tasks = data.get("data", {}).get("tasks", [])
            logger.info(f"拉取到 {len(tasks)} 个任务")
            return tasks
        else:
            logger.warning(f"拉取任务列表失败: code={data.get('code')}, msg={data.get('msg')}")
            return []
    except requests.RequestException as e:
        logger.error(f"请求控制中心失败: {e}")
        return []


def sync_tasks(remote_tasks: List[Dict[str, Any]]):
    """
    将远程任务列表同步到本地scheduler

    比对逻辑：
    1. 遍历远程任务，与scheduler中现有job对比
    2. 不存在的job -> 新增
    3. 已存在但配置不同的job -> 更新
    4. 远程已删除的job -> 从scheduler移除
    """
    # 获取scheduler中已有的task job
    existing_jobs = {}
    for job in scheduler.get_jobs():
        if job.id.startswith("task_"):
            existing_jobs[job.id] = job

    remote_job_ids = set()

    for task in remote_tasks:
        task_id = task.get("task_id", "")
        task_type = task.get("task_type", "")
        config = task.get("config", {})
        schedule = task.get("schedule", {"type": "interval", "seconds": 60})
        enabled = task.get("enabled", True)

        if not task_id or not task_type:
            continue

        job_id = build_job_id(task_id)
        remote_job_ids.add(job_id)

        handler = TASK_HANDLERS.get(task_type)
        if not handler:
            logger.warning(f"未知任务类型: {task_type} (task_id={task_id})，跳过")
            continue

        if not enabled:
            # 任务已禁用，确保从scheduler中移除
            if job_id in existing_jobs:
                scheduler.remove_job(job_id)
                logger.info(f"任务已禁用，从scheduler移除: task_id={task_id}")
            continue

        trigger_kwargs, trigger_type = parse_schedule(schedule)

        # 构建任务参数：将config作为参数传给handler
        job_kwargs = {"task_config": {**config, "task_id": task_id, "task_type": task_type}}

        if job_id in existing_jobs:
            # 任务已存在，更新配置
            existing_job = existing_jobs[job_id]
            try:
                existing_job.reschedule(trigger=trigger_type, **trigger_kwargs)
                logger.debug(f"任务已更新: task_id={task_id}")
            except Exception as e:
                logger.error(f"更新任务失败: task_id={task_id}, error={e}")
        else:
            # 新增任务
            try:
                scheduler.add_job(
                    func=handler,
                    trigger=trigger_type,
                    id=job_id,
                    name=f"{task_type}_{task_id}",
                    replace_existing=False,
                    **trigger_kwargs,
                    **job_kwargs
                )
                logger.info(f"新增任务: task_id={task_id}, type={task_type}, trigger={trigger_type}({trigger_kwargs})")
            except Exception as e:
                logger.error(f"新增任务失败: task_id={task_id}, error={e}")

    # 移除远程已不存在的任务
    for job_id, job in existing_jobs.items():
        if job_id not in remote_job_ids:
            try:
                scheduler.remove_job(job_id)
                logger.info(f"移除过期任务: {job_id}")
            except Exception as e:
                logger.error(f"移除任务失败: {job_id}, error={e}")


# ==================== 定时拉取循环 ====================

_pull_interval = 60  # 默认每60秒拉取一次
_running = False


def _pull_loop():
    """定时拉取任务列表的主循环"""
    global _running
    _running = True
    logger.info(f"任务拉取服务启动，拉取间隔: {_pull_interval}秒")

    while _running:
        try:
            remote_tasks = fetch_tasks()
            if remote_tasks is not None:
                sync_tasks(remote_tasks)
        except Exception as e:
            logger.error(f"任务拉取/同步异常: {e}", exc_info=True)

        time.sleep(_pull_interval)


def start_task_pull_service(interval: int = 60):
    """
    启动任务拉取服务（后台线程）

    Args:
        interval: 拉取间隔（秒），默认60秒
    """
    global _pull_interval, _running

    if _running:
        logger.warning("任务拉取服务已在运行中")
        return

    _pull_interval = interval
    t = threading.Thread(target=_pull_loop, daemon=True, name="task-pull-service")
    t.start()
    logger.info("任务拉取服务已启动")


def stop_task_pull_service():
    """停止任务拉取服务"""
    global _running
    _running = False
    logger.info("任务拉取服务已停止")
