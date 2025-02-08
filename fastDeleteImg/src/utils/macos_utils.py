import subprocess
import logging
import os
from typing import List, Optional

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MacOSUtils:
    @staticmethod
    def _check_tag_command():
        """检查tag命令是否可用"""
        try:
            result = subprocess.run(['which', 'tag'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def _refresh_finder(file_path: str):
        """刷新Finder以显示更新的标签"""
        try:
            # 使用AppleScript触发Finder刷新
            script = f'''
            tell application "Finder"
                if exists POSIX file "{file_path}" then
                    update POSIX file "{file_path}"
                end if
            end tell
            '''
            subprocess.run(['osascript', '-e', script], capture_output=True)
            return True
        except Exception as e:
            logging.error(f'Failed to refresh Finder: {str(e)}')
            return False
    
    # macOS 标签颜色映射
    TAGS = {
        '1': ('Red', '\\033[31m\xe2\x97\x8f\\033[0m'),     # 红色
        '2': ('Orange', '\\033[33m\xe2\x97\x8f\\033[0m'),  # 橙色
        '3': ('Yellow', '\\033[33m\xe2\x97\x8f\\033[0m'),  # 黄色
        '4': ('Green', '\\033[32m\xe2\x97\x8f\\033[0m'),   # 绿色
        '5': ('Blue', '\\033[34m\xe2\x97\x8f\\033[0m'),    # 蓝色
        '6': ('Purple', '\\033[35m\xe2\x97\x8f\\033[0m'),  # 紫色
        '7': ('Gray', '\\033[37m\xe2\x97\x8f\\033[0m')     # 灰色
    }
    
    @staticmethod
    def _run_command(cmd: List[str]) -> tuple[bool, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr if result.returncode != 0 else result.stdout
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def set_tag(file_path: str, tag_key: str) -> bool:
        """设置文件的标签颜色
        参数:
            file_path: 文件路径
            tag_key: 标签键值（1-7）
        返回:
            bool: 是否设置成功
        """
        logging.debug(f'Setting tag {tag_key} for file {file_path}')
        
        try:
            # 检查tag命令是否可用
            if not MacOSUtils._check_tag_command():
                logging.error('tag command not found. Please install it using: brew install tag')
                return False
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logging.error(f'File does not exist: {file_path}')
                return False
            
            # 检查文件权限
            if not os.access(file_path, os.W_OK):
                logging.error(f'No write permission for file: {file_path}')
                return False
            
            # 获取标签颜色
            tag_info = MacOSUtils.TAGS.get(tag_key)
            if not tag_info:
                logging.error(f'Invalid tag key: {tag_key}')
                return False
            
            tag_color, tag_symbol = tag_info
            
            # 使用AppleScript设置标签
            script = f'''
            tell application "Finder"
                if exists POSIX file "{file_path}" then
                    set theFile to POSIX file "{file_path}" as alias
                    set label index of theFile to {tag_key}
                end if
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f'Failed to set tag via AppleScript: {result.stderr}')
                return False
            
            # 刷新Finder以显示更新
            MacOSUtils._refresh_finder(file_path)
            
            logging.debug(f'Added {tag_color} tag {tag_symbol}')
            logging.debug('Tag set successfully')
            return True
            
        except Exception as e:
            logging.error(f'Unexpected error while setting tag: {str(e)}')
            return False
    
    @staticmethod
    def get_tag(file_path: str) -> Optional[str]:
        """获取文件的标签颜色
        参数:
            file_path: 文件路径
        返回:
            str: 标签键值（1-7），如果没有标签则返回None
        """
        try:
            # 使用 tag 命令获取标签
            cmd = ['tag', '-l', file_path]
            success, output = MacOSUtils._run_command(cmd)
            
            if not success or not output.strip():
                return None
            
            # 解析输出找到颜色
            output = output.strip().lower()
            for key, (color, _) in MacOSUtils.TAGS.items():
                if color.lower() in output:
                    return key
            
            return None
            
        except Exception as e:
            logging.error(f'Failed to get tag: {str(e)}')
            return None
