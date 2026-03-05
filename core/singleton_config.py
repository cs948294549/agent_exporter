import os
import yaml
from typing import Any, Dict, Optional

default_config = {
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
    },
    "snmp": {
        "community": "public",
    },
    "ssh": {
        "username": "netops",
        "password": "Chensong6^",
    },
    "logs": {
        "level": "DEBUG",
    }
}

def deep_update(original: dict, update: dict) -> dict:
    """
    递归增量更新字典：只更新指定键，未指定的键保留原值
    :param original: 原始字典（如原有配置）
    :param update: 待更新的字典（增量配置）
    :return: 更新后的新字典
    """
    # 遍历更新字典的每个键值对
    for key, value in update.items():
        # 如果原始字典包含该键，且两者都是字典 → 递归更新嵌套字典
        if key in original and isinstance(original[key], dict) and isinstance(value, dict):
            deep_update(original[key], value)
        # 否则直接覆盖（非字典类型/原始字典无该键）
        else:
            original[key] = value
    return original

class SingletonConfig:
    """全局单例配置加载器"""
    # 私有类属性：存储唯一实例
    _instance: Optional["SingletonConfig"] = None
    # 配置数据存储
    _config: Dict[str, Any] = default_config

    EXTERNAL_CONFIG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # 上级目录（app/）
        "configs", "config.yaml"
    )

    def __new__(cls):
        """单例核心：创建实例前检查是否已存在，不存在则新建"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化时加载配置（仅加载一次）
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """加载配置：优先外部配置，无则用默认（仅执行一次）"""
        # 确定最终配置文件路径
        if os.path.exists(self.EXTERNAL_CONFIG_PATH):
            # 读取并解析 YAML 配置
            try:
                with open(self.EXTERNAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                    external_config = yaml.safe_load(f)
                    if external_config:
                        self._config = deep_update(self._config, external_config)
                print(f"✅ 配置加载成功，路径：{self.EXTERNAL_CONFIG_PATH}")
            except FileNotFoundError:
                raise RuntimeError(f"❌ 配置文件不存在, 仅加载默认配置!")
            except yaml.YAMLError as e:
                raise RuntimeError(f"❌ 配置文件解析失败：{e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        便捷获取配置（支持点语法，如 "server.port"）
        :param key: 配置键，支持分层（如 "database.host"）
        :param default: 不存在时的默认值
        :return: 配置值
        """
        keys = key.split(".")
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def config(self) -> Dict[str, Any]:
        """直接获取完整配置字典（供复杂取值场景）"""
        return self._config

    def reload(self):
        """手动重新加载配置（可选，用于热更新）"""
        self._load_config()
        print("🔄 配置已手动重新加载")


# 全局导出：创建单例实例，项目中直接导入这个实例即可
ConfigLoader = SingletonConfig()