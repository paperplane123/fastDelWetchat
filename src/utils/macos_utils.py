import logging
import os
import traceback
from typing import List, Optional, Dict
from .tag_index import TagIndex

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MacOSUtils:
    # macOS 标签颜色映射
    TAGS = {
        '1': ('Red', '\033[31m●\033[0m', 'Red'),         # 红色
        '2': ('Orange', '\033[33m●\033[0m', 'Orange'),     # 橙色
        '3': ('Yellow', '\033[33m●\033[0m', 'Yellow'),     # 黄色
        '4': ('Green', '\033[32m●\033[0m', 'Green'),       # 绿色
        '5': ('Blue', '\034[34m●\033[0m', 'Blue'),         # 蓝色
        '6': ('Purple', '\035[35m●\033[0m', 'Purple'),     # 紫色
        '7': ('Gray', '\037[37m●\033[0m', 'Gray')          # 灰色
    }
    
    @staticmethod
    def _get_tag_index():
        return TagIndex()

    @staticmethod
    def _check_directory_permissions(file_path: str) -> tuple[bool, str]:
        """检查目录权限
        参数:
            file_path: 文件路径
        返回:
            tuple: (是否有正确权限, 错误信息)
        """
        try:
            # 获取目录路径
            dir_path = os.path.dirname(file_path)
            
            # 检查目录是否存在
            if not os.path.exists(dir_path):
                return False, f'Directory does not exist: {dir_path}'
            
            # 获取目录权限信息
            dir_stat = os.stat(dir_path)
            logging.debug(f'Directory permissions: {oct(dir_stat.st_mode)}')
            logging.debug(f'Directory owner: {dir_stat.st_uid}, group: {dir_stat.st_gid}')
            
            # 检查当前用户是否有读写执行权限
            if not os.access(dir_path, os.R_OK | os.W_OK | os.X_OK):
                return False, f'Insufficient directory permissions: {dir_path}'
            
            # 检查目录的所有上级目录权限
            current_path = dir_path
            while current_path != '/':
                if not os.access(current_path, os.X_OK):
                    return False, f'No execute permission on parent directory: {current_path}'
                current_path = os.path.dirname(current_path)
            
            return True, ''
            
        except Exception as e:
            return False, f'Error checking directory permissions: {str(e)}'









    @staticmethod
    def set_tag(file_path: str, tag_key: str) -> bool:
        """设置文件的标签颜色
        参数:
            file_path: 文件路径
            tag_key: 标签键值（1-7）
        返回:
            bool: 是否设置成功
        """
        try:
            # 获取标签信息
            tag_info = MacOSUtils.TAGS.get(tag_key)
            if not tag_info:
                logging.error(f'Invalid tag key: {tag_key}')
                return False
            
            tag_color, tag_symbol, tag_name = tag_info
            
            # 不再设置系统标签
            
            # 设置自定义标签索引
            if MacOSUtils._get_tag_index().set_tag(file_path, tag_key, tag_name, tag_color):
                logging.debug(f'Added {tag_color} tag {tag_symbol}')
                return True
            return False
            
        except Exception as e:
            logging.error(f'Unexpected error while setting tag: {str(e)}')
            logging.debug(f'Exception traceback: {traceback.format_exc()}')
            return False
        logging.debug(f'Setting tag {tag_key} for file {file_path}')
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logging.error(f'File does not exist: {file_path}')
                return False
            
            # 获取标签颜色
            tag_info = MacOSUtils.TAGS.get(tag_key)
            if not tag_info:
                logging.error(f'Invalid tag key: {tag_key}')
                return False
            
            tag_color, tag_symbol, tag_name = tag_info
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 生成临时文件路径
                temp_file = os.path.join(temp_dir, os.path.basename(file_path))
                logging.debug(f'Using temporary file: {temp_file}')
                
                try:
                    # 复制文件到临时目录
                    shutil.copy2(file_path, temp_file)
                    logging.debug('File copied to temporary location')
                    
                    # 在临时文件上设置标签
                    script = f'''
                    tell application "Finder"
                        try
                            set theFile to POSIX file "{temp_file}" as alias
                            set label index of theFile to {tag_key}
                            set tags of theFile to {{"{tag_name}"}}
                            return true
                        on error errMsg
                            return errMsg
                        end try
                    end tell
                    '''
                    
                    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                    logging.debug(f'AppleScript result: {result.stdout}')
                    
                    if result.returncode != 0:
                        logging.error(f'Failed to set tag via AppleScript: {result.stderr}')
                        return False
                    
                    # 验证标签是否设置成功
                    verify_script = f'''
                    tell application "Finder"
                        try
                            set theFile to POSIX file "{temp_file}" as alias
                            return label index of theFile
                        on error errMsg
                            return errMsg
                        end try
                    end tell
                    '''
                    
                    verify_result = subprocess.run(['osascript', '-e', verify_script], capture_output=True, text=True)
                    logging.debug(f'Verify result: {verify_result.stdout}')
                    
                    if verify_result.returncode != 0:
                        logging.error('Failed to verify tag')
                        return False
                    
                    # 尝试覆盖原文件
                    try:
                        shutil.copy2(temp_file, file_path)
                        logging.debug('Tagged file copied back to original location')
                    except PermissionError:
                        # 如果没有写权限，尝试使用sudo
                        cmd = ['sudo', 'cp', temp_file, file_path]
                        cp_result = subprocess.run(cmd, capture_output=True, text=True)
                        if cp_result.returncode != 0:
                            logging.error(f'Failed to copy file back: {cp_result.stderr}')
                            return False
                        logging.debug('Tagged file copied back using sudo')
                    
                    # 使用xattr设置标签
                    if MacOSUtils._set_finder_tags(file_path, tag_name):
                        logging.debug('Successfully set Finder tags using xattr')
                    else:
                        logging.warning('Failed to set Finder tags using xattr')
                    
                    # 刷新Finder以显示更新
                    MacOSUtils._refresh_finder(file_path)
                    
                    # 再次使用AppleScript设置标签，确保生效
                    final_script = f'''
                    tell application "Finder"
                        try
                            set theFile to POSIX file "{file_path}" as alias
                            set label index of theFile to {tag_key}
                            set tags of theFile to {{"{tag_name}"}}
                            return true
                        on error errMsg
                            return errMsg
                        end try
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', final_script], capture_output=True, text=True)
                    
                    logging.debug(f'Added {tag_color} tag {tag_symbol}')
                    logging.debug('Tag set successfully')
                    return True
                    
                except Exception as e:
                    logging.error(f'Error during temporary file operations: {str(e)}')
                    return False
            
        except Exception as e:
            logging.error(f'Unexpected error while setting tag: {str(e)}')
            logging.debug(f'Exception traceback: {traceback.format_exc()}')
            return False

    @staticmethod
    def get_tag(file_path: str) -> Optional[Dict[str, str]]:
        """获取文件的标签信息
        参数:
            file_path: 文件路径
        返回:
            Optional[Dict[str, str]]: 标签信息，包含tag_key, tag_name, tag_color
        """
        try:
            # 从自定义标签索引获取标签
            return MacOSUtils._get_tag_index().get_tag(file_path)
        except Exception as e:
            logging.error(f'Error getting tag: {str(e)}')
            return None

    @staticmethod
    def get_files_by_tag(tag_key: Optional[str] = None, tag_name: Optional[str] = None) -> List[str]:
        """获取具有特定标签的所有文件
        
        Args:
            tag_key: 标签键值（1-7）
            tag_name: 标签名称
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            return MacOSUtils._get_tag_index().get_files_by_tag(tag_key, tag_name)
        except Exception as e:
            logging.error(f'Error getting files by tag: {str(e)}')
            return []

    @staticmethod
    def remove_tag(file_path: str) -> bool:
        """移除文件的标签
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否移除成功
        """
        try:
            # 不再移除系统标签
            
            # 移除自定义标签索引
            return MacOSUtils._get_tag_index().remove_tag(file_path)
        except Exception as e:
            logging.error(f'Error removing tag: {str(e)}')
            return False

    @staticmethod
    def cleanup_tags() -> int:
        """清理数据库中不存在的文件记录
        
        Returns:
            int: 清理的记录数量
        """
        try:
            return MacOSUtils._get_tag_index().cleanup_missing_files()
        except Exception as e:
            logging.error(f'Error cleaning up tags: {str(e)}')
            return 0
