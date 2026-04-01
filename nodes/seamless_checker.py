import torch
import numpy as np
from PIL import Image
import os
import folder_paths


class SeamlessCheckerNode:
    
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_seamless_" + ''.join(np.random.choice(list("abcdefghijklmnopqrstuvwxyz"), 5))
        self.compress_level = 4
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "tile_count": (["2x2", "3x3", "4x4", "5x5"], {"default": "3x3"}),
            },
        }
    
    RETURN_TYPES = ()
    FUNCTION = "check_seamless"
    OUTPUT_NODE = True
    CATEGORY = "MC_PBR_Master"
    
    def check_seamless(self, image, tile_count):
        tile_size = int(tile_count[0])
        
        img_tensor = image[0]
        i = 255. * img_tensor.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        
        img_width, img_height = img.size
        
        tiled_width = img_width * tile_size
        tiled_height = img_height * tile_size
        
        tiled_img = Image.new('RGB', (tiled_width, tiled_height))
        
        for row in range(tile_size):
            for col in range(tile_size):
                x_offset = col * img_width
                y_offset = row * img_height
                tiled_img.paste(img, (x_offset, y_offset))
        
        filename = f"{self.prefix_append}_{tile_count}.png"
        file_path = os.path.join(self.output_dir, filename)
        tiled_img.save(file_path, compress_level=self.compress_level)
        
        return {
            "ui": {
                "images": [{
                    "filename": filename,
                    "subfolder": "",
                    "type": self.type
                }]
            }
        }


NODE_CLASS_MAPPINGS = {
    "SeamlessChecker": SeamlessCheckerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SeamlessChecker": "MC: Tile Checker"
}