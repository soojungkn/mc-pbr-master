import torch
import numpy as np
from PIL import Image
import os
import folder_paths
import math
import random

class ImagePreviewPassNode:
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + ''.join(np.random.choice(list("abcdefghijklmnopqrstuvwxyz"), 5))
        self.compress_level = 4
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
        }

    @classmethod
    def IS_CHANGED(cls, images):
        try:
            return images.cpu().numpy().sum()
        except:
            return float("NaN")

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "preview_and_pass"
    OUTPUT_NODE = True
    CATEGORY = "MC_PBR_Master"
    
    def preview_and_pass(self, images):
        batch_size = min(len(images), 9)
        results = []
        cache_buster = random.randint(0, 999999)

        if batch_size == 1:
            image = images[0]
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            filename = f"{self.prefix_append}_{cache_buster}_00000.png"
            file_path = os.path.join(self.output_dir, filename)
            img.save(file_path, compress_level=self.compress_level)
            
            results.append({
                "filename": filename,
                "subfolder": "",
                "type": self.type
            })
        else:
            # 여러 장일 경우 그리드 생성 로직
            grid_size = int(math.ceil(math.sqrt(batch_size)))
            first_image = images[0]
            img_height, img_width = first_image.shape[0], first_image.shape[1]
            grid_img = Image.new('RGB', (img_width * grid_size, img_height * grid_size), (0, 0, 0))
            
            for idx in range(batch_size):
                image = images[idx]
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                
                row = idx // grid_size
                col = idx % grid_size
                x_offset = col * img_width
                y_offset = row * img_height
                
                grid_img.paste(img, (x_offset, y_offset))
            
            filename = f"{self.prefix_append}_{cache_buster}_grid.png"
            file_path = os.path.join(self.output_dir, filename)
            grid_img.save(file_path, compress_level=self.compress_level)
            
            results.append({
                "filename": filename,
                "subfolder": "",
                "type": self.type
            })
        
        # ComfyUI UI 엔진에 이미지 리스트 전달 및 결과 이미지 패스
        return {
            "ui": {"images": results},
            "result": (images,)
        }

NODE_CLASS_MAPPINGS = {
    "MC_ImagePreviewPass": ImagePreviewPassNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MC_ImagePreviewPass": "MC: Image Preview Pass"
}