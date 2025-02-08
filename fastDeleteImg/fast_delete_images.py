import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageTk
import keyboard

class FastImageDeleter:
    def __init__(self, root):
        self.root = root
        self.root.title("快速图片清理工具")
        self.root.geometry("1280x800")
        
        # 创建预览窗口
        self.preview_window = None
        self.current_image = None
        self.current_image_tk = None
        
        # 标记状态
        self.marked_items = set()
        
        # 设置主题样式
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TLabel", padding=5)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 分割主框架为左右两部分
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧列表区域
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)
        
        # 右侧预览区域
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=1)
        
        # 顶部工具栏
        self.toolbar = ttk.Frame(self.left_frame)
        self.toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 选择文件夹按钮
        self.select_btn = ttk.Button(
            self.toolbar,
            text="选择文件夹",
            command=self.select_folder
        )
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # 微信图片文件夹按钮
        self.wechat_btn = ttk.Button(
            self.toolbar,
            text="微信图片",
            command=self.open_wechat_folder
        )
        self.wechat_btn.pack(side=tk.LEFT, padx=5)
        
        # 快速选择按钮
        ttk.Button(self.toolbar, text="全选", 
                   command=lambda: self.tree.selection_set(self.tree.get_children())).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="取消选择", 
                   command=lambda: self.tree.selection_remove(self.tree.get_children())).pack(side=tk.LEFT, padx=5)
        
        # 显示选中路径
        self.path_var = tk.StringVar()
        self.path_label = ttk.Label(
            self.main_frame,
            textvariable=self.path_var,
            wraplength=900
        )
        self.path_label.pack(pady=5)
        
        # 快捷键说明
        shortcuts_text = "快捷键：\n- Delete: 删除当前图片\n- Space: 标记/取消标记\n- ←/→: 上一张/下一张图片"
        self.shortcuts_label = ttk.Label(
            self.right_frame,
            text=shortcuts_text,
            justify=tk.LEFT
        )
        self.shortcuts_label.pack(pady=5)
        
        # 进度条和状态
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            self.progress_frame,
            textvariable=self.status_var,
            width=30
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # 图片列表框架
        self.list_frame = ttk.Frame(self.left_frame)
        self.list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建列表视图
        self.tree = ttk.Treeview(
            self.list_frame,
            columns=("标记", "文件名", "大小", "修改时间", "路径"),
            show="headings",
            selectmode="browse"
        )
        
        # 设置列标题和列宽
        columns = [("标记", 50), ("文件名", 200), ("大小", 100), ("修改时间", 150), ("路径", 400)]
        for col, width in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            self.list_frame,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置列表和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部按钮框架
        self.button_frame = ttk.Frame(self.left_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # 删除按钮
        self.delete_btn = ttk.Button(
            self.button_frame,
            text="删除选中图片",
            command=self.delete_selected,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # 预览区域
        self.preview_label = ttk.Label(self.right_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.root.bind('<Delete>', lambda e: self.delete_selected())
        self.root.bind('<space>', self.toggle_mark)
        self.root.bind('<Left>', self.prev_image)
        self.root.bind('<Right>', self.next_image)
        
        # 图片文件扩展名
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # 存储找到的图片
        self.image_files = []
        
        # 用于存储扫描结果的队列
        self.scan_results = []
        
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="选择要清理的文件夹")
        if folder_path:
            self.path_var.set(f"选中文件夹: {folder_path}")
            self.status_var.set("正在扫描文件...")
            self.tree.delete(*self.tree.get_children())
            self.image_files.clear()
            self.scan_results.clear()
            self.delete_btn.configure(state=tk.DISABLED)
            self.select_btn.configure(state=tk.DISABLED)
            
            # 在新线程中扫描文件
            thread = threading.Thread(
                target=self.scan_images,
                args=(folder_path,)
            )
            thread.daemon = True
            thread.start()
            
            # 启动UI更新
            self.root.after(100, self.update_ui)
    
    def scan_images(self, folder_path):
        def process_file(args):
            root, file = args
            if any(file.lower().endswith(ext) for ext in self.image_extensions):
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    mod_time = datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    return {
                        'file': file,
                        'size': file_size,
                        'size_str': self.format_size(file_size),
                        'mod_time': mod_time,
                        'path': file_path
                    }
                except (OSError, PermissionError):
                    return None
            return None

        # 收集所有文件
        files_to_scan = []
        for root, _, files in os.walk(folder_path):
            files_to_scan.extend((root, f) for f in files)

        total_files = len(files_to_scan)
        processed_files = 0

        # 使用线程池并行处理文件
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            for result in executor.map(process_file, files_to_scan):
                processed_files += 1
                progress = (processed_files / total_files) * 100
                
                if result:
                    self.scan_results.append({
                        **result,
                        'progress': progress,
                        'processed': processed_files,
                        'total': total_files
                    })

        # 标记扫描完成
        self.scan_results.append({'finished': True})
    
    def update_ui(self):
        if not self.scan_results:
            self.root.after(50, self.update_ui)
            return
            
        # 批量处理结果
        items_to_process = min(50, len(self.scan_results))
        for _ in range(items_to_process):
            result = self.scan_results.pop(0)
            
            if 'finished' in result:
                self.status_var.set(f"扫描完成，共找到 {len(self.image_files)} 个图片文件")
                if self.image_files:
                    self.delete_btn.configure(state=tk.NORMAL)
                self.select_btn.configure(state=tk.NORMAL)
                return
                
            self.progress_var.set(result['progress'])
            self.status_var.set(f"已处理: {result['processed']}/{result['total']}")
            
            self.image_files.append(result['path'])
            self.tree.insert(
                "",
                tk.END,
                values=("", result['file'], result['size_str'], 
                       result['mod_time'], result['path'])
            )
        
        self.root.after(50, self.update_ui)
        

    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的图片")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的图片吗？此操作不可撤销！"):
            deleted_count = 0
            for item in selected_items:
                values = self.tree.item(item)['values']
                file_path = values[4]  # 完整路径在第五列
                try:
                    os.remove(file_path)
                    self.tree.delete(item)
                    deleted_count += 1
                except Exception as e:
                    messagebox.showerror("错误", f"删除文件 {file_path} 时出错：{str(e)}")
            
            self.status_var.set(f"成功删除 {deleted_count} 个文件")
            
            # 如果列表为空，禁用删除按钮
            if not self.tree.get_children():
                self.delete_btn.configure(state=tk.DISABLED)

    def on_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.tree.item(item)['values']
        file_path = values[4]  # 完整路径在第五列
        
        try:
            # 加载和调整图片大小
            image = Image.open(file_path)
            # 计算缩放比例，保持纵横比
            preview_width = 600
            preview_height = 600
            img_width, img_height = image.size
            ratio = min(preview_width/img_width, preview_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # 调整图片大小
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.current_image_tk = ImageTk.PhotoImage(image)
            
            # 显示图片
            self.preview_label.configure(image=self.current_image_tk)
            
        except Exception as e:
            self.preview_label.configure(image='')
            messagebox.showerror("错误", f"无法加载图片：{str(e)}")
    
    def toggle_mark(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.tree.item(item)['values']
        
        # 切换标记状态
        if item in self.marked_items:
            self.marked_items.remove(item)
            mark = ""
        else:
            self.marked_items.add(item)
            mark = "★"  # 使用星号作为标记
        
        # 更新树视图
        self.tree.item(item, values=(mark,) + values[1:])
    
    def prev_image(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        current_item = selected_items[0]
        prev_item = self.tree.prev(current_item)
        
        if prev_item:
            self.tree.selection_set(prev_item)
            self.tree.see(prev_item)
    
    def next_image(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        current_item = selected_items[0]
        next_item = self.tree.next(current_item)
        
        if next_item:
            self.tree.selection_set(next_item)
            self.tree.see(next_item)

    def find_wechat_folders(self):
        """查找微信的Message文件夹"""
        base_path = os.path.expanduser("~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat")
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
    
    def open_wechat_folder(self):
        # 查找所有微信图片文件夹
        message_folders = self.find_wechat_folders()
        
        if not message_folders:
            messagebox.showerror("错误", "找不到微信图片文件夹，请确认微信是否安装或手动选择文件夹。")
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
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=listbox.yview)
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
    
    def scan_folder(self, folder_path):
        """扫描指定文件夹"""
        self.path_var.set(f"选中文件夹: {folder_path}")
        self.status_var.set("正在扫描文件...")
        self.tree.delete(*self.tree.get_children())
        self.image_files.clear()
        self.scan_results.clear()
        self.delete_btn.configure(state=tk.DISABLED)
        self.select_btn.configure(state=tk.DISABLED)
        
        # 在新线程中扫描文件
        thread = threading.Thread(
            target=self.scan_images,
            args=(folder_path,)
        )
        thread.daemon = True
        thread.start()
        
        # 启动UI更新
        self.root.after(100, self.update_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = FastImageDeleter(root)
    root.mainloop()
