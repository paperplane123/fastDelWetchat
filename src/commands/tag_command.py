import argparse
import logging
import os
from typing import List, Optional

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.macos_utils import MacOSUtils

def setup_tag_parser(subparsers):
    """设置标签命令的解析器"""
    tag_parser = subparsers.add_parser('tag', help='管理文件标签')
    tag_subparsers = tag_parser.add_subparsers(dest='tag_action', help='标签操作')
    
    # 设置标签
    set_parser = tag_subparsers.add_parser('set', help='设置标签')
    set_parser.add_argument('file', help='文件路径')
    set_parser.add_argument('color', choices=['1', '2', '3', '4', '5', '6', '7'], 
                          help='标签颜色: 1=红色, 2=橙色, 3=黄色, 4=绿色, 5=蓝色, 6=紫色, 7=灰色')
    
    # 移除标签
    remove_parser = tag_subparsers.add_parser('remove', help='移除标签')
    remove_parser.add_argument('file', help='文件路径')
    
    # 获取标签
    get_parser = tag_subparsers.add_parser('get', help='获取标签')
    get_parser.add_argument('file', help='文件路径')
    
    # 列出带标签的文件
    list_parser = tag_subparsers.add_parser('list', help='列出带标签的文件')
    list_parser.add_argument('--color', choices=['1', '2', '3', '4', '5', '6', '7'],
                           help='按颜色筛选: 1=红色, 2=橙色, 3=黄色, 4=绿色, 5=蓝色, 6=紫色, 7=灰色')
    
    # 清理失效的标签
    cleanup_parser = tag_subparsers.add_parser('cleanup', help='清理失效的标签')

def handle_tag_command(args):
    """处理标签命令"""
    if args.tag_action == 'set':
        # 设置标签
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f'错误: 文件不存在: {file_path}')
            return
        
        success = MacOSUtils.set_tag(file_path, args.color)
        if success:
            tag_info = MacOSUtils.TAGS[args.color]
            print(f'成功设置{tag_info[0]}标签 {tag_info[1]}')
        else:
            print('设置标签失败')
            
    elif args.tag_action == 'remove':
        # 移除标签
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f'错误: 文件不存在: {file_path}')
            return
        
        success = MacOSUtils.remove_tag(file_path)
        if success:
            print('成功移除标签')
        else:
            print('移除标签失败')
            
    elif args.tag_action == 'get':
        # 获取标签
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f'错误: 文件不存在: {file_path}')
            return
        
        tag_info = MacOSUtils.get_tag(file_path)
        if tag_info:
            color_info = MacOSUtils.TAGS[tag_info['tag_key']]
            print(f'文件标签: {color_info[0]} {color_info[1]}')
        else:
            print('文件没有标签')
            
    elif args.tag_action == 'list':
        # 列出带标签的文件
        files = MacOSUtils.get_files_by_tag(args.color)
        if files:
            print('带标签的文件:')
            for file in files:
                tag_info = MacOSUtils.get_tag(file)
                if tag_info:
                    color_info = MacOSUtils.TAGS[tag_info['tag_key']]
                    print(f'{color_info[1]} {file}')
        else:
            print('没有找到带标签的文件')
            
    elif args.tag_action == 'cleanup':
        # 清理失效的标签
        count = MacOSUtils.cleanup_tags()
        print(f'清理了 {count} 个失效的标签记录')
    
    else:
        print('请指定标签操作: set, remove, get, list, cleanup')
