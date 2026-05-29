import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(name: str, log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """
    设置日志系统
    
    Args:
        name: 日志器名称
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_dir: 日志文件目录
        
    Returns:
        配置好的日志器
    """
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 格式化日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 创建文件处理器 (带滚动)
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{name}_{current_date}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # 保留5个备份
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认日志器
logger = setup_logging("app")

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return setup_logging(name)
