import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Tuple
from PIL import Image, ImageTk

class ToolBar(ttk.Frame):
    def __init__(self, parent, select_cmd: Callable, wechat_cmd: Callable, settings_cmd: Callable):
        super().__init__(parent)
        self.pack(fill=tk.X, pady=(0, 10))
        
        # 选择文件夹按钮
        self.select_btn = ttk.Button(
            self,
            text="选择文件夹",
            command=select_cmd
        )
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # 微信图片文件夹按钮
        self.wechat_btn = ttk.Button(
            self,
            text="微信图片",
            command=wechat_cmd
        )
        self.wechat_btn.pack(side=tk.LEFT, padx=5)
        
        # 设置按钮
        self.settings_btn = ttk.Button(
            self,
            text="设置",
            command=settings_cmd
        )
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        
        # 快速选择按钮
        self.select_all_btn = ttk.Button(self, text="全选")
        self.select_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.deselect_btn = ttk.Button(self, text="取消选择")
        self.deselect_btn.pack(side=tk.LEFT, padx=5)

class ImageList(ttk.Frame):
    def __init__(self, parent, columns: List[Tuple[str, int]], on_select: Callable):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 初始化排序状态
        self.sort_column = None  # 当前排序的列
        self.sort_reverse = False  # 是否降序
        
        # 创建列表视图
        self.tree = ttk.Treeview(
            self,
            columns=[col[0] for col in columns],
            show="headings",
            selectmode="browse"
        )
        
        # 设置列标题和列宽
        for col, width in columns:
            # 使用lambda来保存当前列名
            self.tree.heading(
                col,
                text=col,
                command=lambda c=col: self.sort_by_column(c)
            )
            self.tree.column(col, width=width)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置列表和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', on_select)
    
    def sort_by_column(self, column):
        """按列排序"""
        # 如果点击的是当前排序列，则反转排序方向
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # 获取所有项目
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # 根据列类型进行排序
        if column == "大小":  # 大小列需要特殊处理
            # 将大小字符串转换为字节数
            def get_size_in_bytes(size_str):
                units = {'B': 1, 'KB': 1024, 'MB': 1024*1024, 'GB': 1024*1024*1024, 'TB': 1024*1024*1024*1024}
                try:
                    size, unit = size_str.strip().split()
                    return float(size) * units[unit]
                except:
                    return 0
            
            items.sort(key=lambda x: get_size_in_bytes(x[0]), reverse=self.sort_reverse)
        else:
            # 其他列正常排序
            items.sort(reverse=self.sort_reverse)
        
        # 重新排列项目
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)
        
        # 更新列标题显示排序方向
        for col in self.tree['columns']:
            self.tree.heading(col, text=col.strip('▲▼'))
        new_text = column + (' ▼' if self.sort_reverse else ' ▲')
        self.tree.heading(column, text=new_text)

class StatusBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.X, pady=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 状态标签
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            width=30
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)

class PreviewPanel(ttk.Frame):
    def __init__(self, parent, shortcuts_text: str):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        
        # 初始化变量
        self.zoom_level = 1.0
        self.original_image = None
        self.current_image = None
        
        # 快捷键说明
        shortcuts_text += "\n- 鼠标滚轮: 缩放图片"
        self.shortcuts_label = ttk.Label(
            self,
            text=shortcuts_text,
            justify=tk.LEFT
        )
        self.shortcuts_label.pack(pady=5)
        
        # 预览区域（使用Canvas代替Label以支持更好的缩放）
        self.preview_canvas = tk.Canvas(self, highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定滚轮事件
        self.preview_canvas.bind('<MouseWheel>', self.on_mousewheel)  # Windows
        self.preview_canvas.bind('<Button-4>', self.on_mousewheel)    # Linux上滚
        self.preview_canvas.bind('<Button-5>', self.on_mousewheel)    # Linux下滚
    
    def on_mousewheel(self, event):
        """处理滚轮事件"""
        if not self.original_image:
            return
            
        # 获取滚轮方向
        if event.num == 5 or event.delta < 0:  # 向下滚动，缩小
            self.zoom_level = max(0.1, self.zoom_level - 0.1)
        else:  # 向上滚动，放大
            self.zoom_level = min(5.0, self.zoom_level + 0.1)
        
        # 更新图片显示
        self.update_image()
    
    def set_image(self, image):
        """设置图片"""
        self.original_image = image
        self.zoom_level = 1.0
        self.update_image()
    
    def update_image(self):
        """根据缩放级别更新图片显示"""
        if not self.original_image:
            return
            
        # 获取原始尺寸
        original_width = self.original_image.width
        original_height = self.original_image.height
        
        # 计算新尺寸
        new_width = int(original_width * self.zoom_level)
        new_height = int(original_height * self.zoom_level)
        
        # 清除画布
        self.preview_canvas.delete('all')
        
        if new_width > 0 and new_height > 0:
            # 创建缩放后的图片
            resized_image = self.original_image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )
            
            # 转换为Tkinter图片
            self.current_image = ImageTk.PhotoImage(resized_image)
            
            # 计算居中位置
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            x = max(0, (canvas_width - new_width) // 2)
            y = max(0, (canvas_height - new_height) // 2)
            
            # 显示图片
            self.preview_canvas.create_image(
                x, y,
                anchor='nw',
                image=self.current_image
            )
