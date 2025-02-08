import tkinter as tk
import sys
import logging
import os
from pathlib import Path

# 添加当前目录的父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ui.app import FastImageDeleter

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    try:
        # 创建主窗口
        root = tk.Tk()
        app = FastImageDeleter(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"应用程序出错：{str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
