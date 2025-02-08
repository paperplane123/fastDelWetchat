import os
import shutil
from tkinter import messagebox
from config.config import Config

class CacheUtils:
    @staticmethod
    def move_to_cache(file_paths: list) -> bool:
        """将文件移动到缓存文件夹
        参数:
            file_paths: 要移动的文件路径列表
        返回:
            bool: 是否全部移动成功
        """
        try:
            for file_path in file_paths:
                # 生成目标路径
                filename = os.path.basename(file_path)
                cache_path = os.path.join(Config.CACHE_DIR, filename)
                
                # 如果目标文件已存在，添加数字后缀
                counter = 1
                while os.path.exists(cache_path):
                    name, ext = os.path.splitext(filename)
                    cache_path = os.path.join(Config.CACHE_DIR, f"{name}_{counter}{ext}")
                    counter += 1
                
                # 移动文件到缓存
                shutil.move(file_path, cache_path)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"移动文件到缓存失败：{str(e)}")
            return False
    
    @staticmethod
    def check_cache_threshold() -> bool:
        """检查缓存文件数量并提示清理"""
        try:
            cache_files = [f for f in os.listdir(Config.CACHE_DIR) 
                        if os.path.isfile(os.path.join(Config.CACHE_DIR, f))]
            
            if len(cache_files) >= Config.CACHE_THRESHOLD:
                if messagebox.askyesno("清理缓存", 
                                    f"缓存文件夹中已有{len(cache_files)}个文件，是否清空缓存？"):
                    for f in cache_files:
                        try:
                            os.remove(os.path.join(Config.CACHE_DIR, f))
                        except Exception as e:
                            messagebox.showerror("错误", f"删除缓存文件失败：{str(e)}")
                            return False
                    return True
            return False
        except Exception as e:
            messagebox.showerror("错误", f"检查缓存失败：{str(e)}")
            return False
