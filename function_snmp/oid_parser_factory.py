"""
OID解析器工厂模块

提供OID解析器的工厂类实现，支持统一的解析器注册和管理
"""
import logging
import threading
import inspect
from typing import Dict, List, Any, Optional, Set, Type, Tuple
from function_snmp.oids import OIDParser, get_all_parsers, get_parser_by_name

logger = logging.getLogger(__name__)


class OIDParserFactory:
    """
    OID解析器工厂类（单例模式）
    
    负责注册和管理各种OID解析器类，提供通过OID查找对应解析器类的功能
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OIDParserFactory, cls).__new__(cls)
                cls._instance._init_factory()
            return cls._instance
    
    def _init_factory(self):
        """
        初始化工厂，创建解析器类注册表和实例缓存
        """
        # 解析器类注册表: {oid_prefix: (parser_class, args, kwargs)}
        self._parser_classes: Dict[str, tuple] = {}
        # 解析器实例缓存: {oid_prefix: parser_instance}
        self._parser_instances: Dict[str, OIDParser] = {}
        # 线程锁，保护注册和获取操作的线程安全
        self._lock = threading.RLock()
    
    def register_parser(self, parser_class: Type[OIDParser], *args, **kwargs) -> str:
        """
        注册一个新的OID解析器类
        
        Args:
            parser_class: OID解析器类
            *args: 传递给解析器构造函数的位置参数
            **kwargs: 传递给解析器构造函数的关键字参数
            
        Returns:
            str: 注册的OID前缀
            
        Raises:
            ValueError: 如果解析器类不是OIDParser的子类
        """
        if not issubclass(parser_class, OIDParser):
            raise ValueError(f"{parser_class.__name__} 不是OIDParser的子类")
        
        # 创建临时实例来获取OID前缀
        temp_parser = parser_class(*args, **kwargs)
        oid_prefix = temp_parser.oid_prefix
        
        with self._lock:
            # 注册解析器类和构造参数
            self._parser_classes[oid_prefix] = (parser_class, args, kwargs)
            # 清除可能存在的旧实例缓存
            if oid_prefix in self._parser_instances:
                del self._parser_instances[oid_prefix]
            logger.info(f"已注册OID解析器类: OID={oid_prefix}, 类={parser_class.__name__}")
        
        return oid_prefix
    
    def get_parser_class(self, oid: str) -> Optional[tuple]:
        """
        通过OID获取对应的解析器类和构造参数（仅支持精确匹配）
        
        Args:
            oid: 完整的OID或OID前缀
            
        Returns:
            Optional[tuple]: (parser_class, args, kwargs) 或 None
        """
        with self._lock:
            # 仅支持精确匹配
            if oid in self._parser_classes:
                return self._parser_classes[oid]
            
            logger.warning(f"未找到OID {oid} 对应的解析器类")
            return None
    
    def get_parser(self, oid: str) -> Optional[OIDParser]:
        """
        通过OID获取或创建对应的解析器实例（仅支持精确匹配）
        
        Args:
            oid: 完整的OID或OID前缀
            
        Returns:
            Optional[OIDParser]: 对应的解析器实例，如果未注册则返回None
        """
        with self._lock:
            # 先尝试精确匹配实例缓存
            if oid in self._parser_instances:
                return self._parser_instances[oid]
            
            parser_info = self.get_parser_class(oid)
            if parser_info:
                parser_class, args, kwargs = parser_info
                # 创建新实例并缓存
                parser = parser_class(*args, **kwargs)
                # 使用解析器的实际OID前缀作为缓存键
                self._parser_instances[parser.oid_prefix] = parser
                return parser
            
            return None
    
    def get_all_parser_classes(self) -> Dict[str, tuple]:
        """
        获取所有已注册的解析器类
        
        Returns:
            Dict[str, tuple]: 所有解析器类的字典
        """
        with self._lock:
            return self._parser_classes.copy()
    
    def get_all_parsers(self) -> Dict[str, OIDParser]:
        """
        获取所有已创建的解析器实例
        
        Returns:
            Dict[str, OIDParser]: 所有解析器实例的字典
        """
        with self._lock:
            # 确保所有注册的解析器都有实例
            for oid_prefix, (parser_class, args, kwargs) in self._parser_classes.items():
                if oid_prefix not in self._parser_instances:
                    self._parser_instances[oid_prefix] = parser_class(*args, **kwargs)
            return self._parser_instances.copy()
    
    def unregister_parser(self, oid_prefix: str) -> bool:
        """
        注销指定OID前缀的解析器
        
        Args:
            oid_prefix: OID前缀
            
        Returns:
            bool: 是否成功注销
        """
        with self._lock:
            # 移除类注册
            if oid_prefix in self._parser_classes:
                del self._parser_classes[oid_prefix]
                # 同时移除实例缓存
                if oid_prefix in self._parser_instances:
                    del self._parser_instances[oid_prefix]
                logger.info(f"已注销OID解析器: OID={oid_prefix}")
                return True
            return False
    
    def parse_oid(self, ip: str, community: str, oid: str, use_cache: bool = True) -> Optional[Any]:
        """
        使用注册的解析器解析指定OID的数据
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            oid: 完整的OID
            use_cache: 是否使用缓存
            
        Returns:
            Optional[Any]: 解析后的数据
        """
        parser = self.get_parser(oid)
        if parser:
            return parser.collect_and_parse(ip, community, use_cache)
        return None
    
    def create_parser_instance(self, parser_class: Type[OIDParser], *args, **kwargs) -> OIDParser:
        """
        直接创建指定解析器类的实例
        
        Args:
            parser_class: OID解析器类
            *args: 传递给解析器构造函数的位置参数
            **kwargs: 传递给解析器构造函数的关键字参数
            
        Returns:
            OIDParser: 解析器实例
            
        Raises:
            ValueError: 如果解析器类不是OIDParser的子类
        """
        if not issubclass(parser_class, OIDParser):
            raise ValueError(f"{parser_class.__name__} 不是OIDParser的子类")
        
        return parser_class(*args, **kwargs)


# 创建全局OID解析器工厂实例
global_oid_parser_factory = OIDParserFactory()


def register_parser_from_name(parser_name: str, factory: OIDParserFactory = None) -> bool:
    """
    通过名称从oids模块注册解析器
    
    Args:
        parser_name: 解析器类名称
        factory: 解析器工厂实例，如果为None则使用全局实例
        
    Returns:
        bool: 是否成功注册
    """
    if factory is None:
        factory = global_oid_parser_factory
    
    try:
        # 从oids模块获取解析器类
        parser_class = get_parser_by_name(parser_name)
        if not parser_class:
            logger.warning(f"无法获取解析器类: {parser_name}")
            return False
        
        # 检查是否为OIDParser的子类
        if not issubclass(parser_class, OIDParser):
            logger.warning(f"解析器类 {parser_name} 不是OIDParser的子类")
            return False
        
        # 注册解析器
        factory.register_parser(parser_class)
        logger.info(f"成功注册解析器: {parser_name}")
        return True
    except Exception as e:
        logger.error(f"注册解析器 {parser_name} 时出错: {str(e)}")
        return False


def register_parsers_batch(parser_names: List[str], factory: OIDParserFactory = None) -> Tuple[int, int]:
    """
    批量注册解析器
    
    Args:
        parser_names: 解析器类名称列表
        factory: 解析器工厂实例，如果为None则使用全局实例
        
    Returns:
        Tuple[int, int]: (成功注册数量, 失败注册数量)
    """
    if factory is None:
        factory = global_oid_parser_factory
    
    success_count = 0
    failed_count = 0
    
    for parser_name in parser_names:
        if register_parser_from_name(parser_name, factory):
            success_count += 1
        else:
            failed_count += 1
    
    return success_count, failed_count


def register_default_parsers(factory: OIDParserFactory = None) -> Dict[str, int]:
    """
    注册默认的OID解析器（从oids模块获取所有可用解析器）
    
    Args:
        factory: 解析器工厂实例，如果为None则使用全局实例
        
    Returns:
        Dict[str, int]: 注册结果统计
    """
    if factory is None:
        factory = global_oid_parser_factory
    
    try:
        # 从oids模块获取所有可用的解析器名称
        all_parser_names = get_all_parsers()
        logger.info(f"从oids模块获取到 {len(all_parser_names)} 个可用解析器")
        
        # 批量注册解析器
        success, failed = register_parsers_batch(all_parser_names, factory)
        
        # 生成注册报告
        registered_count = len(factory.get_all_parser_classes())
        report = {
            'total_available': len(all_parser_names),
            'successfully_registered': success,
            'failed_to_register': failed,
            'total_registered': registered_count
        }
        
        logger.info(f"默认解析器注册完成: 可用={report['total_available']}, 成功={report['successfully_registered']}, "
                   f"失败={report['failed_to_register']}, 总计={report['total_registered']}")
        
        return report
    except Exception as e:
        logger.error(f"注册默认OID解析器时发生错误: {str(e)}", exc_info=True)
        return {
            'error': str(e),
            'successfully_registered': 0,
            'failed_to_register': 0,
            'total_registered': 0
        }


# 在模块加载时自动注册默认解析器
try:
    registration_result = register_default_parsers()
    logger.info(f"模块初始化时自动注册解析器完成")
except Exception as e:
    logger.error(f"注册默认OID解析器时发生错误: {str(e)}", exc_info=True)
