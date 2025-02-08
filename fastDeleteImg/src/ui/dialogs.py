import tkinter as tk
from tkinter import ttk, messagebox
from config.config import Config
from utils.settings_utils import SettingsUtils

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("设置")
        self.geometry("300x200")
        
        # 设置为模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 创建设置界面
        self.create_widgets()
        
        # 居中显示
        self.center_window()
        
    def create_widgets(self):
        """创建设置界面组件"""
        # 缓存设置框架
        cache_frame = ttk.LabelFrame(self, text="缓存设置", padding="10")
        cache_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 缓存阈值设置
        ttk.Label(cache_frame, text="缓存阈值:").pack(side=tk.LEFT, padx=5)
        self.threshold_var = tk.StringVar(value=str(Config.CACHE_THRESHOLD))
        threshold_spinbox = ttk.Spinbox(
            cache_frame,
            from_=1,
            to=100,
            width=5,
            textvariable=self.threshold_var
        )
        threshold_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(cache_frame, text="个文件").pack(side=tk.LEFT, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        # 确定按钮
        ttk.Button(
            button_frame,
            text="确定",
            command=self.apply_settings
        ).pack(side=tk.LEFT, padx=5)
        
        # 取消按钮
        ttk.Button(
            button_frame,
            text="取消",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def apply_settings(self):
        """应用并保存设置"""
        try:
            new_threshold = int(self.threshold_var.get())
            if new_threshold < 1:
                raise ValueError("缓存阈值必须大于0")
            
            # 更新设置
            Config.CACHE_THRESHOLD = new_threshold
            
            # 保存设置
            SettingsUtils.save_settings()
            
            self.destroy()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
