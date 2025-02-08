from PIL import Image, ImageTk
from typing import Tuple, Optional

class ImageUtils:
    @staticmethod
    def load_and_resize_image(file_path: str, max_width: int, max_height: int) -> Optional[Tuple[ImageTk.PhotoImage, Image.Image]]:
        """加载并调整图片大小"""
        try:
            # 加载图片
            image = Image.open(file_path)
            
            # 计算缩放比例，保持纵横比
            img_width, img_height = image.size
            ratio = min(max_width/img_width, max_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # 调整图片大小
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 返回原始图片
            return image, resized_image
        except Exception:
            return None
