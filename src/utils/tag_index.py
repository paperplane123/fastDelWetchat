import sqlite3
import os
import logging
from typing import List, Optional, Dict
from pathlib import Path

class TagIndex:
    _instance = None
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super(TagIndex, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        self._initialized = True
        """初始化标签索引系统
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 在用户主目录下创建数据库文件
            db_path = os.path.expanduser('~/.fastDeleteImg/tags.db')
            
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 创建文件标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_tags (
                    file_path TEXT PRIMARY KEY,
                    tag_key TEXT,
                    tag_name TEXT,
                    tag_color TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def set_tag(self, file_path: str, tag_key: str, tag_name: str, tag_color: str) -> bool:
        """设置文件的标签
        
        Args:
            file_path: 文件路径
            tag_key: 标签键值（1-7）
            tag_name: 标签名称
            tag_color: 标签颜色
            
        Returns:
            bool: 是否设置成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO file_tags 
                    (file_path, tag_key, tag_name, tag_color)
                    VALUES (?, ?, ?, ?)
                ''', (file_path, tag_key, tag_name, tag_color))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f'Error setting tag in database: {str(e)}')
            return False

    def get_tag(self, file_path: str) -> Optional[Dict[str, str]]:
        """获取文件的标签信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Dict[str, str]]: 标签信息，包含tag_key, tag_name, tag_color
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT tag_key, tag_name, tag_color
                    FROM file_tags
                    WHERE file_path = ?
                ''', (file_path,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'tag_key': result[0],
                        'tag_name': result[1],
                        'tag_color': result[2]
                    }
                return None
        except Exception as e:
            logging.error(f'Error getting tag from database: {str(e)}')
            return None

    def remove_tag(self, file_path: str) -> bool:
        """移除文件的标签
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否移除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM file_tags WHERE file_path = ?', (file_path,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f'Error removing tag from database: {str(e)}')
            return False

    def get_files_by_tag(self, tag_key: Optional[str] = None, tag_name: Optional[str] = None) -> List[str]:
        """获取具有特定标签的所有文件
        
        Args:
            tag_key: 标签键值（1-7）
            tag_name: 标签名称
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if tag_key:
                    cursor.execute('SELECT file_path FROM file_tags WHERE tag_key = ?', (tag_key,))
                elif tag_name:
                    cursor.execute('SELECT file_path FROM file_tags WHERE tag_name = ?', (tag_name,))
                else:
                    cursor.execute('SELECT file_path FROM file_tags')
                    
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f'Error getting files by tag from database: {str(e)}')
            return []

    def cleanup_missing_files(self) -> int:
        """清理数据库中不存在的文件记录
        
        Returns:
            int: 清理的记录数量
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT file_path FROM file_tags')
                all_files = cursor.fetchall()
                
                removed_count = 0
                for (file_path,) in all_files:
                    if not os.path.exists(file_path):
                        cursor.execute('DELETE FROM file_tags WHERE file_path = ?', (file_path,))
                        removed_count += 1
                
                conn.commit()
                return removed_count
        except Exception as e:
            logging.error(f'Error cleaning up database: {str(e)}')
            return 0
