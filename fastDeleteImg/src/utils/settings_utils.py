import os
import json
from pathlib import Path
from config.config import Config

class SettingsUtils:
    SETTINGS_DIR = os.path.join(str(Path.home()), '.fastDeleteImg')
    SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')
    
    @classmethod
    def load_settings(cls):
        """从文件加载设置"""
        try:
            if os.path.exists(cls.SETTINGS_FILE):
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # 更新配置
                    if 'cache_threshold' in settings:
                        Config.CACHE_THRESHOLD = settings['cache_threshold']
        except Exception as e:
            print(f"加载设置失败：{str(e)}")
    
    @classmethod
    def save_settings(cls):
        """保存设置到文件"""
        try:
            # 确保设置目录存在
            os.makedirs(cls.SETTINGS_DIR, exist_ok=True)
            
            # 收集当前设置
            settings = {
                'cache_threshold': Config.CACHE_THRESHOLD
            }
            
            # 保存到文件
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置失败：{str(e)}")
