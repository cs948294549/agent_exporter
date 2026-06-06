"""
Per-IP 锁管理器

提供按 IP 维度的细粒度锁，确保同一 IP 的任务串行执行，不同 IP 并行执行。
自动清理长时间未使用的锁，防止内存泄漏。

用法:
    from core.ip_lock import ip_lock_manager

    # 方式一：作为上下文管理器
    with ip_lock_manager.get_lock("10.0.0.1"):
        # 同一 IP 的任务在此排队，不同 IP 不受影响
        result = collect(ip)

    # 方式二：手动获取/释放
    lock = ip_lock_manager.get_lock("10.0.0.1")
    lock.acquire()
    try:
        result = collect(ip)
    finally:
        lock.release()
"""
import threading
import time
import logging
from typing import Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class IPKeyLockManager:
    """
    Per-IP 锁管理器

    - 每个 IP 地址维护一把独立的 threading.Lock
    - 同一 IP 的请求排队执行（串行）
    - 不同 IP 的请求互不影响（并行）
    - 支持自动清理：超过 idle_timeout 秒未使用的锁会被回收
    """

    def __init__(self, cleanup_interval: int = 300, idle_timeout: int = 600):
        """
        Args:
            cleanup_interval: 清理检查间隔（秒），默认5分钟
            idle_timeout: 锁空闲超时时间（秒），超过此时间未使用则清理，默认10分钟
        """
        self._locks: Dict[str, threading.Lock] = {}
        self._last_used: Dict[str, float] = {}
        self._dict_lock = threading.Lock()  # 保护 _locks 和 _last_used 的并发访问
        self._cleanup_interval = cleanup_interval
        self._idle_timeout = idle_timeout

        # 启动后台清理线程
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="ip-lock-cleanup"
        )
        self._cleanup_thread.start()

    def get_lock(self, ip: str) -> threading.Lock:
        """获取指定 IP 的锁（不存在则创建）"""
        if ip not in self._locks:
            with self._dict_lock:
                if ip not in self._locks:
                    self._locks[ip] = threading.Lock()
                    logger.debug(f"创建 IP 锁: {ip}")

        self._last_used[ip] = time.time()
        return self._locks[ip]

    @contextmanager
    def acquire(self, ip: str):
        """
        上下文管理器方式获取锁

        with ip_lock_manager.acquire("10.0.0.1"):
            do_something()
        """
        lock = self.get_lock(ip)
        lock.acquire()
        try:
            yield
        finally:
            lock.release()

    def _cleanup_loop(self):
        """后台定期清理长时间未使用的锁"""
        while True:
            time.sleep(self._cleanup_interval)
            try:
                self._cleanup_stale_locks()
            except Exception as e:
                logger.error(f"IP锁清理异常: {e}")

    def _cleanup_stale_locks(self):
        """清理超过 idle_timeout 且未被持有的锁"""
        now = time.time()
        stale_ips = []

        with self._dict_lock:
            for ip, last_used in self._last_used.items():
                if now - last_used > self._idle_timeout:
                    lock = self._locks.get(ip)
                    # 只清理未被持有的锁（未被持有时 locked() 返回 False）
                    if lock and not lock.locked():
                        stale_ips.append(ip)

            for ip in stale_ips:
                del self._locks[ip]
                del self._last_used[ip]
                logger.debug(f"清理空闲 IP 锁: {ip}")

        if stale_ips:
            logger.info(f"清理了 {len(stale_ips)} 个空闲 IP 锁")

    @property
    def active_count(self) -> int:
        """当前活跃的锁数量"""
        with self._dict_lock:
            return len(self._locks)


# 全局单例
ip_lock_manager = IPKeyLockManager()
