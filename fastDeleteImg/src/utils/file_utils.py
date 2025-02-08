import os
from datetime import datetime
from typing import Dict, Optional, List, Tuple

class FileUtils:
    @staticmethod
    def format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict]:
        """获取文件信息"""
        try:
            file_size = os.path.getsize(file_path)
            mod_time = datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'file': os.path.basename(file_path),
                'size': file_size,
                'size_str': FileUtils.format_size(file_size),
                'mod_time': mod_time,
                'path': file_path
            }
        except (OSError, PermissionError):
            return None

    @staticmethod
    def find_related_files(file_path: str) -> List[str]:
        """查找与给定文件相关的文件
        如果是原图，查找缩略图
        如果是缩略图，查找原图
        """
        related_files = []
        dirname = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        # 如果是缩略图
        if filename.endswith('.pic_thumb.jpg'):
            # 查找原图
            original = filename.replace('.pic_thumb.jpg', '.pic.jpg')
            original_path = os.path.join(dirname, original)
            if os.path.exists(original_path):
                related_files.append(original_path)
        
        # 如果是原图
        elif filename.endswith('.pic.jpg'):
            # 查找缩略图
            thumb = filename.replace('.pic.jpg', '.pic_thumb.jpg')
            thumb_path = os.path.join(dirname, thumb)
            if os.path.exists(thumb_path):
                related_files.append(thumb_path)
        
        return related_files
    
    @staticmethod
    def find_wechat_folders(base_path: str) -> list:
        """查找微信的Message文件夹"""
        message_folders = []
        
        if not os.path.exists(base_path):
            return []
            
        # 遍历版本目录
        for version in os.listdir(base_path):
            version_path = os.path.join(base_path, version)
            if not os.path.isdir(version_path):
                continue
                
            # 遍历用户目录
            for user_dir in os.listdir(version_path):
                user_path = os.path.join(version_path, user_dir)
                if not os.path.isdir(user_path):
                    continue
                    
                # 检查Message文件夹
                message_path = os.path.join(user_path, "Message")
                if os.path.exists(message_path):
                    message_folders.append(message_path)
        
        return message_folders
