import os
from pathlib import Path

class Config:
    # 应用设置
    APP_TITLE = "快速图片清理工具"
    APP_WIDTH = 1280
    APP_HEIGHT = 800
    
    # UI设置
    PREVIEW_WIDTH = 600
    PREVIEW_HEIGHT = 600
    
    # 图片设置
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    # 微信文件夹设置
    WECHAT_BASE_PATH = os.path.expanduser(
        "~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat"
    )
    
    # 列设置
    COLUMNS = [
        ("标记", 50),
        ("文件名", 200),
        ("大小", 100),
        ("修改时间", 150),
        ("路径", 400)
    ]
    
    # 快捷键说明
    SHORTCUTS_TEXT = """快捷键：
- Delete/Backspace: 删除当前图片
- Space: 标记/取消标记
- ←/→/↑/↓: 切换图片
- 1: 红色标签
- 2: 橙色标签
- 3: 黄色标签
- 4: 绿色标签
- 5: 蓝色标签
- 6: 紫色标签
- 7: 灰色标签
- 0: 清除标签"""

    # 缓存设置
    CACHE_DIR = os.path.join(str(Path.home()), '.fastDeleteImg', 'cache')
    CACHE_THRESHOLD = 2  # 缓存文件数达到此阈值时提示清理
    
    # 线程设置
    MAX_WORKERS = os.cpu_count()
    UI_UPDATE_INTERVAL = 50  # 毫秒
    BATCH_PROCESS_SIZE = 50  # 每批处理的文件数
