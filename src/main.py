import tkinter as tk
import sys
import logging
import os
import argparse
from pathlib import Path

# 添加当前目录的父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ui.app import FastImageDeleter
from commands import setup_tag_parser, handle_tag_command

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
    
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description='Fast Delete Image - 快速删除和管理图片')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加标签命令
    setup_tag_parser(subparsers)
    
    # 添加GUI命令
    gui_parser = subparsers.add_parser('gui', help='启动图形界面')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    try:
        # 处理命令
        if args.command == 'tag':
            handle_tag_command(args)
        elif args.command == 'gui' or not args.command:
            # 创建主窗口
            root = tk.Tk()
            app = FastImageDeleter(root)
            root.mainloop()
        else:
            parser.print_help()
    except Exception as e:
        logging.error(f"应用程序出错：{str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
