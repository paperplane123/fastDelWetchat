import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Set, List, Optional

from config.config import Config
from utils.file_utils import FileUtils
from utils.image_utils import ImageUtils
from utils.cache_utils import CacheUtils
from utils.settings_utils import SettingsUtils
from utils.macos_utils import MacOSUtils
from ui.components import ToolBar, ImageList, StatusBar, PreviewPanel
from ui.dialogs import SettingsDialog

class FastImageDeleter:
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # 加载设置
        SettingsUtils.load_settings()
        
        self.setup_window()
        self.setup_variables()
        self.create_ui()
        self.bind_events()
    
    def setup_window(self):
        """设置窗口属性"""
        self.root.title(Config.APP_TITLE)
        self.root.geometry(f"{Config.APP_WIDTH}x{Config.APP_HEIGHT}")
    
    def setup_variables(self):
        """初始化变量"""
        self.marked_items: Set[str] = set()
        self.image_files: List[str] = []
        self.scan_results: List[dict] = []
        self.current_image: Optional[tk.PhotoImage] = None
        self.current_image_tk: Optional[tk.PhotoImage] = None
        
        # 创建缓存目录
        os.makedirs(Config.CACHE_DIR, exist_ok=True)
    
    def create_ui(self):
        """创建UI组件"""
        # 设置主题样式
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TLabel", padding=5)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 分割主框架
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 创建左右框架
        self.left_frame = ttk.Frame(self.paned_window)
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)
        self.paned_window.add(self.right_frame, weight=1)
        
        # 创建工具栏
        self.toolbar = ToolBar(
            self.left_frame,
            self.select_folder,
            self.open_wechat_folder,
            self.show_settings
        )
        self.toolbar.select_all_btn.configure(
            command=lambda: self.image_list.tree.selection_set(
                self.image_list.tree.get_children()
            )
        )
        self.toolbar.deselect_btn.configure(
            command=lambda: self.image_list.tree.selection_remove(
                self.image_list.tree.get_children()
            )
        )
        
        # 创建路径标签
        self.path_var = tk.StringVar()
        self.path_label = ttk.Label(
            self.main_frame,
            textvariable=self.path_var,
            wraplength=900
        )
        self.path_label.pack(pady=5)
        
        # 创建图片列表
        self.image_list = ImageList(
            self.left_frame,
            Config.COLUMNS,
            self.on_select
        )
        
        # 创建底部按钮
        self.button_frame = ttk.Frame(self.left_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        self.delete_btn = ttk.Button(
            self.button_frame,
            text="删除选中图片",
            command=self.delete_selected,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建状态栏
        self.status_bar = StatusBar(self.main_frame)
        
        # 创建预览面板
        self.preview_panel = PreviewPanel(
            self.right_frame,
            Config.SHORTCUTS_TEXT
        )
    
    def bind_events(self):
        """绑定事件"""
        # 删除快捷键
        self.root.bind('<Delete>', lambda e: self.delete_selected())
        self.root.bind('<BackSpace>', lambda e: self.delete_selected())  # 增加退格键作为删除快捷键
        
        # 导航快捷键
        self.root.bind('<Left>', self.prev_image)
        self.root.bind('<Right>', self.next_image)
        self.root.bind('<Up>', self.prev_image)    # 增加上下方向键
        self.root.bind('<Down>', self.next_image)
        
        # 标记快捷键
        self.root.bind('<space>', self.toggle_mark)    # 空格键标记/取消标记
        # 绑定颜色标签快捷键
        self.root.bind('1', lambda e: self.set_mark('1'))   # 红色
        self.root.bind('2', lambda e: self.set_mark('2'))   # 橙色
        self.root.bind('3', lambda e: self.set_mark('3'))   # 黄色
        self.root.bind('4', lambda e: self.set_mark('4'))   # 绿色
        self.root.bind('5', lambda e: self.set_mark('5'))   # 蓝色
        self.root.bind('6', lambda e: self.set_mark('6'))   # 紫色
        self.root.bind('7', lambda e: self.set_mark('7'))   # 灰色
        self.root.bind('0', lambda e: self.set_mark('0'))   # 清除标签
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = filedialog.askdirectory(title="选择要清理的文件夹")
        if folder_path:
            self.scan_folder(folder_path)
    
    def scan_folder(self, folder_path: str):
        """扫描文件夹"""
        self.path_var.set(f"选中文件夹: {folder_path}")
        self.status_bar.status_var.set("正在扫描文件...")
        self.image_list.tree.delete(*self.image_list.tree.get_children())
        self.image_files.clear()
        self.scan_results.clear()
        self.delete_btn.configure(state=tk.DISABLED)
        self.toolbar.select_btn.configure(state=tk.DISABLED)
        
        # 在新线程中扫描文件
        thread = threading.Thread(
            target=self.scan_images,
            args=(folder_path,)
        )
        thread.daemon = True
        thread.start()
        
        # 启动UI更新
        self.root.after(Config.UI_UPDATE_INTERVAL, self.update_ui)
    
    def scan_images(self, folder_path: str):
        """扫描图片文件"""
        files_to_scan = []
        for root, _, files in os.walk(folder_path):
            files_to_scan.extend((root, f) for f in files)

        total_files = len(files_to_scan)
        processed_files = 0

        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            for root, file in files_to_scan:
                if any(file.lower().endswith(ext) for ext in Config.IMAGE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    file_info = FileUtils.get_file_info(file_path)
                    
                    if file_info:
                        processed_files += 1
                        progress = (processed_files / total_files) * 100
                        
                        # 获取已有的标签
                        tag_info = MacOSUtils._get_tag_index().get_tag(file_path)
                        mark_symbol = '★' if tag_info else ''
                        
                        self.scan_results.append({
                            **file_info,
                            'mark': mark_symbol,
                            'progress': progress,
                            'processed': processed_files,
                            'total': total_files
                        })

        # 标记扫描完成
        self.scan_results.append({'finished': True})
    
    def update_ui(self):
        """更新UI显示"""
        if not self.scan_results:
            self.root.after(Config.UI_UPDATE_INTERVAL, self.update_ui)
            return
            
        # 批量处理结果
        items_to_process = min(Config.BATCH_PROCESS_SIZE, len(self.scan_results))
        for _ in range(items_to_process):
            result = self.scan_results.pop(0)
            
            if 'finished' in result:
                self.status_bar.status_var.set(
                    f"扫描完成，共找到 {len(self.image_files)} 个图片文件"
                )
                if self.image_files:
                    self.delete_btn.configure(state=tk.NORMAL)
                self.toolbar.select_btn.configure(state=tk.NORMAL)
                return
                
            self.status_bar.progress_var.set(result['progress'])
            self.status_bar.status_var.set(
                f"已处理: {result['processed']}/{result['total']}"
            )
            
            self.image_files.append(result['path'])
            item = self.image_list.tree.insert(
                "",
                tk.END,
                values=(result['mark'], result['file'], result['size_str'],
                       result['mod_time'], result['path'])
            )
            
            # 如果有标签，添加到标记集合
            if result['mark']:
                self.marked_items.add(item)
            
            # 如果是第一个项目，自动选中并预览
            if len(self.image_files) == 1:
                self.image_list.tree.selection_set(item)
                self.image_list.tree.focus(item)
                self.image_list.tree.see(item)
                self.on_select(None)
        
        self.root.after(Config.UI_UPDATE_INTERVAL, self.update_ui)
    
    def on_select(self, event):
        """处理选择事件"""
        selected_items = self.image_list.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.image_list.tree.item(item)['values']
        file_path = values[4]  # 完整路径在第五列
        
        # 加载和显示图片
        result = ImageUtils.load_and_resize_image(
            file_path,
            Config.PREVIEW_WIDTH,
            Config.PREVIEW_HEIGHT
        )
        
        if result:
            original_image, _ = result
            self.preview_panel.set_image(original_image)
        else:
            self.preview_panel.set_image(None)
            messagebox.showerror("错误", "无法加载图片")
    
    def set_mark(self, tag_key: str, event=None):
        """设置标记"""
        selected_items = self.image_list.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.image_list.tree.item(item)['values']
        file_path = values[4]  # 完整路径在第五列
        
        # 设置 macOS 标签
        if MacOSUtils.set_tag(file_path, tag_key):
            # 更新列表显示
            mark_symbol = '★' if tag_key != '0' else ''
            if mark_symbol:
                self.marked_items.add(item)
            else:
                self.marked_items.discard(item)
            
            self.image_list.tree.item(item, values=(mark_symbol,) + tuple(values[1:]))
            
            # 自动移动到下一张图片
            self.next_image()
    
    def toggle_mark(self, event=None):
        """切换标记状态"""
        selected_items = self.image_list.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.image_list.tree.item(item)['values']
        file_path = values[4]  # 完整路径在第五列
        
        # 获取当前标签
        current_tag = MacOSUtils.get_tag(file_path)
        
        if current_tag:
            self.set_mark('0')  # 清除标签
        else:
            self.set_mark('1')  # 设置红色标签
    
    def prev_image(self, event=None):
        """显示上一张图片"""
        selected_items = self.image_list.tree.selection()
        if not selected_items:
            return
            
        current_item = selected_items[0]
        prev_item = self.image_list.tree.prev(current_item)
        
        if prev_item:
            self.image_list.tree.selection_set(prev_item)
            self.image_list.tree.see(prev_item)
    
    def next_image(self, event=None):
        """显示下一张图片"""
        selected_items = self.image_list.tree.selection()
        if not selected_items:
            return
            
        current_item = selected_items[0]
        next_item = self.image_list.tree.next(current_item)
        
        if next_item:
            self.image_list.tree.selection_set(next_item)
            self.image_list.tree.see(next_item)
    
    def delete_selected(self):
        """删除选中的图片（移动到缓存）"""
        selected_items = self.image_list.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的图片")
            return
        
        # 在删除前找到下一个项目
        next_item = None
        for item in selected_items:
            next_item = self.image_list.tree.next(item)
            if next_item not in selected_items:  # 确保下一个项目不是要删除的
                break
            next_item = None
        
        # 如果没有找到下一个，尝试使用上一个
        if not next_item:
            for item in selected_items:
                prev_item = self.image_list.tree.prev(item)
                if prev_item and prev_item not in selected_items:
                    next_item = prev_item
                    break
        
        # 收集要删除的文件和其关联文件
        files_to_delete = set()
        items_to_delete = set()
        
        for item in selected_items:
            values = self.image_list.tree.item(item)['values']
            file_path = values[4]  # 完整路径在第五列
            files_to_delete.add(file_path)
            items_to_delete.add(item)
            
            # 查找关联文件
            related_files = FileUtils.find_related_files(file_path)
            for related_file in related_files:
                files_to_delete.add(related_file)
                # 查找关联文件对应的列表项
                for child in self.image_list.tree.get_children():
                    if self.image_list.tree.item(child)['values'][4] == related_file:
                        items_to_delete.add(child)
                        break
        
        # 移动文件到缓存
        if CacheUtils.move_to_cache(list(files_to_delete)):
            # 从列表中删除项目
            for item in items_to_delete:
                self.image_list.tree.delete(item)
            
            self.status_bar.status_var.set(f"已移动 {len(files_to_delete)} 个文件到缓存")
            
            # 检查缓存阈值
            CacheUtils.check_cache_threshold()
            
            # 如果有下一个项目，选中并预览
            if next_item and next_item not in items_to_delete:
                self.image_list.tree.selection_set(next_item)
                self.image_list.tree.focus(next_item)
                self.image_list.tree.see(next_item)
                self.on_select(None)
            elif next_item in items_to_delete:
                # 如果下一个项目也被删除了，尝试找到一个未被删除的项目
                for item in self.image_list.tree.get_children():
                    if item not in items_to_delete:
                        self.image_list.tree.selection_set(item)
                        self.image_list.tree.focus(item)
                        self.image_list.tree.see(item)
                        self.on_select(None)
                        break
            
            # 如果列表为空，禁用删除按钮
            if not self.image_list.tree.get_children():
                self.delete_btn.configure(state=tk.DISABLED)
    
    def show_settings(self):
        """显示设置对话框"""
        SettingsDialog(self.root)
    
    def open_wechat_folder(self):
        """打开微信图片文件夹"""
        message_folders = FileUtils.find_wechat_folders(Config.WECHAT_BASE_PATH)
        
        if not message_folders:
            messagebox.showerror(
                "错误",
                "找不到微信图片文件夹，请确认微信是否安装或手动选择文件夹。"
            )
            return
        
        # 如果找到多个文件夹，让用户选择
        if len(message_folders) > 1:
            dialog = tk.Toplevel(self.root)
            dialog.title("选择微信文件夹")
            dialog.geometry("600x400")
            
            # 创建列表框
            listbox = tk.Listbox(dialog, selectmode=tk.SINGLE)
            listbox.pack(fill=tk.BOTH, expand=True)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(
                dialog,
                orient=tk.VERTICAL,
                command=listbox.yview
            )
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.configure(yscrollcommand=scrollbar.set)
            
            # 添加文件夹到列表
            for folder in message_folders:
                listbox.insert(tk.END, folder)
            
            def on_select():
                selection = listbox.curselection()
                if selection:
                    selected_path = message_folders[selection[0]]
                    dialog.destroy()
                    self.scan_folder(selected_path)
            
            # 确认按钮
            ttk.Button(dialog, text="确认", command=on_select).pack(pady=10)
            
            return
        
        # 如果只找到一个文件夹，直接使用
        self.scan_folder(message_folders[0])
